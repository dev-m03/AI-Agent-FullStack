import os
import json
from dotenv import load_dotenv
from dateparser import parse as parse_date
import google.generativeai as genai

from calendar_utils import book_event, check_availability

load_dotenv()

# ======================================================
# Configure Gemini (official SDK)
# ======================================================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ======================================================
# Pick a working text model dynamically (NO HARDCODE)
# ======================================================
def get_working_model():
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            # Prefer Gemini 1.5 Flash if available
            if "gemini-1.5-flash" in m.name:
                return genai.GenerativeModel(m.name)
    # Fallback: first available text model
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            return genai.GenerativeModel(m.name)
    raise RuntimeError("No usable Gemini model found")

model = get_working_model()

# ======================================================
# Main intent handler
# ======================================================
def handle_intent(user_input: str) -> str:
    try:
        prompt = f"""
You help users manage Google Calendar.

User message:
"{user_input}"

Respond ONLY in valid JSON.

If user wants to check calendar:
{{ "intent": "check" }}

If user wants to book a meeting:
{{
  "intent": "book",
  "summary": "meeting title",
  "start_time": "natural language time",
  "end_time": "natural language time"
}}

Return ONLY JSON.
"""

        response = model.generate_content(prompt)
        data = json.loads(response.text.strip())

        # ---------------- CHECK CALENDAR ----------------
        if data["intent"] == "check":
            events = check_availability()
            if not events:
                return "✅ You're free!"

            return "\n".join(
                f"• **{e.get('summary','No title')}** at "
                f"`{e['start'].get('dateTime', e['start'].get('date'))}`"
                for e in events
            )

        # ---------------- BOOK MEETING ----------------
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
