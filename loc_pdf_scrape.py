import os
import time
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# === CONFIGURATION ===
BASE_URL = "https://www.loc.gov/acq/devpol/"
PDF_FOLDER = "pdfs"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# === Create output folder ===
os.makedirs(PDF_FOLDER, exist_ok=True)

# === Initialize crawling ===
visited_pages = set()
pdf_links = set()
html_queue = [BASE_URL]

# === Crawl HTML pages ===
while html_queue:
    current_url = html_queue.pop(0)
    if current_url in visited_pages:
        continue

    print(f"🌐 Visiting: {current_url}")
    visited_pages.add(current_url)

    try:
        response = requests.get(current_url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"❌ Failed to fetch {current_url}: {e}")
        continue

    soup = BeautifulSoup(response.text, "html.parser")

    for a in soup.find_all("a", href=True):
        href = a["href"]
        absolute_url = urljoin(current_url, href)
        parsed = urlparse(absolute_url)

        # Skip non-loc.gov links
        if "loc.gov" not in parsed.netloc:
            continue

        # Only crawl inside /acq/devpol/
        if not parsed.path.startswith("/acq/devpol/"):
            continue

        # Queue .html pages for further crawling
        if parsed.path.endswith(".html") and absolute_url not in visited_pages:
            html_queue.append(absolute_url)

        # Collect .pdf links
        if parsed.path.endswith(".pdf"):
            pdf_links.add(absolute_url)

    time.sleep(1)  # be polite

# === Download all PDFs ===
print(f"\n📄 Found {len(pdf_links)} PDF files.")
for pdf_url in sorted(pdf_links):
    filename = os.path.basename(urlparse(pdf_url).path)
    filepath = os.path.join(PDF_FOLDER, filename)

    if os.path.exists(filepath):
        print(f"✅ Already downloaded: {filename}")
        continue

    print(f"⬇️ Downloading: {filename}")
    try:
        with requests.get(pdf_url, headers=HEADERS, stream=True, timeout=15) as r:
            r.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        print(f"✅ Saved to: {filepath}")
    except Exception as e:
        print(f"❌ Failed to download {pdf_url}: {e}")

print("\n🏁 Done!")
