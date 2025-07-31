from typing import TypedDict, Annotated

from langchain_groq import ChatGroq
from langchain_tavily import  TavilySearch
import requests
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START,END
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
import os

# OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
OPENWEATHER_API_KEY ='80019514908fc06dd23e0d5efeba030b'


class State(TypedDict):
    messages: Annotated[list, add_messages]

@tool
def fetch_user_weather_data_for_use_in_advice(location: str) -> str:
    """
    Fetches the current and short-term forecast weather data for a specified farm location to help provide farming advice.

    Parameters:
    ----------
    location : str
        The name of the town or village where the user's farm is located (e.g., 'Nairobi', 'Kisumu').

    Returns:
    -------
    str
        A short and SMS-compatible summary of the current weather and forecast in that location, including temperature and condition.
        For example: "Nairobi: Now 27°C, clear sky. Forecast: Light rain expected in 3 hours."

    Example Use:
    -----------
    Use this tool when the user asks:
    - "What's the weather like in Eldoret?"
    - "Will it rain in Kitale today?"
    - "Can I plant beans today in Nakuru?"
    """
    if not OPENWEATHER_API_KEY:
        return "Weather service is temporarily unavailable. Please try again later."

    try:
        # Fetch current weather
        current_url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={OPENWEATHER_API_KEY}&units=metric"
        current_response = requests.get(current_url)
        current_data = current_response.json()

        if current_response.status_code != 200 or "weather" not in current_data:
            return f"Could not retrieve weather data for {location}. Please check the location name."

        # Parse current weather
        city = current_data["name"]
        current_temp = current_data["main"]["temp"]
        current_desc = current_data["weather"][0]["description"]

        # Fetch forecast for the next few hours
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={location}&appid={OPENWEATHER_API_KEY}&units=metric"
        forecast_response = requests.get(forecast_url)
        forecast_data = forecast_response.json()

        if forecast_response.status_code != 200 or "list" not in forecast_data:
            return f"{city}: Now {current_temp}°C, {current_desc}. Forecast not available."

        # Get the next forecasted weather in 3 hours
        next_forecast = forecast_data["list"][0]  # 3-hour block
        forecast_temp = next_forecast["main"]["temp"]
        forecast_desc = next_forecast["weather"][0]["description"]

        return (
            f"{city}: Now {current_temp}°C, {current_desc}. "
            f"Forecast: {forecast_desc} at {forecast_temp}°C in 3 hours."
        )

    except Exception as e:
        return f"Weather lookup error: {str(e)}"

def fetch_news_from_reliable_sources(newsQuery:str) -> str:
    return "any relevant news based on what the user searched"

def tool_calling_llm(state:State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


llm = ChatGroq(model="llama-3.1-8b-instant",api_key='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')
tool = TavilySearch(max_results=2, tavily_api_key='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')
tools = [fetch_user_weather_data_for_use_in_advice]
llm_with_tools = llm.bind_tools(tools)
load_dotenv()


def generate_llm_response(user_message: str):
    system_message = {
        "role": "system",
        "content": (
            "You are a Farm Advisory Agent. Help farmers identify problems or solutions related to their farming questions. "
            "Respond in short, clear, use the user's language to respond to them. Maintain one currency if the user asks anything about money. Use Kenyan Shillings (KES)."
            " Keep it simple, avoid long words, and ensure it's easy to understand even on basic phones. Remove any '*' symbols in the response"
        )
    }

    user_msg = {"role": "user", "content": user_message}

    builder = StateGraph(State)
    builder.add_node("tool_calling_llm", tool_calling_llm)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "tool_calling_llm")
    builder.add_conditional_edges("tool_calling_llm", tools_condition)
    builder.add_edge("tools", "tool_calling_llm")

    graph = builder.compile()

    response = graph.invoke({"messages": [system_message, user_msg]})

    for m in response['messages']:
        m.pretty_print()

    return response['messages'][-1].content


if __name__ == "__main__":
    res = generate_llm_response("Tafadhali nipe hali ya anga ya Eldoret na kile mmea naweza panda, nipe mifano ya mimea ambayo naweza panda")
    print("<<response>>", res)


