import yaml
from crewai import Task
from textwrap import dedent

class BusinessReportTasks:
    def __init__(self):
        with open('config/tasks.yaml', 'r') as file:
            self.tasks_config = yaml.safe_load(file)

    def download_report_task(self, agent):
        config = self.tasks_config['download_report_task']
        return Task(
            description=config['description'],
            expected_output=config['expected_output'],
            agent=agent
        )

    def analysis_task(self, agent, context):
        config = self.tasks_config['analysis_task']
        return Task(
            description=dedent(config['description']),
            expected_output=config['expected_output'],
            agent=agent,
            context=context
        )

    def email_task(self, agent, context):
        config = self.tasks_config['email_task']
        return Task(
            description=dedent(config['description']),
            expected_output=config['expected_output'],
            agent=agent,
            context=context
        )

    def cleanup_task(self, agent, context):
        config = self.tasks_config['cleanup_task']
        return Task(
            description=dedent(config['description']),
            expected_output=config['expected_output'],
            agent=agent,
            context=context
        )