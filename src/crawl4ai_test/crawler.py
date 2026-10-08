import asyncio

from crawl4ai import AsyncWebCrawler


URL = "https://pharox3d.com/"


async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(URL)

        if result.success:
            print("✅ Crawl successful!")
            print(f"URL: {result.url}")
            print()
            print(result.markdown[:5000])
        else:
            print("❌ Crawl failed!")
            print(result.error_message)


if __name__ == "__main__":
    asyncio.run(main())