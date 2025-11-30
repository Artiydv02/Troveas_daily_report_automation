from crewai import Crew
from agents import BusinessReportAgents
from tasks import BusinessReportTasks

class ReportingCrew:
    def run(self):
        agents = BusinessReportAgents()
        tasks = BusinessReportTasks()
        
        # Full 4-agent workflow with Uniware API
        downloader = agents.downloader_agent()
        analyst = agents.analyst_agent()
        communicator = agents.communications_agent()
        cleanup = agents.cleanup_agent()
        
        # Create sequential tasks
        download_task = tasks.download_report_task(downloader)
        analysis_task = tasks.analysis_task(analyst, context=[download_task])
        emailing_task = tasks.email_task(communicator, context=[analysis_task])
        cleanup_task = tasks.cleanup_task(cleanup, context=[emailing_task])

        crew = Crew(
            agents=[downloader, analyst, communicator, cleanup],
            tasks=[download_task, analysis_task, emailing_task, cleanup_task],
            verbose=True
        )
        result = crew.kickoff()
        return result
