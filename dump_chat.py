import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(executable_path="/usr/bin/chromium", headless=True)
        # using the session because chat requires login
        context = await browser.new_context(storage_state="../scraper/olx_session.json")
        page = await context.new_page()
        await page.goto("https://chat.olx.com.br/?list-id=1527823856", wait_until="networkidle")
        await asyncio.sleep(5)
        html = await page.content()
        with open("chat_dump.html", "w") as f:
            f.write(html)
        await browser.close()
        
asyncio.run(main())
