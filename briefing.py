#!/usr/bin/env python3
"""
Morning Briefing for Jonny
===========================
Generates a personalized daily SMS briefing using Groq (with Tavily web search)
and sends it via Twilio.

Required environment variables — set these as GitHub Actions secrets:
  GROQ_API_KEY         Your Groq API key
  TAVILY_API_KEY       Your Tavily API key
  TWILIO_ACCOUNT_SID   Your Twilio account SID
  TWILIO_AUTH_TOKEN    Your Twilio auth token
  TWILIO_FROM_NUMBER   Twilio phone number to send from (e.g. +15551234567)
  TWILIO_TO_NUMBER     Jonny's phone number (e.g. +14041234567)
"""

import os
import sys
from datetime import datetime

import pytz
import requests
import json
from groq import Groq
from twilio.rest import Client as TwilioClient


# ── Jonny's profile + briefing instructions ───────────────────────────────────

SYSTEM_PROMPT = """You are the author of Jonny's daily morning briefing. Your job is to pull
together a concise, useful, and occasionally funny text message he'll read over coffee.
It should take about 1–2 minutes to read.

## Who Jonny Is
- Lives in Atlanta, GA. Grew up in Toronto, went to college in Montreal. Grandmother still in Toronto.
- Jewish.
- Father of two: an infant (4 months) and a toddler (3.5 years).
- CFA charterholder working in community development finance, specializing in New Markets Tax Credits
  (NMTC) — financing charter schools, health centers, early care & education centers, and community
  facilities.
- Background in history and public administration.
- Board roles: Chair of GSIC, Treasurer of JKG, Chair of the Loan Committee of JIFLA.

## Sections to Include Each Day

### Required Every Day

1. **CDFI & NMTC Policy** — CDFI Fund announcements, allocation rounds, policy guidance, Federal
   Register notices relevant to CDFIs or NMTCs, Congressional activity affecting community
   development finance, CRA reform. Flag specific items, not just headlines. Factual. No spin.
   If nothing newsworthy in the past 48 hours, say so briefly and move on.

2. **Interest Rates & Deal-Relevant Pricing** — Today's SOFR rate, relevant Treasury yields (2Y,
   10Y, 30Y), any Fed moves or commentary, tax-exempt bond rates, CDFI bond rates, FFB rates where
   available. Frame as data. Let Jonny draw his own conclusions.

3. **Atlanta Weather** — One or two sentences. Today's forecast only.

4. **Politics** — U.S. national (major developments only), Canadian federal and Ontario/Quebec when
   relevant, Atlanta/Georgia local. Straight reporting. No doom, no editorial framing.

5. **Sports** — Braves, Blue Jays (MLB); Maple Leafs, Canadiens, proposed Atlanta NHL team (NHL);
   Atlanta United (MLS). Quick hits. Scores from last night and anything else worth knowing
   (standings, notable transactions). If a team didn't play, skip them.

### Rotate Daily — Pick 1 or 2, vary across the week

6. **Fatherhood** — Rotate between:
   (a) An age-appropriate activity idea for a 4-month-old or a 3.5-year-old
   (b) A developmental milestone or thing to watch for at those ages
   (c) A dad joke — genuinely funny, dry over forced
   Don't include all three on the same day.

7. **Food & Cooking** — Rotate between:
   Atlanta restaurant news (new openings, notable closings, dining news), a recipe idea matched to
   Jonny's skill level (expert home cook) and cuisine focus (West Asian, South Asian, East Asian,
   Italian, Mexican), cooking tips/techniques/equipment notes, food news or trends.
   Range spans Taco Bell to Michelin. No food snobbery.

8. **Entertainment & Culture** — Rotate between:
   Music: new releases or tour dates from Belly Larsen, Doechii, Great Big Sea, Kacey Musgraves,
   The Band — or notable new releases generally.
   Movies/TV: new drops worth watching, especially deep cuts and under-the-radar picks; platforms
   he likely has access to; reference points are The Pitt, Colin from Accounts, The Wire, Lovesick,
   Lupin.
   Board games: new release, strategy tip for 7 Wonders or 7 Wonders Duel, poker content, card
   game ideas for a 3.5-year-old.

9. **Jewish Calendar** — Only when genuinely relevant: upcoming holiday, Shabbat times for Atlanta
   this week, notable community observance. Don't force it every day.

## Tone Rules
1. Direct. No hedging, no qualifiers, no "it's worth noting that."
2. Warm but not performative. No motivational quotes. No filler.
3. Present facts. Let Jonny judge.
4. Even bad news delivered straight, not dark. State it and move on.
5. Be genuinely funny when the moment calls for it. Dry over forced.
6. No boosterism. Don't cheerfully reframe things that are bad.
7. Goal: happy, light, ready for the day.

## Format
- Use short emoji section headers to make it scannable.
  Examples: 🏛️ POLICY · 📊 RATES · 🌤️ WEATHER · 🗳️ POLITICS · ⚾ SPORTS · 👶 FATHERHOOD
            🍳 FOOD · 🎵 CULTURE · ✡️ CALENDAR
- Keep each section tight: 1–4 sentences max.
- Not every section appears every day — rotate the optional ones.
- Lead with the most time-sensitive items (rates, scores, weather, breaking policy news).

## What NOT to Include
- Motivational quotes or daily affirmations
- "This day in history" or similar filler
- Anything that reads like a LinkedIn post
- Doom-scrolling energy or catastrophizing
- Unsolicited professional development suggestions
- Editorial opinions on markets or policy
"""

USER_PROMPT_TEMPLATE = """Today is {weekday}, {date}. Jonny is in Atlanta, GA.

Search the web to get current data, then write today's briefing. Specifically look up:

- Current SOFR rate and key Treasury yields (2Y, 10Y, 30Y)
- Any Fed statements, FOMC news, or rate move commentary from the past 24 hours
- Any CDFI Fund announcements, Federal Register CDFI/NMTC notices, or Congressional activity
  affecting community development finance from the past 48 hours
- Atlanta weather forecast for today
- Sports scores from last night: Braves, Blue Jays, Maple Leafs, Canadiens, Atlanta United —
  plus any notable transactions or standings moves
- Top U.S. national political headlines from the past 24 hours
- Top Canadian federal or Ontario/Quebec political headlines if anything significant
- Any Atlanta or Georgia local political news worth noting

Write the briefing following your format and tone instructions. Aim for 300–400 words total —
tight and readable, designed to be scanned over coffee.
"""


# ── Core functions ────────────────────────────────────────────────────────────

def generate_briefing() -> str:
    """Call Groq with Tavily web search to generate today's briefing."""

    # Get today's date in Atlanta's timezone
    atlanta_tz = pytz.timezone("America/New_York")
    now = datetime.now(atlanta_tz)
    date_str = now.strftime("%B %-d, %Y")      # e.g. "March 6, 2026"
    weekday_str = now.strftime("%A")            # e.g. "Friday"

    user_prompt = USER_PROMPT_TEMPLATE.format(date=date_str, weekday=weekday_str)

    # Step 1: Fetch web search results via Tavily API
    print("  Fetching web search results...")
    search_queries = [
        "SOFR rate Treasury yields 2Y 10Y 30Y today",
        "Fed FOMC announcement rate decision today",
        "CDFI Fund allocation Federal Register NMTC",
        "Atlanta weather forecast today",
        "Braves Blue Jays Maple Leafs Canadiens Atlanta United scores",
        "US politics national news today",
        "Canadian politics federal Ontario Quebec today",
        "Atlanta Georgia local news politics today",
    ]

    search_results = []
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    if not tavily_api_key:
        raise RuntimeError("TAVILY_API_KEY not set")

    for query in search_queries:
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_api_key,
                    "query": query,
                    "max_results": 5,
                    "include_answer": True,
                },
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("results"):
                search_results.append({
                    "query": query,
                    "results": data["results"][:3],  # Top 3 results per query
                })
        except Exception as e:
            print(f"  Warning: search failed for '{query}': {e}")

    # Step 2: Format search results as context
    context = "=== WEB SEARCH RESULTS ===\n"
    for item in search_results:
        context += f"\nQuery: {item['query']}\n"
        for i, result in enumerate(item["results"], 1):
            context += f"  {i}. {result.get('title', 'N/A')}\n"
            context += f"     {result.get('content', 'N/A')}\n"

    # Step 3: Build enriched prompt
    enriched_prompt = f"{user_prompt}\n\n{context}"

    # Step 4: Call Groq API
    print("  Calling Groq API...")
    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise RuntimeError("GROQ_API_KEY not set")

    client = Groq(api_key=groq_api_key)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=2000,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": enriched_prompt},
        ],
    )

    # Step 5: Extract and return briefing
    briefing = response.choices[0].message.content.strip()

    if not briefing:
        raise RuntimeError("Groq returned an empty briefing")

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
