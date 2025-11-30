import os
import yaml
from crewai import Agent
from langchain_openai import ChatOpenAI
from tools.custom_tool import UniwareAPITools, DataAnalysisTools, EmailTools, CleanupTools

class BusinessReportAgents:
    def __init__(self):
        with open('config/agents.yaml', 'r') as file:
            self.agents_config = yaml.safe_load(file)
        # UPDATED: Naye .env variable 'MODEL' ko use karein
        self.llm = ChatOpenAI(model_name=os.getenv("MODEL", "gpt-4o"))

    def downloader_agent(self):
        config = self.agents_config['downloader_agent']
        return Agent(
            role=config['role'], goal=config['goal'], backstory=config['backstory'],
            tools=[UniwareAPITools()], llm=self.llm, verbose=True
        )

    def analyst_agent(self):
        config = self.agents_config['analyst_agent']
        return Agent(
            role=config['role'], goal=config['goal'], backstory=config['backstory'],
            tools=[DataAnalysisTools()], llm=self.llm, verbose=True
        )

    def communications_agent(self):
        config = self.agents_config['communications_agent']
        return Agent(
            role=config['role'], goal=config['goal'], backstory=config['backstory'],
            tools=[EmailTools()], llm=self.llm, verbose=True
        )

    def cleanup_agent(self):
        config = self.agents_config['cleanup_agent']
        return Agent(
            role=config['role'], goal=config['goal'], backstory=config['backstory'],
            tools=[CleanupTools()], llm=self.llm, verbose=True
        )
