from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List

@CrewBase
class MyCrew():

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def supervisor_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['supervisor_agent'], # type: ignore[index]
            verbose=True
        )

    @agent
    def conversational_intake_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['conversational_intake_agent'],  # type: ignore[index]
            verbose=True
        )

    @agent
    def database_handler_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['database_handler_agent'], # type: ignore[index]
            verbose=True
        )

    @task
    def handle_new_aid_request(self) -> Task:
        return Task(config=self.tasks_config['handle_new_aid_request']) # type: ignore[index]

    @task
    def extract_request_information(self) -> Task:
        return Task(config=self.tasks_config['extract_request_information']) # type: ignore[index]

    @task
    def store_aid_request(self) -> Task:
        return Task(config=self.tasks_config['store_aid_request']) # type: ignore[index]

    @task
    def send_confirmation_message(self) -> Task:
        return Task(config=self.tasks_config['send_confirmation_message']) # type: ignore[index]

    @task
    def simulate_aid_request(self) -> Task:
        return Task(config=self.tasks_config['simulate_aid_request']) # type: ignore[index]


    @crew
    def crew(self) -> Crew:
        """Creates the MyCrew crew"""

        return Crew(
            agents=self.agents, # type: ignore[arg-type]
            tasks=self.tasks, # type: ignore[arg-type]
            process=Process.sequential,
            verbose=True,
        )