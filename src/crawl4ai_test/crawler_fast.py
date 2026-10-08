import asyncio
import os
import psutil
import requests

from pathlib import Path
from typing import List
from urllib.parse import urlparse

from xml.etree import ElementTree

from crawl4ai import (
    AsyncWebCrawler,
    BrowserConfig,
    CrawlerRunConfig,
    CacheMode,
)


# ============================================================
# CONFIGURATION
# ============================================================

SITEMAP_URL = "https://pharox3d.com/sitemap.xml"

MAX_CONCURRENT = 10

PROJECT_ROOT = Path.cwd()

OUTPUT_DIR = PROJECT_ROOT / "output"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


NAMESPACE = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9"
}


# ============================================================
# URL / FILENAME HELPERS
# ============================================================

def create_filename(url: str, index: int) -> str:
    """
    Convert a URL into a safe Markdown filename.
    """

    parsed = urlparse(url)

    path = parsed.path.strip("/")

    if not path:
        name = "home"
    else:
        name = path.replace("/", "_")

    # Remove unsafe filename characters
    safe_name = "".join(
        character
        if character.isalnum() or character in "-_"
        else "_"
        for character in name
    )

    return f"{index:04d}_{safe_name}.md"


# ============================================================
# SITEMAP PARSER
# ============================================================

def fetch_xml(url: str):
    """
    Download an XML document.
    """

    response = requests.get(
        url,
        timeout=30,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(X11; Linux x86_64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/154.0 Safari/537.36"
            )
        },
    )

    response.raise_for_status()

    return ElementTree.fromstring(
        response.content
    )


def parse_sitemap(sitemap_url: str) -> List[str]:
    """
    Recursively parse a sitemap or sitemap index.

    Returns actual webpage URLs.
    """

    print(
        f"🗺️ Reading sitemap: {sitemap_url}"
    )

    root = fetch_xml(
        sitemap_url
    )

    # --------------------------------------------------------
    # Check whether this is a sitemap index
    # --------------------------------------------------------

    child_sitemaps = root.findall(
        "sm:sitemap/sm:loc",
        NAMESPACE,
    )

    if child_sitemaps:

        print(
            f"   📚 Found {len(child_sitemaps)} child sitemaps"
        )

        all_urls = []

        for sitemap in child_sitemaps:

            child_url = sitemap.text

            if not child_url:
                continue

            child_urls = parse_sitemap(
                child_url
            )

            all_urls.extend(
                child_urls
            )

        return all_urls

    # --------------------------------------------------------
    # Otherwise this is an actual URL sitemap
    # --------------------------------------------------------

    page_urls = root.findall(
        "sm:url/sm:loc",
        NAMESPACE,
    )

    urls = [
        url.text
        for url in page_urls
        if url.text
    ]

    print(
        f"   🔗 Found {len(urls)} actual URLs"
    )

    return urls


def get_pharox3d_urls() -> List[str]:
    """
    Get all actual Pharox3D webpage URLs
    from the sitemap hierarchy.
    """

    print(
        "\n========================================"
    )

    print(
        "🗺️ PHAROX3D SITEMAP DISCOVERY"
    )

    print(
        "========================================\n"
    )

    urls = parse_sitemap(
        SITEMAP_URL
    )

    # --------------------------------------------------------
    # Keep only Pharox3D URLs
    # --------------------------------------------------------

    urls = [
        url
        for url in urls
        if url.startswith(
            "https://pharox3d.com/"
        )
    ]

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    urls = list(
        dict.fromkeys(urls)
    )

    print(
        "\n========================================"
    )

    print(
        f"🌐 TOTAL URLs FOUND: {len(urls)}"
    )

    print(
        "========================================\n"
    )

    return urls


# ============================================================
# MEMORY MONITOR
# ============================================================

class MemoryMonitor:

    def __init__(self):

        self.process = psutil.Process(
            os.getpid()
        )

        self.peak = 0

    def log(self, prefix=""):

        current = (
            self.process
            .memory_info()
            .rss
        )

        if current > self.peak:

            self.peak = current

        current_mb = (
            current
            // (1024 * 1024)
        )

        peak_mb = (
            self.peak
            // (1024 * 1024)
        )

        print(
            f"{prefix}"
            f"Memory: {current_mb} MB | "
            f"Peak: {peak_mb} MB"
        )


# ============================================================
# CRAWLER
# ============================================================

async def crawl_parallel(
    urls: List[str],
    max_concurrent: int = MAX_CONCURRENT,
):

    print(
        "\n========================================"
    )

    print(
        "🕷️ PHAROX3D CRAWLER"
    )

    print(
        "========================================"
    )

    print(
        f"📄 URLs to crawl: {len(urls)}"
    )

    print(
        f"⚡ Concurrency: {max_concurrent}"
    )

    print(
        f"📁 Output: {OUTPUT_DIR}"
    )

    print()

    memory = MemoryMonitor()

    # --------------------------------------------------------
    # Browser configuration
    # --------------------------------------------------------

    browser_config = BrowserConfig(

        headless=True,

        verbose=False,

        extra_args=[
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--no-sandbox",
        ],
    )

    # --------------------------------------------------------
    # Crawl configuration
    # --------------------------------------------------------

    crawl_config = CrawlerRunConfig(

        cache_mode=CacheMode.BYPASS,
    )

    # --------------------------------------------------------
    # Start crawler
    # --------------------------------------------------------

    crawler = AsyncWebCrawler(
        config=browser_config
    )

    await crawler.start()

    success_count = 0

    failed_count = 0

    try:

        # ----------------------------------------------------
        # Process URLs in batches
        # ----------------------------------------------------

        for start in range(
            0,
            len(urls),
            max_concurrent,
        ):

            batch = urls[
                start:
                start + max_concurrent
            ]

            batch_number = (
                start // max_concurrent
            ) + 1

            print(
                "\n----------------------------------------"
            )

            print(
                f"📦 Batch {batch_number}"
            )

            print(
                f"URLs: {len(batch)}"
            )

            print(
                "----------------------------------------"
            )

            memory.log(
                "Before: "
            )

            # ------------------------------------------------
            # Create crawl tasks
            # ------------------------------------------------

            tasks = []

            for index, url in enumerate(
                batch
            ):

                session_id = (
                    f"pharox3d_{start + index}"
                )

                task = crawler.arun(

                    url=url,

                    config=crawl_config,

                    session_id=session_id,
                )

                tasks.append(
                    task
                )

            # ------------------------------------------------
            # Run batch
            # ------------------------------------------------

            results = await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )

            memory.log(
                "After: "
            )

            # ------------------------------------------------
            # Process results
            # ------------------------------------------------

            for local_index, result in enumerate(
                results
            ):

                url = batch[
                    local_index
                ]

                global_index = (
                    start + local_index
                )

                # --------------------------------------------
                # Exception
                # --------------------------------------------

                if isinstance(
                    result,
                    Exception,
                ):

                    print(
                        f"❌ {url}"
                    )

                    print(
                        f"   Error: {result}"
                    )

                    failed_count += 1

                    continue

                # --------------------------------------------
                # Crawl failed
                # --------------------------------------------

                if not result.success:

                    print(
                        f"❌ {url}"
                    )

                    if hasattr(
                        result,
                        "error_message",
                    ):

                        print(
                            f"   Error: "
                            f"{result.error_message}"
                        )

                    failed_count += 1

                    continue

                # --------------------------------------------
                # Crawl successful
                # --------------------------------------------

                filename = create_filename(
                    url,
                    global_index,
                )

                output_path = (
                    OUTPUT_DIR
                    / filename
                )

                # --------------------------------------------
                # Save Markdown
                # --------------------------------------------

                output_path.write_text(
                    result.markdown,
                    encoding="utf-8",
                )

                success_count += 1

                print(
                    f"✅ {url}"
                )

                print(
                    f"   💾 {output_path.name}"
                )

    finally:

        print(
            "\n🧹 Closing crawler..."
        )

        await crawler.close()

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    memory.log(
        "Final: "
    )

    print(
        "\n========================================"
    )

    print(
        "📊 CRAWL SUMMARY"
    )

    print(
        "========================================"
    )

    print(
        f"🌐 Total URLs: {len(urls)}"
    )

    print(
        f"✅ Successfully crawled: {success_count}"
    )

    print(
        f"❌ Failed: {failed_count}"
    )

    print(
        f"💾 Markdown directory: {OUTPUT_DIR}"
    )

    print(
        f"🧠 Peak memory: "
        f"{memory.peak // (1024 * 1024)} MB"
    )

    print(
        "========================================"
    )


# ============================================================
# MAIN
# ============================================================

async def main():

    urls = get_pharox3d_urls()

    if not urls:

        print(
            "❌ No URLs found."
        )

        return

    # --------------------------------------------------------
    # Show first URLs before crawling
    # --------------------------------------------------------

    print(
        "\n🔎 First 10 URLs:"
    )

    for url in urls[:10]:

        print(
            f"   {url}"
        )

    print()

    # --------------------------------------------------------
    # Start crawling
    # --------------------------------------------------------

    await crawl_parallel(
        urls,
        max_concurrent=MAX_CONCURRENT,
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    asyncio.run(
        main()
    )