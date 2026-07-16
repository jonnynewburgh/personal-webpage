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
from datetime import datetime, timedelta, timezone
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
- Breaking-news sections (Politics, Fed/rate commentary) are last-24-hours only. Check each
  result's Published date against today's date — if it's more than 24 hours old, drop it, even
  if it's the best or only item found. A thinner section beats a stale item reported as new.
  CDFI & NMTC Policy moves slower, so a somewhat wider window (per the search results provided)
  is fine there, but still lead with the actual date and never imply something is new when it
  isn't.
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

1. **Atlanta Weather** — One or two sentences. Today's forecast only.

2. **Interest Rates & Deal-Relevant Pricing** — SOFR and Treasury yields at the 3-month,
   2-year, 7-year, and 10-year tenors come from the "AUTHORITATIVE RATES" block — use those
   exact figures and their source URLs. Add any Fed moves or commentary from the news results.
   Frame as data. Let Jonny draw his own conclusions. A trend chart is attached automatically
   after this section — do not write a trend line or list of 7d/30d/365d changes yourself.

3. **CDFI & NMTC Policy** — CDFI Fund announcements, allocation rounds, policy guidance, Federal
   Register notices relevant to CDFIs or NMTCs, Congressional activity affecting community
   development finance, CRA reform. Flag specific items, not just headlines. Factual. No spin.
   Only items genuinely about the CDFI Fund, NMTC, CDFIs, or CRA — ignore unrelated "tax
   credit" or general finance stories. If there's nothing genuinely on-topic and current,
   omit this section entirely (do not write a "no announcements" line).

3b. **Economy & Credit** — Every item in the "AUTHORITATIVE INDICATORS" block is a fresh
   release from the last ~36 hours (FRED-filtered). If the block is absent or empty, OMIT
   this section entirely — do not fall back to prior-month numbers, do not describe what's
   "typical", do not mention that data was checked. Use the exact figures and source URLs.
   Possible items when present:
     - Labor: unemployment rate (U-3), U-6 underemployment, latest nonfarm payroll change and
       the two prior months (call out any revision to the prior print if the news results
       mention one), avg hourly earnings YoY, weekly initial jobless claims.
     - Inflation: latest headline & core CPI (MoM and YoY), core PCE (MoM and YoY).
     - Growth: Atlanta Fed GDPNow nowcast.
     - Credit/housing: ICE BofA US HY OAS, 30-year mortgage rate.
   One tight line per metric. If a metric isn't in the block, omit it silently. Group with
   short sub-labels ("Labor:", "Inflation:", "Growth:", "Credit:") so the section stays
   scannable. Data only — no editorializing.

4. **Politics** — 4-5 items total, drawn from U.S. national, Canadian federal/Ontario/Quebec, and
   Atlanta/Georgia local news. Prioritize actual policy substance — legislation, regulation,
   court rulings, budget/appropriations, agency actions — over horse-race, campaign, or
   personality-driven political coverage. Straight reporting, no doom, no editorial framing.
   Name the specific development — who, what, when. If fewer than 4 items have genuine, current,
   policy-relevant material, include only what's real rather than padding with vague filler.

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
  Examples: 🌤️ WEATHER · 📊 RATES · 🏛️ POLICY · 📈 ECONOMY · 🗳️ POLITICS · ⚾ SPORTS
            🍳 FOOD · 🎵 CULTURE · ✡️ CALENDAR
- Weather always leads. Follow the Required Every Day order above; rotate the optional
  sections after Sports, and not every optional section appears every day.

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
- Any BLS jobs report or CPI/PCE inflation release from the past 48 hours, including any
  revisions to prior-month nonfarm payrolls
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


_TREASURY_TENORS = [("3-month", "BC_3MONTH"), ("2-year", "BC_2YEAR"),
                     ("7-year", "BC_7YEAR"), ("10-year", "BC_10YEAR")]


def _fetch_curve_xml(yyyymm: str) -> str:
    url = (
        "https://home.treasury.gov/resource-center/data-chart-center/"
        "interest-rates/pages/xml?data=daily_treasury_yield_curve"
        f"&field_tdr_date_value_month={yyyymm}"
    )
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return resp.text


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
        for label, tag in _TREASURY_TENORS:
            val = last_val(tag)
            if val:
                rates.append((label, val, as_of, src))
    except Exception as e:
        print(f"  Warning: Treasury yield curve fetch failed: {e}")

    return rates


def fetch_rate_changes(rates: list) -> dict:
    """Compute 7/30/365-day changes (in percentage points) for each current rate.

    Reuses the current values from fetch_rates() and looks up the closest prior
    value on or before each lookback date. SOFR history comes from the NY Fed's
    bulk endpoint (one call); Treasury history requires one XML fetch per lookback
    month since the feed is paginated by month. Failure-tolerant per tenor/window —
    missing history just omits that line, never raises.

    Returns {label: {7: delta, 30: delta, 365: delta}}, only for values found.
    """
    changes = {}
    now = datetime.now(pytz.timezone("America/New_York"))
    windows = {7: now - timedelta(days=7), 30: now - timedelta(days=30),
               365: now - timedelta(days=365)}
    current = {label: float(val) for label, val, _, _ in rates}

    # SOFR history — one bulk call covers all three lookback windows.
    if "SOFR" in current:
        try:
            r = requests.get(
                "https://markets.newyorkfed.org/api/rates/secured/sofr/last/400.json",
                timeout=15,
            )
            r.raise_for_status()
            hist = sorted(
                (e["effectiveDate"], float(e["percentRate"]))
                for e in r.json()["refRates"]
            )
            deltas = {}
            for days, target in windows.items():
                target_str = target.strftime("%Y-%m-%d")
                past = [v for d, v in hist if d <= target_str]
                if past:
                    deltas[days] = round(current["SOFR"] - past[-1], 2)
            if deltas:
                changes["SOFR"] = deltas
        except Exception as e:
            print(f"  Warning: SOFR history fetch failed: {e}")

    # Treasury tenors — one XML fetch per lookback month (400-day history isn't
    # available in one call like SOFR; the feed is paginated by calendar month).
    tenor_labels = {label for label, _ in _TREASURY_TENORS if label in current}
    if tenor_labels:
        xml_cache = {}
        for days, target in windows.items():
            yyyymm = target.strftime("%Y%m")
            try:
                if yyyymm not in xml_cache:
                    xml_cache[yyyymm] = _fetch_curve_xml(yyyymm)
                xml = xml_cache[yyyymm]
                dates = re.findall(r"<d:NEW_DATE[^>]*>([^<]+)</d:NEW_DATE>", xml)
                target_str = target.strftime("%Y-%m-%d")
                for label, tag in _TREASURY_TENORS:
                    if label not in tenor_labels:
                        continue
                    vals = re.findall(rf"<d:{tag}[^>]*>([^<]+)</d:{tag}>", xml)
                    pairs = [(d[:10], v) for d, v in zip(dates, vals) if d[:10] <= target_str and v]
                    if pairs:
                        changes.setdefault(label, {})[days] = round(
                            current[label] - float(pairs[-1][1]), 2
                        )
            except Exception as e:
                print(f"  Warning: Treasury history fetch failed ({days}d): {e}")

    return changes


def build_rate_trend_chart(rates: list, rate_changes: dict) -> bytes:
    """Render a small line chart of each tenor's value over the last year.

    Reconstructs historical points from the current value and the 7/30/365-day
    deltas (current - delta = past value), so no extra network calls are needed
    beyond what fetch_rate_changes already made. A tenor is only plotted if all
    three lookback windows resolved; skips the chart entirely if nothing qualifies.

    Returns PNG bytes, or None if there's nothing to plot.
    """
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm

    x_labels = ["365d ago", "30d ago", "7d ago", "Today"]
    x = range(len(x_labels))

    # A muted, higher-contrast palette in a deliberate order (short end to long
    # end of the curve) instead of matplotlib's default cycle.
    colors = {
        "SOFR": "#2C7FB8", "3-month": "#41AB5D", "2-year": "#F2A93B",
        "7-year": "#E4572E", "10-year": "#8856A7",
    }
    sans = [f.name for f in fm.fontManager.ttflist]
    font = next((f for f in ("Segoe UI", "Helvetica Neue", "Arial") if f in sans), "DejaVu Sans")
    plt.rcParams["font.family"] = font

    fig, ax = plt.subplots(figsize=(6.4, 2.9), dpi=160)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    plotted = False
    for label, val, _, _ in rates:
        deltas = rate_changes.get(label)
        if not deltas or not all(d in deltas for d in (7, 30, 365)):
            continue
        current = float(val)
        y = [current - deltas[365], current - deltas[30], current - deltas[7], current]
        color = colors.get(label, "#555555")
        ax.plot(x, y, marker="o", markersize=5.5, linewidth=2.4, color=color,
                label=label, solid_capstyle="round", zorder=3,
                markerfacecolor="white", markeredgewidth=1.8, markeredgecolor=color)
        ax.annotate(f"{y[-1]:.2f}%", (x[-1], y[-1]), xytext=(8, 0),
                    textcoords="offset points", va="center", fontsize=9,
                    color=color, fontweight="bold")
        plotted = True

    if not plotted:
        plt.close(fig)
        return None

    ax.set_title("Rate Trend — Past Year", fontsize=11, fontweight="bold",
                  color="#1a1a1a", loc="left", pad=10)
    ax.set_xticks(list(x))
    ax.set_xticklabels(x_labels, fontsize=9.5, color="#444444")
    ax.set_xlim(-0.15, len(x_labels) - 0.15 + 0.55)  # room for value labels
    ax.tick_params(axis="y", labelsize=9.5, colors="#444444")
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.1f}%")

    ax.grid(True, axis="y", color="#dddddd", linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#bbbbbb")

    legend = ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.34), ncol=5,
                        fontsize=9, frameon=False, handlelength=1.4,
                        columnspacing=1.2, handletextpad=0.5)
    for text in legend.get_texts():
        text.set_color("#444444")

    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor="white", bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    return buf.getvalue()


def fetch_indicators() -> list:
    """Fetch macro indicators from FRED. Returns a list of formatted display lines.

    Requires FRED_API_KEY. Fails soft — a missing key or any per-series error just
    omits those lines. Groq gets a pre-formatted "AUTHORITATIVE INDICATORS" block
    so it doesn't invent numbers.

    Series pulled:
      UNRATE       Unemployment rate (U-3), %
      U6RATE       U-6 underemployment, %
      PAYEMS       Nonfarm payrolls, thousands (last 3 obs → MoM changes)
      CES0500000003  Avg hourly earnings, all private, level (last 13 obs → YoY %)
      ICSA         Initial jobless claims, thousands (weekly, latest)
      CPIAUCSL     Headline CPI (last 13 → MoM & YoY)
      CPILFESL     Core CPI (last 13 → MoM & YoY)
      PCEPILFE     Core PCE (last 13 → MoM & YoY)
      GDPNOW       Atlanta Fed GDPNow, %
      BAMLH0A0HYM2 ICE BofA US HY OAS, %
      MORTGAGE30US 30-yr fixed mortgage rate, %
    """
    api_key = os.environ.get("FRED_API_KEY", "").strip()
    if not api_key:
        print("  FRED_API_KEY not set — skipping macro indicators.")
        return []

    FRED_SRC = "https://fred.stlouisfed.org/series/{}"
    # Only include a series if FRED updated it within this many hours. Daily series
    # (HY OAS, mortgage, GDPNow) pass every business day; monthly series (UNRATE,
    # PAYEMS, CPI, PCE) pass only on their release day. "New data only" = the point.
    MAX_AGE_HOURS = 36

    def is_fresh(series_id):
        r = requests.get(
            "https://api.stlouisfed.org/fred/series",
            params={"series_id": series_id, "api_key": api_key, "file_type": "json"},
            timeout=15,
        )
        r.raise_for_status()
        ts = r.json()["seriess"][0]["last_updated"]  # e.g. "2026-07-15 07:31:03-05"
        naive = datetime.strptime(ts[:19], "%Y-%m-%d %H:%M:%S")
        offset_h = int(ts[-3:]) if len(ts) >= 22 and ts[-3:].lstrip("-+").isdigit() else 0
        dt = naive.replace(tzinfo=timezone(timedelta(hours=offset_h)))
        age = datetime.now(timezone.utc) - dt
        return age <= timedelta(hours=MAX_AGE_HOURS)

    def obs(series_id, limit=1):
        url = "https://api.stlouisfed.org/fred/series/observations"
        r = requests.get(url, params={
            "series_id": series_id, "api_key": api_key, "file_type": "json",
            "sort_order": "desc", "limit": limit,
        }, timeout=15)
        r.raise_for_status()
        rows = r.json().get("observations", [])
        out = []
        for row in rows:
            v = row.get("value")
            if v in (None, ".", ""):
                continue
            try:
                out.append((row["date"], float(v)))
            except ValueError:
                continue
        return out  # newest first

    def fresh_obs(series_id, limit=1):
        """obs() gated on freshness. Returns [] silently if the series is stale."""
        if not is_fresh(series_id):
            return []
        return obs(series_id, limit)

    lines = []

    def try_add(fn, label):
        try:
            fn()
        except Exception as e:
            print(f"  Warning: {label} fetch failed: {e}")

    def _simple(series_id, label, fmt):
        rows = fresh_obs(series_id)
        if not rows:
            return
        lines.append((label, fmt.format(rows[0][1]), rows[0][0], FRED_SRC.format(series_id)))

    # Labor
    try_add(lambda: _simple("UNRATE", "Unemployment rate (U-3)", "{:.1f}%"), "UNRATE")
    try_add(lambda: _simple("U6RATE", "U-6 underemployment", "{:.1f}%"), "U6RATE")

    def _payems():
        rows = fresh_obs("PAYEMS", limit=4)  # newest first
        if len(rows) < 4:
            return
        m0, m1, m2, m3 = rows
        val = (f"latest {(m0[1]-m1[1]):+,.0f}k ({m0[0][:7]}); "
               f"prior {(m1[1]-m2[1]):+,.0f}k ({m1[0][:7]}); "
               f"prior-prior {(m2[1]-m3[1]):+,.0f}k ({m2[0][:7]})")
        lines.append(("Nonfarm payrolls MoM", val, m0[0], FRED_SRC.format("PAYEMS")))
    try_add(_payems, "PAYEMS")

    def _ahe():
        rows = fresh_obs("CES0500000003", limit=13)
        if len(rows) < 13:
            return
        yoy = (rows[0][1] / rows[12][1] - 1) * 100
        lines.append(("Avg hourly earnings YoY", f"{yoy:+.1f}%", rows[0][0], FRED_SRC.format("CES0500000003")))
    try_add(_ahe, "AHE YoY")

    def _icsa():
        rows = fresh_obs("ICSA")
        if not rows:
            return
        lines.append(("Initial jobless claims", f"{rows[0][1]/1000:.0f}k", rows[0][0], FRED_SRC.format("ICSA")))
    try_add(_icsa, "ICSA")

    # Inflation — MoM & YoY for each
    def _infl(series_id, label):
        rows = fresh_obs(series_id, limit=13)
        if len(rows) < 13:
            return
        mom = (rows[0][1] / rows[1][1] - 1) * 100
        yoy = (rows[0][1] / rows[12][1] - 1) * 100
        lines.append((label, f"MoM {mom:+.2f}%, YoY {yoy:+.1f}%", rows[0][0], FRED_SRC.format(series_id)))
    try_add(lambda: _infl("CPIAUCSL", "Headline CPI"), "CPI")
    try_add(lambda: _infl("CPILFESL", "Core CPI"), "core CPI")
    try_add(lambda: _infl("PCEPILFE", "Core PCE"), "core PCE")

    # Growth
    try_add(lambda: _simple("GDPNOW", "GDPNow (Atlanta Fed)", "{:+.1f}%"), "GDPNOW")

    # Credit / housing
    try_add(lambda: _simple("BAMLH0A0HYM2", "ICE BofA US HY OAS", "{:.2f}%"), "HY OAS")
    try_add(lambda: _simple("MORTGAGE30US", "30-yr fixed mortgage", "{:.2f}%"), "MORTGAGE30US")

    return lines


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
        {"q": "Federal Reserve FOMC interest rate decision or statement", "days": 1},
        {"q": "BLS employment situation nonfarm payrolls report revision", "days": 3, "cap": 200},
        {"q": "CPI inflation report release BLS", "days": 3, "cap": 200},
        {"q": "PCE inflation report release BEA", "days": 3, "cap": 200},
        {"q": "CDFI Fund New Markets Tax Credit NMTC announcement or Federal Register notice", "days": 21},
        {"q": "Atlanta weather forecast today"},
        {"q": "Braves Blue Jays Atlanta United score result last night", "days": 2},
        {"q": "US federal policy legislation regulation court ruling news", "days": 1, "keep": 4},
        {"q": "Canada federal Ontario Quebec policy legislation news", "days": 1, "keep": 4},
        {"q": "Atlanta Georgia state policy legislation news", "days": 1, "keep": 4},
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
                    "results": data["results"][:spec.get("keep", 3)],  # TPM-bounded
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
    # Trend data is no longer surfaced as text — send_email() attaches a chart instead.

    indicators = fetch_indicators()
    if indicators:
        ind_block = (
            "=== AUTHORITATIVE INDICATORS — use these EXACT figures and source URLs for the "
            "Economy & Credit section; do NOT substitute web-search numbers ===\n"
        )
        for label, val, as_of, url in indicators:
            ind_block += f"- {label}: {val} (as of {as_of}) — source: {url}\n"
        context = ind_block + "\n" + context

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


def _briefing_to_html(message: str, chart_cid: str = None) -> str:
    """Render the plain-text briefing as HTML, turning markdown links into <a> tags.

    If chart_cid is given, an inline rate-trend chart image is inserted right
    after the rates section (the block whose header line mentions "RATE").
    """
    paragraphs = message.strip().split("\n\n")
    blocks = []
    for para in paragraphs:
        html_para = _markdown_links_to_html(para).replace("\n", "<br>\n")
        blocks.append(f"<p>{html_para}</p>")
        first_line = para.split("\n", 1)[0]
        if chart_cid and "RATE" in first_line.upper():
            blocks.append(
                f'<p><img src="cid:{chart_cid}" alt="Rate trend chart" '
                'style="max-width:100%;"></p>'
            )
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
    hyperlinks plus an inline rate-trend chart, and a plain-text fallback
    with "Name (url)" for clients that don't render HTML.

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

    # Rebuild the rate-trend chart for the email. Cheap (a handful of already-
    # cacheable HTTP calls, once a day) and keeps chart-building decoupled from
    # the LLM call in generate_briefing().
    chart_png = None
    try:
        rates = fetch_rates()
        if rates:
            chart_png = build_rate_trend_chart(rates, fetch_rate_changes(rates))
    except Exception as e:
        print(f"  Warning: rate trend chart build failed: {e}")

    chart_cid = "rate-trend-chart" if chart_png else None

    email = EmailMessage()
    email["Subject"] = f"Morning Briefing — {date_str}"
    email["From"] = gmail_address
    email["To"] = recipient
    email.set_content(_markdown_links_to_plain(message))
    email.add_alternative(_briefing_to_html(message, chart_cid), subtype="html")
    if chart_png:
        html_part = email.get_payload()[1]
        html_part.add_related(chart_png, maintype="image", subtype="png", cid=chart_cid)

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


def run_release_alert() -> None:
    """Short 'data release' briefing — fires only when FRED has fresh releases.

    Fetches indicators; exits silently (no email) if none are fresh. Otherwise
    asks Groq for a focused ECONOMY + RATES email — no weather/sports/culture.
    """
    print("Release-alert mode — checking for fresh FRED releases...")
    indicators = fetch_indicators()
    if not indicators:
        print("No fresh economic releases — skipping email.")
        return

    ind_block = ""
    for label, val, as_of, url in indicators:
        ind_block += f"- {label}: {val} (as of {as_of}) — source: {url}\n"

    system = (
        "You write a short 'data release' alert email in Axios Smart Brevity style. "
        "Plain text, no markdown headers. Lead with one punchy takeaway line summarizing "
        "what just printed. Then a tight bullet per fresh indicator using the EXACT figures "
        "and source URLs from the AUTHORITATIVE INDICATORS block below. Cite inline as "
        "markdown links (e.g. [FRED](https://...)). No editorializing, no forecasting. "
        "Group by Labor / Inflation / Growth / Credit sub-labels when more than one item "
        "in a group. Keep the whole email under 200 words."
    )
    user = f"Fresh FRED releases as of now:\n\n{ind_block}\n\nWrite the alert."

    groq_api_key = os.environ.get("GROQ_API_KEY")
    if not groq_api_key:
        raise RuntimeError("GROQ_API_KEY not set")
    client = Groq(api_key=groq_api_key)
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile", max_tokens=1200,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
    )
    body = resp.choices[0].message.content.strip()
    if not body:
        raise RuntimeError("Groq returned empty release alert")

    # Reuse send_email but override the subject
    gmail_address = os.environ.get("GMAIL_ADDRESS", "").strip()
    app_password = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    recipient = os.environ.get("RECIPIENT", "").strip() or gmail_address
    date_str = datetime.now(pytz.timezone("America/New_York")).strftime("%A, %B %-d, %Y")
    email = EmailMessage()
    email["Subject"] = f"Data Release — {date_str}"
    email["From"] = gmail_address
    email["To"] = recipient
    email.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, app_password)
        server.send_message(email)
    print(f"Release alert sent to {recipient}.")


def main():
    atlanta_tz = pytz.timezone("America/New_York")
    now = datetime.now(atlanta_tz)
    print(f"Atlanta time: {now.strftime('%H:%M %Z')}")

    if os.environ.get("BRIEFING_MODE") == "release_alert":
        try:
            run_release_alert()
        except Exception as exc:
            print(f"ERROR in release alert: {exc}", file=sys.stderr)
            sys.exit(1)
        return

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
