import os
from dotenv import load_dotenv
from dateparser import parse as parse_date
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from calendar_utils import book_event, check_availability

# Load environment variables
load_dotenv()

# -------------------- Book Meeting Tool --------------------

class BookingInput(BaseModel):
    summary: str = Field(default="General Meeting", description="Title or subject of the meeting")
    start_time: str = Field(..., description="Start time in natural language (e.g., 'tomorrow at 10 PM')")
    end_time: str = Field(..., description="End time in natural language (e.g., 'tomorrow at 11 PM')")

def book_meeting(summary: str = "General Meeting", start_time: str = None, end_time: str = None) -> str:
    try:
        if not start_time or not end_time:
            return "❌ Please provide both start_time and end_time."

        # Convert natural language time to UTC
        start = parse_date(start_time, settings={
            "TIMEZONE": "Asia/Kolkata",
            "TO_TIMEZONE": "UTC",
            "RETURN_AS_TIMEZONE_AWARE": True
        })
        end = parse_date(end_time, settings={
            "TIMEZONE": "Asia/Kolkata",
            "TO_TIMEZONE": "UTC",
            "RETURN_AS_TIMEZONE_AWARE": True
        })

        if not start or not end:
            return "❌ Couldn't understand the time. Please use clear phrasing."

        start_iso = start.isoformat()
        end_iso = end.isoformat()

        event = book_event(summary, start_iso, end_iso)

        start_fmt = start.astimezone().strftime('%b %d, %I:%M %p')
        end_fmt = end.astimezone().strftime('%I:%M %p')

        return (f"✅ Meeting **'{summary}'** booked from **{start_fmt} to {end_fmt} IST**.\n"
                f"🔗 [View in Calendar]({event['htmlLink']})")
    except Exception as e:
        return f"❌ Booking failed: {str(e)}"

# -------------------- Check Calendar Tool --------------------

def check_calendar(_: str) -> str:
    try:
        events = check_availability()
        if not events:
            return "✅ You're free! No upcoming meetings found."
        return "\n".join([
            f"• **{e['summary']}** at `{e['start'].get('dateTime', e['start'].get('date'))}`"
            for e in events
        ])
    except Exception as e:
        return f"❌ Calendar check failed: {str(e)}"

# -------------------- Gemini Model --------------------

llm = ChatGoogleGenerativeAI(
    model="models/gemini-1.5-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    api_version="v1",
    temperature=0,
    task_type="conversational"
)

# -------------------- Tool Registration --------------------

tools = [
    StructuredTool.from_function(
        func=book_meeting,
        name="book_meeting",
        description="Use this tool to schedule meetings. Accepts meeting topic, start time, and end time in natural language.",
        args_schema=BookingInput
    ),
    StructuredTool.from_function(
        func=check_calendar,
        name="check_calendar",
        description=(
            "Use this tool to check the user's Google Calendar for upcoming meetings. "
            "Use it when the user asks things like: "
            "'Do I have meetings tomorrow?', 'What's on my calendar?', 'Am I free at 2 PM tomorrow?'."
        )
    )
]

# -------------------- Prompt Template --------------------

prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are TailorTalk, an AI assistant for Google Calendar.\n"
     "You can:\n"
     "- Book meetings using natural language like 'book a meeting tomorrow at 3 PM'\n"
     "- Check upcoming events using natural language like 'do I have meetings tomorrow?'\n"
     "Always use the tools provided to answer questions. Do not respond with 'I cannot access calendar'."),
    ("user", "{input}"),
    ("assistant", "{agent_scratchpad}")
])

# -------------------- LangChain Agent Setup --------------------

agent_chain = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)

agent = AgentExecutor.from_agent_and_tools(
    agent=agent_chain,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    return_intermediate_steps=False
)

# -------------------- Entry Point for FastAPI --------------------

def handle_intent(user_input: str) -> str:
    try:
        result = agent.invoke({"input": user_input})
        return result.get("output") or str(result)
    except Exception as e:
        print("❌ LangChain error:", e)
        return "❌ Something went wrong. Please try again."
