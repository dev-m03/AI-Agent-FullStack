import os
from dotenv import load_dotenv
from dateparser import parse as parse_date

from calendar_utils import book_event, check_availability

from langchain.tools import StructuredTool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

load_dotenv()

# ======================================================
# Input schema for booking tool
# ======================================================
class BookingInput(BaseModel):
    summary: str = Field(
        default="General Meeting",
        description="Meeting title or purpose"
    )
    start_time: str = Field(
        ...,
        description="Start time (e.g., 'tomorrow at 10 PM')"
    )
    end_time: str = Field(
        ...,
        description="End time (e.g., 'tomorrow at 11 PM')"
    )

# ======================================================
# Tool: Book meeting
# ======================================================
def book_meeting(
    summary: str = "General Meeting",
    start_time: str | None = None,
    end_time: str | None = None
) -> str:
    try:
        if not start_time or not end_time:
            return "❌ Please provide both start_time and end_time."

        start = parse_date(
            start_time,
            settings={
                "TIMEZONE": "Asia/Kolkata",
                "TO_TIMEZONE": "UTC",
                "RETURN_AS_TIMEZONE_AWARE": True,
            },
        )
        end = parse_date(
            end_time,
            settings={
                "TIMEZONE": "Asia/Kolkata",
                "TO_TIMEZONE": "UTC",
                "RETURN_AS_TIMEZONE_AWARE": True,
            },
        )

        if not start or not end:
            return "❌ Couldn't understand the provided time. Please try again."

        event = book_event(
            summary,
            start.isoformat(),
            end.isoformat()
        )

        start_fmt = start.astimezone().strftime("%b %d, %I:%M %p")
        end_fmt = end.astimezone().strftime("%I:%M %p")

        return (
            f"✅ Meeting **'{summary}'** booked from "
            f"**{start_fmt} to {end_fmt} IST**.\n"
            f"🔗 [View in Calendar]({event['htmlLink']})"
        )

    except Exception as e:
        return f"❌ Booking failed: {str(e)}"

# ======================================================
# Tool: Check calendar (NO params – IMPORTANT)
# ======================================================
def check_calendar() -> str:
    try:
        events = check_availability()
        if not events:
            return "✅ You're free!"

        return "\n".join(
            f"• **{e.get('summary', 'No title')}** at "
            f"`{e['start'].get('dateTime', e['start'].get('date'))}`"
            for e in events
        )

    except Exception as e:
        return f"❌ Calendar check failed: {str(e)}"

# ======================================================
# Gemini LLM (STABLE + SUPPORTED)
# ======================================================
llm = ChatGoogleGenerativeAI(
    model="gemini-pro",                     # ✅ supported by LangChain
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0,
    convert_system_message_to_human=True    # 🔥 REQUIRED
)

# ======================================================
# Tools
# ======================================================
tools = [
    StructuredTool.from_function(
        func=book_meeting,
        name="book_meeting",
        description="Book a meeting using summary, start_time, and end_time (natural language supported).",
        args_schema=BookingInput,
    ),
    StructuredTool.from_function(
        func=check_calendar,
        name="check_calendar",
        description="Check your upcoming Google Calendar events.",
    ),
]

# ======================================================
# Prompt
# ======================================================
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are TailorTalk, an AI assistant that helps users book meetings and "
            "check calendars. You understand natural language like "
            "'tomorrow at 10 PM IST'. Always include the calendar link when booking."
        ),
        ("user", "{input}"),
        ("assistant", "{agent_scratchpad}")
    ]
)

# ======================================================
# Agent
# ======================================================
agent_chain = create_openai_functions_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

agent = AgentExecutor.from_agent_and_tools(
    agent=agent_chain,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)

# ======================================================
# Entry function called by FastAPI
# ======================================================
def handle_intent(user_input: str) -> str:
    try:
        result = agent.invoke({"input": user_input})
        return result["output"]
    except Exception as e:
        print("❌ LangChain error:", e)
        return f"❌ Backend error: {str(e)}"
