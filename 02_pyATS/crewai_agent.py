
from crewai import Agent, Task, Crew
from langchain_community.llms import Ollama
from langchain_community.tools import DuckDuckGoSearchRun

# Initialize the tool
duckduckgo_search = DuckDuckGoSearchRun()

# Define the agent
summarizer_agent = Agent(
    role='Summarizer',
    goal='Summarize the given text.',
    backstory='You are an expert in summarizing text.',
    verbose=True,
    allow_delegation=False,
    tools=[duckduckgo_search],
    llm=Ollama(model="llama2")
)

def summarize_text(text):
    """
    Summarizes the given text using a CrewAI agent.
    """
    task = Task(
        description=f'Summarize the following text: {text}',
        agent=summarizer_agent
    )

    crew = Crew(
        agents=[summarizer_agent],
        tasks=[task],
        verbose=2
    )

    result = crew.kickoff()
    return result
