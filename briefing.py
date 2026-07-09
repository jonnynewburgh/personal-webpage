#!/usr/bin/env python3
"""
Morning Briefing for Jonny
===========================
Generates a personalized daily briefing using Groq (with Tavily web search)
and sends it via email over Gmail SMTP.

Required environment variables — set these as GitHub Actions secrets:
  GROQ_API_KEY         Your Groq API key
  TAVILY_API_KEY       Your Tavily API key
  GMAIL_ADDRESS        Gmail account to send from / authenticate as
  GMAIL_APP_PASSWORD   Gmail App Password (not your account password)
  RECIPIENT            Where to deliver (optional; defaults to GMAIL_ADDRESS)
"""

import os
import re
import sys
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

import pytz
import requests
from groq import Groq


# ── Jonny's profile + briefing instructions ───────────────────────────────────

SYSTEM_PROMPT = """You are the author of Jonny's daily morning briefing — a tight,
scannable plain-text email he reads over coffee, written in Axios "Smart Brevity" style.

## Smart Brevity style
- Open each section with one punchy takeaway line, then 1–2 short sentences or a few "-"
  bullets. Paragraphs rarely exceed two sentences.
- Information-dense but brief — every line earns its place. No padding, no hedging, no
  wind-up, no "it's worth noting". Cut needless words.
- Use plain-text label cues where useful: "Why it matters:", "By the numbers:",
  "The latest:", "Go deeper:".
- Plain text only. No Markdown — no ** or ## characters (they won't render in email).
  Separate sections with a blank line. Emoji section headers are good.

## Voice
Write directly. The profile below tells you WHAT to cover — it is background for choosing
content, NOT something to talk about. Never refer to "Jonny" in the third person, never
explain why an item is relevant to him personally, and never write filler like "you may be
interested in" or "as someone who works in...". Just give the information. ("Why it matters"
explains an item's objective significance, never personal relevance.)

## Currency & sourcing
- Today's date is in the user message. Report only what is genuinely current: lead with
  dates, and never present an old item as if it just happened. Undated program or reference
  pages (e.g. a past CDFI Fund allocation round or NOAA) are background, not news.
- Ground every fact — every rate, score, date, announcement — in the search results below.
  Do not invent figures or URLs or rely on memory.
- Cite sources INLINE, right after the claim they support, as a markdown link using the
  publication or site name as the link text and the exact URL from the search results —
  e.g. "SOFR is 3.60% ([New York Fed](https://newyorkfed.org/...))" or a
  "Go deeper: [Axios](https://...)" line. Use the outlet/site name (e.g. "Reuters",
  "CDFI Fund", "AccuWeather"), never the raw URL, as the visible link text. Do NOT put a
  sources list at the bottom.
- If a section has no genuine, current update, OMIT it entirely — no "nothing new" filler.
  Weather and rates always have data; news sections appear only when there's something real.
- This applies to individual lines too. NEVER write "no data available", "no game results",
  "no new announcements", "not directly available", or similar. If you don't have something,
  leave it out silently. For rates, list only the tenors you can actually source — do not
  enumerate the ones you're missing.

## Who Jonny Is
- Lives in Atlanta, GA. Grew up in Toronto, went to college in Montreal. Grandmother still in Toronto.
- Jewish.
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
   Only items genuinely about the CDFI Fund, NMTC, CDFIs, or CRA — ignore unrelated "tax
   credit" or general finance stories. If there's nothing genuinely on-topic and current,
   omit this section entirely (do not write a "no announcements" line).

2. **Interest Rates & Deal-Relevant Pricing** — SOFR and Treasury yields at the 3-month,
   2-year, 7-year, and 10-year tenors come from the "AUTHORITATIVE RATES" block — use those
   exact figures and their source URLs. Add any Fed moves or commentary from the news results.
   Frame as data. Let Jonny draw his own conclusions.

3. **Atlanta Weather** — One or two sentences. Today's forecast only.

4. **Politics** — U.S. national (major developments only), Canadian federal and Ontario/Quebec when
   relevant, Atlanta/Georgia local. Straight reporting. No doom, no editorial framing. Name the
   specific development — who, what, when. If the only material is generic, undated, or a news
   site's landing page, OMIT politics rather than reporting vague filler.

5. **Sports** — Braves, Blue Jays (MLB); Maple Leafs, Canadiens, proposed Atlanta NHL team (NHL);
   Atlanta United (MLS). Quick hits. Scores from last night and anything else worth knowing
   (standings, notable transactions). If a team didn't play, skip them.

### Rotate Daily — Pick 2 or 3, vary across the week

6. **Food & Cooking** — Rotate between:
   Atlanta restaurant news (new openings, notable closings, dining news), a recipe idea matched to
   Jonny's skill level (expert home cook) and cuisine focus (West Asian, South Asian, East Asian,
   Italian, Mexican), cooking tips/techniques/equipment notes, food news or trends.
   Range spans Taco Bell to Michelin. No food snobbery.

7. **Entertainment & Culture** — Rotate between:
   Music: new releases or tour dates from Belly Larsen, Doechii, Great Big Sea, Kacey Musgraves,
   The Band — or notable new releases generally.
   Movies/TV: new drops worth watching, especially deep cuts and under-the-radar picks; platforms
   he likely has access to; reference points are The Pitt, Colin from Accounts, The Wire, Lovesick,
   Lupin.
   Board games: new release, strategy tip for 7 Wonders or 7 Wonders Duel, poker content.

8. **Jewish Calendar** — Only when genuinely relevant: upcoming holiday, Shabbat times for Atlanta
   this week, notable community observance. Don't force it every day.

## Tone Rules
1. Direct. No hedging, no qualifiers, no "it's worth noting that."
2. Warm but not performative. No motivational quotes. No filler.
3. Present facts. Let Jonny judge.
4. Even bad news delivered straight, not dark. State it and move on.
5. Be genuinely funny when the moment calls for it. Dry over forced.
6. No boosterism. Don't cheerfully reframe things that are bad.
7. Goal: happy, light, ready for the day.

## Ordering & headers
- Use short emoji section headers to make it scannable.
  Examples: 🏛️ POLICY · 📊 RATES · 🌤️ WEATHER · 🗳️ POLITICS · ⚾ SPORTS
            🍳 FOOD · 🎵 CULTURE · ✡️ CALENDAR
- Lead with the most time-sensitive items (rates, scores, weather, breaking policy news).
- Rotate the optional sections; not every section appears every day.

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

- Current SOFR rate and Treasury yields at the 3-month, 2-year, 7-year, and 10-year tenors
- Any Fed statements, FOMC news, or rate move commentary from the past 24 hours
- Any CDFI Fund announcements, Federal Register CDFI/NMTC notices, or Congressional activity
  affecting community development finance from the past 48 hours
- Atlanta weather forecast for today
- Sports scores from last night: Braves, Blue Jays, Maple Leafs, Canadiens, Atlanta United —
  plus any notable transactions or standings moves
- Top U.S. national political headlines from the past 24 hours
- Top Canadian federal or Ontario/Quebec political headlines if anything significant
- Any Atlanta or Georgia local political news worth noting
- Atlanta restaurant openings, closings, or dining news this week
- New music releases / tour dates and notable new TV or streaming drops this week

Write the briefing in Axios Smart Brevity style: tight, scannable, plain text, with a punchy
takeaway line and short "-" bullets per section. Cite each fact inline as a markdown link
using the source's name as the link text (e.g. "[Reuters](https://...)"), not the raw URL,
from the results above — no bottom sources list. Lead with dates, ground every claim in the
sources, never present anything stale as if it's new, and OMIT any section that has no
current update.
"""


# ── Core functions ────────────────────────────────────────────────────────────

# Placeholder phrases the model writes when it has nothing — despite being told not
# to. We strip these deterministically rather than relying on the model to comply.
_FILLER_RE = re.compile(
    r"(no (new|other|current|relevant|additional|game|further)\b"
    r"|not (currently |directly )?available"
    r"|nothing (new|to report|else|notable)"
    r"|no (data|updates?|announcements?|results?|scores?|news)\b"
    r"|:\s*(not available|n/?a|none|tbd))",
    re.I,
)


def strip_filler(briefing: str) -> str:
    """Remove 'nothing to report' filler lines, then drop any section left empty.

    Sections are blank-line-separated blocks: a header line followed by content.
    A line is dropped if it's a filler placeholder; a whole block is dropped if no
    real content survives. This guarantees no filler regardless of model compliance.
    """
    cleaned = []
    for block in re.split(r"\n\s*\n", briefing.strip()):
        lines = block.split("\n")
        header, content = lines[0], lines[1:]
        kept = [ln for ln in content if ln.strip() and not _FILLER_RE.search(ln)]
        if not kept:
            continue  # header had no real content beneath it — drop the section
        cleaned.append("\n".join([header] + kept))
    return "\n\n".join(cleaned)


def fetch_rates() -> list:
    """Fetch authoritative current rates from structured sources, not web search.

    SOFR comes from the NY Fed reference-rates API; the Treasury par yield curve
    (3mo/2yr/7yr/10yr) from Treasury's daily XML feed. Both are keyless. Each source
    is failure-tolerant — a failed fetch just omits those rates, never raises.

    Returns a list of (label, value, as_of_date, source_url) tuples.
    """
    rates = []

    # SOFR — Federal Reserve Bank of New York
    try:
        r = requests.get(
            "https://markets.newyorkfed.org/api/rates/secured/sofr/last/1.json",
            timeout=15,
        )
        r.raise_for_status()
        ref = r.json()["refRates"][0]
        rates.append((
            "SOFR", ref["percentRate"], ref["effectiveDate"],
            "https://www.newyorkfed.org/markets/reference-rates/sofr",
        ))
    except Exception as e:
        print(f"  Warning: SOFR fetch failed: {e}")

    # Treasury par yield curve — latest published business day. Try the current
    # month; early in a month it can be empty, so fall back to the previous month.
    def _fetch_curve_xml(yyyymm):
        url = (
            "https://home.treasury.gov/resource-center/data-chart-center/"
            "interest-rates/pages/xml?data=daily_treasury_yield_curve"
            f"&field_tdr_date_value_month={yyyymm}"
        )
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.text

    try:
        now = datetime.now(pytz.timezone("America/New_York"))
        xml = _fetch_curve_xml(now.strftime("%Y%m"))
        if not re.search(r"<d:NEW_DATE", xml):
            prev = (now.replace(day=1) - timedelta(days=1)).strftime("%Y%m")
            xml = _fetch_curve_xml(prev)

        def last_val(tag):
            vals = re.findall(rf"<d:{tag}[^>]*>([^<]+)</d:{tag}>", xml)
            return vals[-1] if vals else None

        dates = re.findall(r"<d:NEW_DATE[^>]*>([^<]+)</d:NEW_DATE>", xml)
        as_of = dates[-1][:10] if dates else None
        src = ("https://home.treasury.gov/resource-center/data-chart-center/"
               "interest-rates/TextView?type=daily_treasury_yield_curve")
        for label, tag in [("3-month", "BC_3MONTH"), ("2-year", "BC_2YEAR"),
                           ("7-year", "BC_7YEAR"), ("10-year", "BC_10YEAR")]:
            val = last_val(tag)
            if val:
                rates.append((label, val, as_of, src))
    except Exception as e:
        print(f"  Warning: Treasury yield curve fetch failed: {e}")

    return rates


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
    # Time-sensitive queries use Tavily's news topic + a recency window ("days")
    # so they return actual recent stories instead of evergreen landing pages or
    # year-old announcements. Weather stays on general search (data page, not "news").
    # Empty results are fine — the prompt omits sections with no update. SOFR and the
    # Treasury curve come from structured APIs (fetch_rates), not web search.
    search_queries = [
        {"q": "Federal Reserve FOMC interest rate decision or statement", "days": 7},
        {"q": "CDFI Fund New Markets Tax Credit NMTC announcement or Federal Register notice", "days": 21},
        {"q": "Atlanta weather forecast today"},
        {"q": "Braves Blue Jays Atlanta United score result last night", "days": 2},
        {"q": "top US national political news developments", "days": 2},
        {"q": "Canada federal Ontario Quebec political news", "days": 3},
        {"q": "Atlanta Georgia state politics news", "days": 3},
        {"q": "Atlanta restaurant opening closing dining news", "days": 21},
        {"q": "new music album release and new TV streaming show", "days": 14},
    ]

    search_results = []
    tavily_api_key = os.environ.get("TAVILY_API_KEY")
    if not tavily_api_key:
        raise RuntimeError("TAVILY_API_KEY not set")

    for spec in search_queries:
        query = spec["q"]
        payload = {
            "api_key": tavily_api_key,
            "query": query,
            "max_results": 5,
            "include_answer": True,
        }
        # A "days" window implies a news-topic search (recency-ranked, dated results).
        if "days" in spec:
            payload["topic"] = "news"
            payload["days"] = spec["days"]
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("results"):
                search_results.append({
                    "query": query,
                    "results": data["results"][:3],  # Top 3 per query (TPM-bounded)
                    "cap": spec.get("cap", 400),      # snippet char cap for this query
                })
        except Exception as e:
            print(f"  Warning: search failed for '{query}': {e}")

    # Step 2: Format search results as context. Include each source's URL and
    # publish date (when Tavily provides one) so the model can cite it and judge
    # how fresh the item actually is — undated pages are treated as background.
    context = "=== WEB SEARCH RESULTS ===\n"
    for item in search_results:
        context += f"\nQuery: {item['query']}\n"
        cap = item.get("cap", 400)
        for i, result in enumerate(item["results"], 1):
            published = result.get("published_date") or "no date given"
            # Cap each snippet so extra queries don't blow the Groq free-tier TPM limit.
            snippet = (result.get("content") or "N/A")[:cap]
            context += f"  {i}. {result.get('title', 'N/A')}\n"
            context += f"     URL: {result.get('url', 'N/A')} | Published: {published}\n"
            context += f"     {snippet}\n"

    # Step 2b: Authoritative rates from structured sources (not web search), so the
    # rates section is always complete and accurate. Prepended to the context and
    # marked authoritative so the model uses these exact figures and source URLs.
    rates = fetch_rates()
    if rates:
        rates_block = (
            "=== AUTHORITATIVE RATES — use these EXACT figures and source URLs for the "
            "rates section; do NOT substitute web-search numbers ===\n"
        )
        for label, val, as_of, url in rates:
            rates_block += f"- {label}: {val}% (as of {as_of}) — source: {url}\n"
        context = rates_block + "\n" + context

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
        max_tokens=3500,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": enriched_prompt},
        ],
    )

    # Step 5: Extract briefing. Sources are cited inline by the model (see prompt),
    # so there's no appended sources list.
    briefing = response.choices[0].message.content.strip()

    if not briefing:
        raise RuntimeError("Groq returned an empty briefing")

    # Deterministically remove any filler the model added despite the prompt.
    briefing = strip_filler(briefing)

    if not briefing:
        raise RuntimeError("Briefing was empty after stripping filler")

    return briefing


_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")


def _markdown_links_to_html(text: str) -> str:
    """Convert [Source Name](url) markdown links to <a> tags and escape the rest."""
    import html as _html

    out = []
    pos = 0
    for m in _MD_LINK_RE.finditer(text):
        out.append(_html.escape(text[pos:m.start()]))
        label, url = m.group(1), m.group(2)
        out.append(f'<a href="{_html.escape(url)}">{_html.escape(label)}</a>')
        pos = m.end()
    out.append(_html.escape(text[pos:]))
    return "".join(out)


def _briefing_to_html(message: str) -> str:
    """Render the plain-text briefing as HTML, turning markdown links into <a> tags."""
    paragraphs = message.strip().split("\n\n")
    blocks = []
    for para in paragraphs:
        html_para = _markdown_links_to_html(para).replace("\n", "<br>\n")
        blocks.append(f"<p>{html_para}</p>")
    body = "\n".join(blocks)
    return (
        '<html><body style="font-family: -apple-system, Helvetica, Arial, sans-serif; '
        'font-size: 15px; line-height: 1.5; color: #1a1a1a;">\n'
        f"{body}\n</body></html>"
    )


def _markdown_links_to_plain(text: str) -> str:
    """Fallback for non-HTML mail clients: '[Name](url)' -> 'Name (url)'."""
    return _MD_LINK_RE.sub(r"\1 (\2)", text)


def send_email(message: str) -> None:
    """Send the briefing to Jonny via Gmail SMTP.

    Uses Python's stdlib smtplib + email — no third-party dependencies.
    Connects over implicit TLS (SMTP_SSL) on port 465, so the exchange is
    encrypted from the first byte with no STARTTLS upgrade step. Email has
    no practical body-length limit, so the full briefing is sent as-is.

    Sent as multipart/alternative: an HTML part with source names as real
    hyperlinks, and a plain-text fallback with "Name (url)" for clients that
    don't render HTML.

    Fails closed: a missing or blank required variable raises before any
    network call, and any SMTP error propagates to the caller.
    """
    gmail_address = os.environ.get("GMAIL_ADDRESS", "").strip()
    app_password = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    if not gmail_address:
        raise RuntimeError("GMAIL_ADDRESS is not set")
    if not app_password:
        raise RuntimeError("GMAIL_APP_PASSWORD is not set")
    recipient = os.environ.get("RECIPIENT", "").strip() or gmail_address

    atlanta_tz = pytz.timezone("America/New_York")
    date_str = datetime.now(atlanta_tz).strftime("%A, %B %-d, %Y")

    email = EmailMessage()
    email["Subject"] = f"Morning Briefing — {date_str}"
    email["From"] = gmail_address
    email["To"] = recipient
    email.set_content(_markdown_links_to_plain(message))
    email.add_alternative(_briefing_to_html(message), subtype="html")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, app_password)
        server.send_message(email)

    print(f"Email sent to {recipient}.")


# ── Entry point ───────────────────────────────────────────────────────────────

def check_atlanta_time() -> bool:
    """Return True only if Atlanta's clock is currently between 6:00–9:00 AM.

    The workflow fires at both 10:30 UTC and 11:30 UTC every day to cover
    EDT and EST. This check ensures exactly one of those runs actually sends
    the briefing, regardless of DST transitions. Widened from a 1-hour to a
    3-hour window because GitHub's scheduled-cron queue routinely delays
    "schedule"-triggered runs by 2-4+ hours, which was causing every run to
    land outside a narrower window and silently skip for weeks.
    """
    atlanta_tz = pytz.timezone("America/New_York")
    hour = datetime.now(atlanta_tz).hour
    return 6 <= hour < 9


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
        send_email(briefing)
    except Exception as exc:
        print(f"ERROR sending email: {exc}", file=sys.stderr)
        sys.exit(1)

    print("Done.")


if __name__ == "__main__":
    main()
