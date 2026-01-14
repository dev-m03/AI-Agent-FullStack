import os
import json
from dotenv import load_dotenv
from dateparser import parse as parse_date
import google.generativeai as genai

from calendar_utils import book_event, check_availability

load_dotenv()

# ======================================================
# Configure Gemini (OFFICIAL SDK – STABLE)
# ======================================================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")

# ======================================================
# Main intent handler (called by FastAPI)
# ======================================================
def handle_intent(user_input: str) -> str:
    try:
        prompt = f"""
You are an assistant that helps users with Google Calendar.

User input:
"{user_input}"

Decide intent and respond ONLY in valid JSON.

If the user wants to check calendar:
{{ "intent": "check" }}

If the user wants to book a meeting:
{{
  "intent": "book",
  "summary": "meeting title",
  "start_time": "natural language time",
  "end_time": "natural language time"
}}

Return ONLY JSON. No markdown. No explanation.
"""

        response = model.generate_content(prompt)
        data = json.loads(response.text.strip())

        # -----------------------
        # CHECK CALENDAR
        # -----------------------
        if data["intent"] == "check":
            events = check_availability()
            if not events:
                return "✅ You're free!"

            return "\n".join(
                f"• **{e.get('summary', 'No title')}** at "
                f"`{e['start'].get('dateTime', e['start'].get('date'))}`"
                for e in events
            )

        # -----------------------
        # BOOK MEETING
        # -----------------------
        if data["intent"] == "book":
            start = parse_date(data["start_time"])
            end = parse_date(data["end_time"])

            if not start or not end:
                return "❌ Could not understand the provided time."

            event = book_event(
                data.get("summary", "Meeting"),
                start.isoformat(),
                end.isoformat()
            )

            return (
                f"✅ Meeting booked!\n"
                f"🔗 [View in Calendar]({event['htmlLink']})"
            )

        return "❌ Unknown intent."

    except Exception as e:
        print("❌ Backend error:", e)
        return f"❌ Error: {str(e)}"
