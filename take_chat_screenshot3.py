import asyncio
import sys
sys.path.append('scraper')
from tools.browser_manager import start_browser, close_browser

async def main():
    context = await start_browser()
    page = context.pages[0]
    
    try:
        await page.goto("https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/o-p-o-r-t-u-n-i-d-a-d-e-sobrado-jardim-oriente-venda-1525441605", timeout=60000)
    except Exception as e:
        print("Timeout nav, continuing anyway...")
    await page.wait_for_timeout(3000)
    
    btn = page.locator('button:has-text("Chat")').first
    if await btn.is_visible():
        print("Chat button found. Clicking...")
        async with context.expect_page(timeout=5000) as new_page_info:
            await btn.click()
        try:
            new_page = await new_page_info.value
            print("Opened in new tab!")
            await new_page.wait_for_timeout(3000)
            print("Textareas on new tab:", await new_page.locator("textarea").count())
            await new_page.screenshot(path="chat_new_tab.png")
        except Exception:
            print("No new tab opened.")
            print("Textareas on same page:", await page.locator("textarea").count())
            await page.screenshot(path="chat_same_page.png")
    else:
        print("Chat button NOT found.")
        await page.screenshot(path="chat_button_not_found.png")
        
    await close_browser()

asyncio.run(main())
