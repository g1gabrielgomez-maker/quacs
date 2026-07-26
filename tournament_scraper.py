import asyncio
import os
import requests
from playwright.async_api import async_playwright

# Configuration
BASE44_API_URL = os.getenv("BASE44_API_URL", "https://your-base44-app.base44.app/api/tournaments")
BASE44_API_KEY = os.getenv("BASE44_API_KEY", "your_api_key_here")

# Target club portals or tournament aggregators in DR
TARGET_URLS = [
    {"region": "Santo Domingo", "url": "https://example-dr-padel-portal.com/santodomingo"},
    {"region": "Punta Cana", "url": "https://example-dr-padel-portal.com/puntacana"},
    {"region": "Santiago", "url": "https://example-dr-padel-portal.com/santiago"},
]

async def scrape_padel_tournaments():
    tournaments_found = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        for target in TARGET_URLS:
            print(f"🔍 Scraping tournaments for {target['region']}...")
            try:
                await page.goto(target["url"], timeout=30000)
                await page.wait_for_selector(".event-card", timeout=10000)

                # Extract event cards from the portal page
                cards = await page.query_selector_all(".event-card")
                for card in cards:
                    title_elem = await card.query_selector(".event-title")
                    venue_elem = await card.query_selector(".venue-name")
                    date_elem = await card.query_selector(".event-date")
                    image_elem = await card.query_selector("img")

                    title = await title_elem.inner_text() if title_elem else "Torneo de Pádel"
                    venue = await venue_elem.inner_text() if venue_elem else "Club de Pádel"
                    date = await date_elem.inner_text() if date_elem else "Por confirmar"
                    cover_image = await image_elem.get_attribute("src") if image_elem else ""

                    tournament_data = {
                        "Title": title.strip(),
                        "VenueName": venue.strip(),
                        "Region": target["region"],
                        "Date": date.strip(),
                        "Status": "Upcoming",
                        "CoverImage": cover_image,
                        "GoalAmount": 2000, # Default target USD for social foundation
                        "CurrentAmountRaised": 0,
                        "Source": "Automated Scraper"
                    }
                    tournaments_found.append(tournament_data)

            except Exception as e:
                print(f"⚠️ Error scraping {target['region']}: {e}")

        await browser.close()
    
    return tournaments_found

def push_to_base44(tournaments):
    """Sends scraped tournaments to Base44 REST API database."""
    headers = {
        "Authorization": f"Bearer {BASE44_API_KEY}",
        "Content-Type": "application/json"
    }

    for tournament in tournaments:
        print(f"🚀 Syncing to Base44: {tournament['Title']} ({tournament['VenueName']})")
        response = requests.post(BASE44_API_URL, json=tournament, headers=headers)
        if response.status_code in [200, 201]:
            print(" ✅ Successfully saved.")
        else:
            print(f" ❌ Failed to save: {response.status_code} - {response.text}")

if __name__ == "__main__":
    scraped_data = asyncio.run(scrape_padel_tournaments())
    if scraped_data:
        push_to_base44(scraped_data)