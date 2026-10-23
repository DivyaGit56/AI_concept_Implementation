from langchain_core.messages import HumanMessage  
from langchain_openai import ChatOpenAI               # OpenAI API wrapper for chat models,it provides a simple interface to interact with OpenAI's chat models, allowing you to send messages and receive responses in a conversational format.
from langchain.tools import tool                       # A utility for defining tools that can be used by agents, enabling them to perform specific actions or access certain functionalities during their interactions.
from langgraph.agents import create_react_agent         # A function to create a ReAct agent, which is a type of agent that can reason and act based on the information it receives, allowing for more dynamic and interactive conversations.
from dotenv import load_dotenv                        # A utility for loading environment variables from a .env file, making it easy to manage configuration settings.

load_dotenv()  # Load environment variables from .env file

def main():
    model = ChatOpenAi(temperature = 0) # Initialize the chat model with a specified temperature, which controls the randomness of the responses. A temperature of 0 means the model will produce more deterministic responses.
    