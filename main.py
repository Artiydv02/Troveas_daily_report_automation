from dotenv import load_dotenv
from crew import ReportingCrew

def run():
    """Main function to run the crew, called by 'crewai run'."""
    load_dotenv()
    
    print("\n--- Starting the Fully Automated Reporting Crew ---\n")
    crew_result = ReportingCrew().run()
    
    print("\n\n--- Crew Execution Finished ---")
    print("Final Result:")
    print(crew_result)
