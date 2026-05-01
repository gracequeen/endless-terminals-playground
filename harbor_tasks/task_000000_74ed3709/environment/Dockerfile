FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/home/user

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    curl \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libx11-xcb1 \
    libxcb1 \
    libxcursor1 \
    libxi6 \
    libxtst6 \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest pyppeteer

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN useradd -m -d /home/user -s /bin/bash user

RUN mkdir -p /home/user/scraper && chmod 0777 /home/user/scraper
RUN mkdir -p /home/user/testsite && chmod 0755 /home/user/testsite

RUN cat > /home/user/testsite/products.html << 'HTMLEOF'
<!DOCTYPE html>
<html>
<head>
    <title>Product Listing</title>
</head>
<body>
    <h1>Products</h1>
    <div class="product">
        <span class="name">Widget A</span>
        <span class="price">$19.99</span>
    </div>
    <div class="product">
        <span class="name">Widget B</span>
        <span class="price">$24.99</span>
    </div>
    <div class="product">
        <span class="name">Gadget Pro</span>
        <span class="price">$149.99</span>
    </div>
    <div class="product">
        <span class="name">Super Gizmo</span>
        <span class="price">$79.50</span>
    </div>
    <div class="product">
        <span class="name">Mega Device</span>
        <span class="price">$299.00</span>
    </div>
</body>
</html>
HTMLEOF

RUN cat > /home/user/testsite/server.py << 'PYEOF'
#!/usr/bin/env python3
import http.server
import socketserver
import os
import datetime

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/home/user/testsite", **kwargs)

    def do_GET(self):
        # Log access
        with open("/home/user/testsite/access.log", "a") as f:
            f.write(f"{datetime.datetime.now().isoformat()} GET {self.path}\n")

        # Route /products to products.html
        if self.path == "/products":
            self.path = "/products.html"

        return super().do_GET()

    def log_message(self, format, *args):
        pass  # Suppress console output

if __name__ == "__main__":
    PORT = 8080
    with socketserver.TCPServer(("", PORT), CustomHandler) as httpd:
        httpd.serve_forever()
PYEOF

RUN chmod +x /home/user/testsite/server.py

RUN cat > /home/user/scraper/scrape.py << 'SCRAPEEOF'
#!/usr/bin/env python3
import asyncio
import json
import os
from pyppeteer import launch

async def scrape_prices():
    browser = await launch(
        headless=False,
        args=['--no-sandbox']
    )

    page = await browser.newPage()
    await page.goto('http://localhost:8080/products')

    await page.waitForSelector('.product', timeout=5000)

    products = await page.evaluate('''() => {
        const items = document.querySelectorAll('.product');
        return Array.from(items).map(item => ({
            name: item.querySelector('.name').textContent,
            price: item.querySelector('.price').textContent
        }));
    }''')

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'prices.json')

    with open(output_path, 'w') as f:
        json.dump(products, f, indent=2)

    await browser.close()
    print(f"Scraped {len(products)} products to {output_path}")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(scrape_prices())
SCRAPEEOF

RUN chmod +x /home/user/scraper/scrape.py

RUN touch /home/user/testsite/access.log && chmod 0666 /home/user/testsite/access.log

RUN mkdir -p /home/user/.local/share/pyppeteer && \
    chown -R user:user /home/user/.local

USER user
WORKDIR /home/user

RUN python3 -c "from pyppeteer import chromium_downloader; chromium_downloader.download_chromium()"

USER root

RUN chown -R user:user /home/user

RUN cat > /entrypoint.sh << 'ENTRYEOF'
#!/bin/bash

# Mount a tiny /dev/shm to simulate the IoT device problem
if mount | grep -q '/dev/shm'; then
    umount /dev/shm 2>/dev/null || true
fi
mount -t tmpfs -o size=1M tmpfs /dev/shm 2>/dev/null || true

# Start the test server as user
su - user -c "cd /home/user/testsite && python3 server.py &"

# Wait for server to be ready
sleep 2

# Execute the provided command or start bash
exec "$@"
ENTRYEOF

RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["su", "-", "user"]
