import threading
from coral_server.agent.router_agent import RouterAgent
from crewai_agent import summarize_text
from langchain_agent import answer_question

# Global variable to store the router agent
router_agent = None

def start_coral_server():
    """
    Starts the Coral server in a separate thread.
    """
    global router_agent
    router_agent = RouterAgent()
    router_agent.start()

def register_agents():
    """
    Registers the CrewAI and LangChain agents with the router agent.
    """
    router_agent.register_agent("summarizer", summarize_text)
    router_agent.register_agent("qa", answer_question)

def delegate_task(task, text):
    """
    Delegates a task to the appropriate agent using the router agent.
    """
    if router_agent is None:
        raise Exception("Coral server not started.")

    if task == "summarize":
        return router_agent.call_agent("summarizer", text)
    elif task == "qa":
        return router_agent.call_agent("qa", {"question": text, "context": ""})
    else:
        return "Unknown task"

# Start the Coral server and register the agents in a separate thread
server_thread = threading.Thread(target=start_coral_server)
server_thread.daemon = True
server_thread.start()

# Register the agents after the server has started
# This is not ideal, but it's a simple way to ensure the server is running
# before registering the agents.
import time
time.sleep(5) # Wait for the server to start
register_agents()