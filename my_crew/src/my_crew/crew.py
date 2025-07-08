from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
import yaml

@CrewBase
class MyCrew():

    with open('C:\\Users\\hp\\Coding Projects\\havk-project-name-undecided\\my_crew\\src\\my_crew\\config\\agents.yaml') as f:
        agents_config = yaml.safe_load(f)
    with open('C:\\Users\\hp\\Coding Projects\\havk-project-name-undecided\\my_crew\\src\\my_crew\\config\\tasks.yaml') as f:
        tasks_config = yaml.safe_load(f)

    @agent
    def supervisor_agent(self) -> Agent:
        return Agent(
            **self.agents_config['supervisor_agent'],
            verbose=True
        )

    @agent
    def conversational_intake_agent(self) -> Agent:
        return Agent(
            **self.agents_config['conversational_intake_agent'],
            verbose=True
        )

    @agent
    def database_handler_agent(self) -> Agent:
        return Agent(
            **self.agents_config['database_handler_agent'],
            verbose=True
        )

    @task
    def handle_new_aid_request(self) -> Task:
        return Task(
            **self.tasks_config['handle_new_aid_request']
        )

    @task
    def extract_request_information(self) -> Task:
        return Task(
            **self.tasks_config['extract_request_information']
        )

    @task
    def store_aid_request(self) -> Task:
        return Task(
            **self.tasks_config['store_aid_request']
        )

    @task
    def send_confirmation_message(self) -> Task:
        return Task(
            **self.tasks_config['send_confirmation_message']
        )

    @task
    def simulate_aid_request(self) -> Task:
        return Task(
            **self.tasks_config['simulate_aid_request']
        )

    @property
    def agents(self):
        return [
            self.supervisor_agent(),
            self.conversational_intake_agent(),
            self.database_handler_agent(),
        ]

    @property
    def tasks(self):
        return [
            self.handle_new_aid_request(),
            self.extract_request_information(),
            self.store_aid_request(),
            self.send_confirmation_message(),
            self.simulate_aid_request(),
        ]

    @crew
    def crew(self) -> Crew:
        """Creates the MyCrew crew"""

        return Crew(
            agents=self.agents, # type: ignore[arg-type]
            tasks=self.tasks, # type: ignore[arg-type]
            process=Process.sequential,
            verbose=True,
        )