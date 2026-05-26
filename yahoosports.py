import asyncio
from datetime import date, timedelta
import os
from pyppeteer import launch
import re
import sys

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

TEAM_URL = 'https://sports.yahoo.com/nba/teams/minnesota/'
DEFAULT_CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
BLOCKED_RESOURCE_TYPES = {'image', 'media', 'font'}
HEADLINE_SELECTOR = "#entity-story-cards a[href] h3, #entity-latest-news a[href]"
GAME_SELECTOR = "#team-schedule [id^='nba.g.']"
GAME_LINK_SELECTOR = "#team-schedule a[href*='/nba/']"


class YahooSportsError(RuntimeError):
    """Raised when Yahoo Sports data cannot be loaded or parsed."""


def normalize_game_summary(game, game_date):
    game = re.sub(r'\s+', ' ', game).replace('View game', '').strip()
    compact = game.replace(' ', '')
    score_match = re.search(r'([A-Z]{2,3})\d+-\d+(\d{2,3})([A-Z]{2,3})\d+-\d+(\d{2,3})', compact)

    if score_match:
        team_one, score_one, team_two, score_two = score_match.groups()
        game = f"{team_one} {score_one} {team_two} {score_two}"

    if "final" not in game.lower():
        game = f"{game} Final {game_date.month}/{game_date.day}"

    return game


async def intercept_request(req):
    resource_type = req.resourceType

    if resource_type in BLOCKED_RESOURCE_TYPES:
        await req.abort()
    else:
        await req.continue_()


async def get_first_non_empty_text(page, selector, description):
    try:
        await page.waitForSelector(selector, {'timeout': 15000})
        text = await page.evaluate(
            """selector => {
                const normalize = text => (text || '').replace(/\\s+/g, ' ').trim();
                const nodes = Array.from(document.querySelectorAll(selector));
                const node = nodes.find(el => normalize(el.innerText || el.textContent));
                return node ? normalize(node.innerText || node.textContent) : '';
            }""",
            selector
        )
    except Exception as exc:
        raise YahooSportsError(f"Could not find {description}. Yahoo may have changed the page layout.") from exc

    if not text:
        raise YahooSportsError(f"Found {description}, but it was empty.")

    return text


async def find_latest_game_summary(page, max_days_back=200):
    current_date = date.today()
    await page.waitForSelector(GAME_SELECTOR, {'timeout': 15000})

    for i in range(max_days_back):
        d = current_date - timedelta(days=i)
        month = d.strftime("%m")
        day = d.strftime("%d")
        year = d.strftime("%Y")
        game_id = f"{year}{month}{day}"
        game = await page.evaluate(
            """({ linkSelector, gameId }) => {
                const normalize = text => (text || '').replace(/\\s+/g, ' ').trim();
                const links = Array.from(document.querySelectorAll(linkSelector));
                const link = links.find(el => el.href && el.href.includes(gameId));
                return link ? normalize(link.innerText || link.textContent) : '';
            }""",
            {'linkSelector': GAME_LINK_SELECTOR, 'gameId': game_id}
        )

        if game:
            return normalize_game_summary(game, d), d

    raise YahooSportsError(f"Could not find a completed Timberwolves game in the last {max_days_back} days.")


async def getGame(headless=False, chrome_path=None, max_days_back=200):
    chrome_path = chrome_path or os.getenv('CHROME_PATH') or DEFAULT_CHROME_PATH
    browser = await launch(
        headless=headless,
        executablePath=chrome_path,
        args=['--window-size=1600,900', '--no-sandbox', '--disable-setuid-sandbox'],
        defaultViewport=None
    )

    try:
        page = await browser.newPage()
        await page.setRequestInterception(True)
        page.on('request', lambda req: asyncio.ensure_future(intercept_request(req)))

        await page.goto(TEAM_URL, {'waitUntil': 'domcontentloaded', 'timeout': 30000})
        headline = await get_first_non_empty_text(page, HEADLINE_SELECTOR, "top Timberwolves headline")

        game, game_date = await find_latest_game_summary(page, max_days_back)
        game_summary = [game]

        if not game_summary:
            raise YahooSportsError(f"Found a game for {game_date:%Y-%m-%d}, but its summary was empty.")

        return headline, game_summary
    finally:
        await browser.close()
