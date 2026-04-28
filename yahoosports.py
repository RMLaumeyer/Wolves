import asyncio
from datetime import date, timedelta
from pyppeteer import launch
import sys

if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def intercept_request(req):
    resource_type = req.resourceType

    if resource_type in ['image', 'media', 'font']:
        await req.abort()
    else:
        await req.continue_()

async def getGame():
    browser = await launch(
        headless=False,
        executablePath=r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        args=['--window-size=1600,900'],
        defaultViewport=None
    )

    page = await browser.newPage()
    await page.setRequestInterception(True)
    page.on('request', lambda req: asyncio.ensure_future(intercept_request(req)))

    await page.goto('https://sports.yahoo.com/nba/teams/minnesota/')

    #._ys_1x3jodo > li:nth-of-type(1) -> with journal and time no splice though
    headline = await page.querySelectorEval("._ys_1lhqvo9 li:nth-of-type(1) ._ys_1ftqhsw", "el => el.textContent")
    print(headline)

    #._ys_1rml24t ._ys_zxgo4o:nth-of-type(2) ._ys_1dbz5fh
    await asyncio.sleep(3)
    await asyncio.gather(
        page.waitForNavigation(),
        page.click("a#TEAM_SCHEDULE")
    )
  
    
    #[role] ._ys_1ensitm:nth-of-type(2)
    await asyncio.sleep(3)
    await asyncio.gather(
        page.waitForNavigation(),
        page.click("[role] ._ys_1w3oe7v:nth-of-type(2)")
    )
    
    await asyncio.sleep(3)
    #div:nth-of-type(1) > ._ys_l5y8fj
    await page.waitForSelector("div:nth-of-type(1) > ._ys_l5y8fj")
    await page.click("div:nth-of-type(1) > ._ys_l5y8fj")
    print("done click")




    #at list 
    current_date = date.today()
    await asyncio.sleep(2)
    for i in range(200):
        d = current_date - timedelta(days=i)

        month = d.strftime("%m")
        day = d.strftime("%d")
        year = d.strftime("%Y")

        prevGame = await page.querySelector(f"[id='nba\\.g\\.{year}{month}{day}07']")

        if prevGame:
            break
            

    print(month, day, year)

    game = await page.querySelectorEval(f"[id='nba\\.g\\.{year}{month}{day}07']", "el => el.innerText")

    gameSum = game.split("\n")
    print(gameSum)

    


    await browser.close()

    return headline, gameSum