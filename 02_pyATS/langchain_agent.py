from langchain.agents import AgentType, initialize_agent
from langchain_community.llms import Ollama
from langchain_community.tools import DuckDuckGoSearchRun

# Initialize the tool
duckduckgo_search = DuckDuckGoSearchRun()

# Initialize the LLM
llm = Ollama(model="llama2")

# Initialize the agent
qa_agent = initialize_agent(
    [duckduckgo_search],
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

def answer_question(data):
    """
    Answers a question about a given text using a LangChain agent.
    """
    question = data['question']
    context = data['context']
    prompt = f"Context: {context}\n\nQuestion: {question}"
    result = qa_agent.run(prompt)
    return result
