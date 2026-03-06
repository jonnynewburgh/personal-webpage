import httpx
from bs4 import BeautifulSoup
from models.schemas import HtmlTableCandidate, UrlProbeResult


async def probe_html_tables(url: str) -> UrlProbeResult:
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        html = resp.text

    soup = BeautifulSoup(html, "lxml")
    raw_tables = soup.find_all("table")

    candidates: list[HtmlTableCandidate] = []
    for i, table in enumerate(raw_tables):
        rows = table.find_all("tr")
        if not rows:
            continue
        # Count cols from first row
        first_cells = rows[0].find_all(["th", "td"])
        cols = len(first_cells)
        if cols == 0:
            continue
        headers = [c.get_text(strip=True)[:40] for c in first_cells]
        candidates.append(
            HtmlTableCandidate(
                index=i,
                rows=len(rows),
                cols=cols,
                headers=headers,
            )
        )

    return UrlProbeResult(
        url=url,
        detected_type="html",
        html_tables=candidates,
    )


async def fetch_html_table(url: str, table_index: int) -> bytes:
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    return resp.content
