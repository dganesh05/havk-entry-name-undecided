import asyncio
import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import Update
from crew import MyCrew
import openai
import json
import re

load_dotenv()
crew = MyCrew()
sessions = {}

FIELD_PROMPTS = {
    "category": (
        "To help you best, could you tell me what kind of assistance you need? "
        "For example, is it food, hygiene, or something else?"
    ),
    "urgency": (
        "How urgent is your request? Would you say it's low, medium, or high priority?"
    ),
    "help_mode": (
        "Would you prefer to receive help in person, virtually, or are you not sure yet?"
    ),
    "location_hint": (
        "Could you share a location or area where you’d like to receive help? "
        "It can be as general or specific as you’re comfortable with."
    ),
    "description": (
        "Could you briefly describe your situation or what you need help with?"
    ),
    "is_anonymous": (
        "Would you like your request to be anonymous? Just let me know yes or no."
    )
}

SYSTEM_PROMPT = """You are a helpful, empathetic assistant helping someone request aid. Given the conversation so far and the information already collected, generate a friendly, natural follow-up question to gather the next missing detail. Avoid technical terms and use plain language."""

REQUIRED_FIELDS = ["category", "urgency", "help_mode", "location_hint", "description", "is_anonymous"]

def is_json_complete(json_obj):
    return all(json_obj.get(field) not in [None, "", "unknown"] for field in REQUIRED_FIELDS)

def get_missing_fields(json_obj):
    return [field for field in REQUIRED_FIELDS if json_obj.get(field) in [None, "", "unknown"]]

def get_next_missing_field(json_obj):
    missing = get_missing_fields(json_obj)
    return missing[0] if missing else None

def get_conversation_history(user_id):
    # Example: sessions[user_id]["history"] = [("User", "I need food"), ("Bot", "How urgent?"), ...]
    history = sessions[user_id].get("history", [])
    return "\n".join([f"{role}: {msg}" for role, msg in history])

def build_llm_prompt(conversation, current_json, missing_fields):
    return (
        f"Conversation so far:\n{conversation}\n\n"
        f"Current information collected:\n{current_json}\n\n"
        f"Fields still missing: {', '.join(missing_fields)}\n\n"
        "Please generate a friendly, empathetic question to ask for the next missing field."
    )

def store_json(final_json, notes):
    # Replace this with your actual storage logic
    # For now, just return a confirmation string
    return (
        "Your request has been submitted!\n\n"
        f"Details: {final_json}\n"
        f"Additional notes: {' '.join(notes) if notes else 'None'}"
    )

def merge_json_fields(old: dict, new: dict) -> dict:
    """Merges newly extracted JSON fields into the existing JSON state, ignoring unknown or empty values."""
    merged = old.copy()
    for key, value in new.items():
        if value and value != "unknown":
            merged[key] = value
    return merged

client = openai.OpenAI()  # This uses your OPENAI_API_KEY from env

def extract_json(user_message, current_json):
    prompt = (
        "You are an assistant helping to fill out an aid request form. "
        "Given the user's latest message and the current form data, extract any new information and return ONLY a JSON object with the updated fields. "
        "Do not include any explanation or extra text.\n\n"
        f"Current form data: {current_json}\n"
        f"User message: {user_message}\n\n"
        "Return only the JSON with any new or updated fields."
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You extract structured data from user messages for an aid request form."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    content = response.choices[0].message.content
    import json, re
    try:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            return {}
    except Exception as e:
        print("Error parsing JSON from LLM response:", e)
        return {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    sessions[user_id] = {
        "json": {},
        "in_progress": True,
        "turns": 0
    }
    await update.message.reply_text("👋 Hi! Let’s start your aid request. Just tell me what you need help with.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_message = update.message.text.strip()

    # Ensure session exists
    if user_id not in sessions:
        await update.message.reply_text("Please start the conversation with /start.")
        return

    # 1. Handle "done"
    if user_message == "/done":
        # Submit JSON + notes
        final_json = sessions[user_id]["json"]
        notes = sessions[user_id].get("notes", [])
        response = store_json(final_json, notes)
        await update.message.reply_text(response)
        sessions.pop(user_id)
        return

    # 2. Extract info and update JSON
    partial_json = extract_json(user_message, sessions[user_id]["json"])
    sessions[user_id]["json"] = merge_json_fields(sessions[user_id]["json"], partial_json)
    sessions[user_id]["turns"] += 1

    # 3. Check if complete
    if not is_json_complete(sessions[user_id]["json"]):
        # 4. Ask next question
        conversation = get_conversation_history(user_id)
        current_json = sessions[user_id]["json"]
        missing_fields = get_missing_fields(current_json)
        llm_prompt = build_llm_prompt(conversation, current_json, missing_fields)
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or "gpt-4"
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": llm_prompt}
            ]
        )
        next_question = response.choices[0].message.content
        await update.message.reply_text(next_question)
    else:
        # JSON is complete, collect extra info
        if "ready_for_notes" not in sessions[user_id]:
            sessions[user_id]["ready_for_notes"] = True
            sessions[user_id]["notes"] = []
            await update.message.reply_text(
                "Great, I have all the required information. "
                "If there’s anything else you’d like to add—details, context, or special requests—just type it here. "
                "When you’re ready to submit, type /done."
            )
        else:
            # Collect extra info
            sessions[user_id]["notes"].append(user_message)
            await update.message.reply_text(
                "Noted! You can keep adding more, or type /done to submit."
            )


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN missing in .env")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🚀 Bot is running... talk to it on Telegram.")
    app.run_polling()  # <-- synchronous, no await

if __name__ == "__main__":
    main()
