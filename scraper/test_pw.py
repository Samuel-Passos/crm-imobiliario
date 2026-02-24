import asyncio
from playwright.async_api import async_playwright
import tempfile
import shutil
from pathlib import Path
import os

CHROME_PROFILE_PATH = os.getenv('CHROME_PROFILE_PATH', '/home/samuel/.config/google-chrome')

def setup_temp_profile(user_data_dir: str, profile_dir: str = 'Default') -> str:
    temp_dir = tempfile.mkdtemp(prefix='playwright-profile-tmp-')
    path_original_user_data = Path(user_data_dir)
    path_original_profile = path_original_user_data / profile_dir
    path_temp_profile = Path(temp_dir) / profile_dir

    if path_original_profile.exists():
        shutil.copytree(path_original_profile, path_temp_profile)
        local_state_src = path_original_user_data / 'Local State'
        local_state_dst = Path(temp_dir) / 'Local State'
        if local_state_src.exists():
            shutil.copy(local_state_src, local_state_dst)
    return temp_dir

async def main():
    temp_profile_dir = setup_temp_profile(CHROME_PROFILE_PATH)
    try:
        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=temp_profile_dir,
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-extensions',
                ]
            )
            page = await context.new_page()
            print("Page created. Navigating...")
            await page.goto("https://sp.olx.com.br/vale-do-paraiba-e-litoral-norte/imoveis/linda-casa-condominio-terra-nova-sao-jose-dos-campos-sp-r-610-000-1479566282", timeout=15000)
            print("Navigated successfully. Title:", await page.title())
            await context.close()
    finally:
        shutil.rmtree(temp_profile_dir, ignore_errors=True)

asyncio.run(main())
