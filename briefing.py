#!/usr/bin/env python3
"""
Morning Briefing for Jonny
===========================
Generates a personalized daily SMS briefing using Claude (with live web search)
and sends it via Twilio.

Required environment variables — set these as GitHub Actions secrets:
  ANTHROPIC_API_KEY    Your Anthropic API key
  TWILIO_ACCOUNT_SID   Your Twilio account SID
  TWILIO_AUTH_TOKEN    Your Twilio auth token
  TWILIO_FROM_NUMBER   Twilio phone number to send from (e.g. +15551234567)
  TWILIO_TO_NUMBER     Jonny's phone number (e.g. +14041234567)
"""

import os
import sys
from datetime import datetime

import pytz
import anthropic
from twilio.rest import Client as TwilioClient


# ── Jonny's profile + briefing instructions ───────────────────────────────────

SYSTEM_PROMPT = """You are the author of Jonny's daily morning briefing — a concise SMS he reads over coffee (1–2 min).

## Who Jonny Is
- Atlanta, GA. Jewish. Father of a 4-month-old and a 3.5-year-old.
- CFA charterholder in community development finance, specializing in NMTCs (financing charter schools, health centers, community facilities).
- Board: Chair of GSIC, Treasurer of JKG, Chair of JIFLA Loan Committee.

## Sections (Required Every Day)

🏛️ **CDFI & NMTC Policy** — CDFI Fund announcements, Federal Register notices, Congressional activity, CRA reform. Flag specifics, not headlines. If nothing in 48 hours, say so briefly.

📊 **Rates** — SOFR, Treasury yields (2Y, 10Y, 30Y), Fed commentary, tax-exempt bond rates. Data only, no opinions.

🌤️ **Weather** — Atlanta today. One or two sentences.

🗳️ **Politics** — U.S. national (major only), Atlanta/Georgia local. Straight reporting.

### Rotate Daily — Pick 1

👶 **Fatherhood** — One of: activity idea for a 4-month-old or 3.5-year-old; developmental milestone; dry dad joke.

🍳 **Food** — One of: Atlanta restaurant news; recipe idea (expert home cook, West/South/East Asian, Italian, or Mexican); cooking tip; food news.

✡️ **Jewish Calendar** — Only when relevant: upcoming holiday, Shabbat times, notable observance. Skip if nothing genuine.

## Tone
Direct. Warm, not performative. Facts only — let Jonny judge. Dry humor when it fits. No hedging, no filler, no doom.

## Format
- Emoji section headers. 1–4 sentences per section. Lead with time-sensitive items.
- 300–400 words total.
"""

USER_PROMPT_TEMPLATE = """Today is {weekday}, {date}. Jonny is in Atlanta, GA.

Search the web to get current data, then write today's briefing. Specifically look up:

- Current SOFR rate and key Treasury yields (2Y, 10Y, 30Y)
- Any Fed statements, FOMC news, or rate move commentary from the past 24 hours
- Any CDFI Fund announcements, Federal Register CDFI/NMTC notices, or Congressional activity
  affecting community development finance from the past 48 hours
- Atlanta weather forecast for today
- Top U.S. national political headlines from the past 24 hours
- Any Atlanta or Georgia local political news worth noting

Write the briefing following your format and tone instructions. 300–400 words, scannable over coffee.
"""


# ── Core functions ────────────────────────────────────────────────────────────

def generate_briefing() -> str:
    """Call Claude with live web search to generate today's briefing."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Get today's date in Atlanta's timezone
    atlanta_tz = pytz.timezone("America/New_York")
    now = datetime.now(atlanta_tz)
    date_str = now.strftime("%B %-d, %Y")      # e.g. "March 6, 2026"
    weekday_str = now.strftime("%A")            # e.g. "Friday"

    user_prompt = USER_PROMPT_TEMPLATE.format(date=date_str, weekday=weekday_str)

    # Server-side web search and fetch tools — Claude handles the search loop
    # automatically on Anthropic's infrastructure. No client-side execution needed.
    tools = [
        {"type": "web_search_20260209", "name": "web_search"},
        {"type": "web_fetch_20260209",  "name": "web_fetch"},
    ]

    messages = [{"role": "user", "content": user_prompt}]

    # Claude's server-side tool loop can hit a 10-iteration limit and return
    # stop_reason="pause_turn". When that happens, re-send the conversation to
    # let it continue. We cap this at 5 rounds to stay sane.
    max_continuations = 3
    final_response = None

    for attempt in range(max_continuations):
        print(f"  API call {attempt + 1}/{max_continuations}...")

        with client.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=3000,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        ) as stream:
            response = stream.get_final_message()

        print(f"  stop_reason={response.stop_reason}")

        if response.stop_reason in ("end_turn", "stop_sequence"):
            final_response = response
            break

        elif response.stop_reason == "pause_turn":
            # Server-side tool loop hit its iteration cap. Re-send the full
            # conversation so Claude can pick up where it left off.
            messages = [
                {"role": "user",      "content": user_prompt},
                {"role": "assistant", "content": response.content},
            ]
            final_response = response  # keep as fallback if loop ends here

        else:
            # Unexpected stop reason — take what we have
            final_response = response
            break

    if final_response is None:
        raise RuntimeError("No response received from Claude")

    # Pull out all text blocks from the response
    text_parts = [
        block.text
        for block in final_response.content
        if hasattr(block, "text") and block.text
    ]
    briefing = "\n\n".join(text_parts).strip()

    if not briefing:
        raise RuntimeError("Claude returned an empty briefing")

    return briefing


def send_sms(message: str) -> None:
    """Send the briefing to Jonny via Twilio SMS.

    Twilio automatically splits messages longer than 160 characters into
    concatenated segments (up to 1,600 characters total recommended). For a
    1–2 minute read (~300–400 words), expect 5–10 SMS segments delivered
    as one threaded message on most modern phones.
    """
    twilio_client = TwilioClient(
        os.environ["TWILIO_ACCOUNT_SID"],
        os.environ["TWILIO_AUTH_TOKEN"],
    )

    result = twilio_client.messages.create(
        body=message,
        from_=os.environ["TWILIO_FROM_NUMBER"],
        to=os.environ["TWILIO_TO_NUMBER"],
    )

    print(f"SMS sent. Twilio SID: {result.sid}, status: {result.status}")


# ── Entry point ───────────────────────────────────────────────────────────────

def check_atlanta_time() -> bool:
    """Return True only if Atlanta's clock is currently between 6:00–7:00 AM.

    The workflow fires at both 10:30 UTC and 11:30 UTC every day to cover
    EDT and EST. This check ensures exactly one of those runs actually sends
    the briefing, regardless of DST transitions.
    """
    atlanta_tz = pytz.timezone("America/New_York")
    hour = datetime.now(atlanta_tz).hour
    return 6 <= hour < 7


def main():
    atlanta_tz = pytz.timezone("America/New_York")
    now = datetime.now(atlanta_tz)
    print(f"Atlanta time: {now.strftime('%H:%M %Z')}")

    # Skip the time-gate for manual runs triggered via the GitHub Actions UI.
    manual_run = os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch"
    if not manual_run and not check_atlanta_time():
        print("Outside the 6–7 AM window — skipping. (The other cron will handle it.)")
        sys.exit(0)

    print("Generating morning briefing...")

    try:
        briefing = generate_briefing()
    except Exception as exc:
        print(f"ERROR generating briefing: {exc}", file=sys.stderr)
        sys.exit(1)

    print("\n" + "─" * 60)
    print(briefing)
    print("─" * 60 + "\n")

    try:
        send_sms(briefing)
    except Exception as exc:
        print(f"ERROR sending SMS: {exc}", file=sys.stderr)
        sys.exit(1)

    print("Done.")


if __name__ == "__main__":
    main()
