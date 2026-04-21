# Camoufox Harness — Quick Examples

Common automation patterns and workflows.

## Web Scraping

### Extract links from page

```python
await goto("https://news.ycombinator.com")
await wait_for_load()

links = json.loads(await js("""
  Array.from(document.querySelectorAll('a')).map(a => ({
    text: a.innerText.trim(),
    href: a.href
  })).filter(l => l.text && l.href)
"""))
```

### Extract structured data

```python
await goto("https://example.com/products")
await wait_for_load()
await wait(2)  # Wait for dynamic content

products = json.loads(await js("""
  Array.from(document.querySelectorAll('.product-card')).map(card => {
    const title = card.querySelector('.title')?.innerText.trim()
    const price = card.querySelector('.price')?.innerText.trim()
    const link = card.querySelector('a')?.href
    return { title, price, link }
  })
"""))
```

### Pagination

```python
all_items = []

for page in range(1, 6):
    await goto(f"https://example.com/page/{page}")
    await wait_for_load()
    await wait(1)

    items = json.loads(await js("/* extraction code */"))
    all_items.extend(items)

print(f"Total: {len(all_items)} items")
```

## Form Automation

### Login flow

```python
await goto("https://example.com/login")
await wait_for_load()

await type_text("#email", "user@example.com")
await type_text("#password", "secret123")
await click("#login-button")
await wait_for_load()

# Verify login
info = await page_info()
assert "dashboard" in info["url"].lower()
```

### Multi-step form

```python
await goto("https://example.com/register")

# Step 1
await type_text("#username", "myuser")
await click("#next-button")
await wait(0.5)

# Step 2
await type_text("#email", "user@example.com")
await click("#next-button")
await wait(0.5)

# Step 3
await type_text("#password", "secret")
await click("#submit-button")
await wait_for_load()
```

### File upload

```python
await goto("https://example.com/upload")

# Use Playwright's set_input_files
await _page.locator("#file-input").set_input_files("/path/to/file.pdf")
await click("#upload-button")
await wait_for_load()
```

## E-commerce

### Price monitoring

```python
await goto("https://www.amazon.com/dp/B08X6Y4NK3")
await wait_for_load()
await wait(2)

price = await js("""
  document.querySelector('.price')?.innerText.replace(/[^\\d]/g, '')
""")

print(f"Current price: {price}")
```

### Product search

```python
await goto("https://www.ozon.ru/search/?text=ноутбук")
await wait_for_load()
await wait(2)

# Scroll to load more
await scroll("down", 800)
await wait(0.5)
await scroll("down", 800)
await wait(1)

products = json.loads(await js("""
  Array.from(document.querySelectorAll('[class*="tile-root"]')).map(tile => {
    const link = tile.querySelector('a[href*="/product/"]')
    const price = tile.innerText.match(/(\\d[\\d\\s]*)\\s*₽/)
    return {
      title: tile.querySelector('span')?.innerText,
      price: price ? price[1].replace(/\\s/g, '') : '',
      url: link ? link.href : ''
    }
  })
"""))
```

### Stock checking

```python
async def check_stock(url):
    await goto(url)
    await wait_for_load()

    in_stock = await js("""
      !/нет в наличии/i.test(document.body.innerText)
    """)

    return {"url": url, "in_stock": in_stock}

urls = ["https://example.com/item1", "https://example.com/item2"]
results = [await check_stock(u) for u in urls]
```

## Testing

### Click journey

```python
await goto("https://example.com")

# Navigation
await click("nav a[href='/products']")
await wait_for_load()

# Filter
await click("#filter-price-low")
await wait(0.5)

# Select item
await click(".product-card:first-child a")
await wait_for_load()

# Verify
assert "product-detail" in await _page.url()
```

### Form validation

```python
await goto("https://example.com/register")

# Test empty submit
await click("#submit-button")
await wait(0.5)

# Check for error
error = await js("""
  document.querySelector('.error-message')?.innerText
""")

assert error == "Email is required"
```

### Screenshot testing

```python
await goto("https://example.com")

# Take full page screenshot
await screenshot("/tmp/full.png", full=True)

# Take viewport screenshot
await screenshot("/tmp/viewport.png")

# Compare with reference
import hashlib
current = hashlib.md5(Path("/tmp/viewport.png").read_bytes()).hexdigest()
reference = "..."  # Load from file
assert current == reference
```

## Data Export

### Save to JSON

```python
await goto("https://example.com/data")
data = json.loads(await js("/* extraction */"))

import json
from datetime import datetime

output = {
    "timestamp": datetime.now().isoformat(),
    "url": await _page.url,
    "data": data
}

with open("output.json", "w") as f:
    json.dump(output, f, indent=2)
```

### Save to CSV

```python
import csv

products = json.loads(await js("/* extraction */"))

with open("products.csv", "w") as f:
    writer = csv.DictWriter(f, fieldnames=["title", "price", "url"])
    writer.writeheader()
    writer.writerows(products)
```

### Append to database

```python
import sqlite3

items = json.loads(await js("/* extraction */"))

conn = sqlite3.connect("data.db")
cursor = conn.cursor()

for item in items:
    cursor.execute(
        "INSERT INTO products (title, price, url) VALUES (?, ?, ?)",
        (item["title"], item["price"], item["url"])
    )

conn.commit()
conn.close()
```

## Advanced Patterns

### Retry on failure

```python
async def robust_goto(url, max_retries=3):
    for i in range(max_retries):
        try:
            await goto(url)
            await wait_for_load()
            return True
        except Exception as e:
            if i == max_retries - 1:
                raise
            await wait(2 ** i)  # Exponential backoff
    return False
```

### Parallel page processing

```python
import asyncio

urls = ["https://example.com/page1", "https://example.com/page2"]

async def process_url(url):
    await goto(url)
    await wait_for_load()
    return await js("document.title")

results = await asyncio.gather(*[process_url(u) for u in urls])
```

### Custom selectors with fallback

```python
async def smart_click(selectors):
    """Try multiple selectors until one works."""
    for selector in selectors:
        try:
            await click(selector)
            return True
        except:
            continue
    return False

# Try multiple possible selectors
await smart_click(["#submit", ".submit-button", "button[type='submit']"])
```

### Conditional waiting

```python
await goto("https://example.com")

# Wait for specific element
await _page.wait_for_selector(".loaded-content", timeout=5000)

# Or wait for condition
await _page.wait_for_function("() => document.title.includes('Loaded')")
```

## Anti-Detection Patterns

### Human-like navigation

```python
# Random delays between actions
await goto("https://example.com")
await random_delay(1, 3)

await click("#link")
await random_delay(0.5, 1.5)

await type_text("#input", "text")
await random_delay(0.3, 0.8)
```

### Mouse movement simulation

```python
# Use built-in humanize (enabled by default)
await human_click("#button")  # Adds random delays
await human_type("#input", "text")  # Types with variation
```

### Viewport variation

```python
# Change viewport size between requests
sizes = [(1920, 1080), (1366, 768), (1440, 900)]
import random

width, height = random.choice(sizes)
await _page.set_viewport_size({"width": width, "height": height})
```

## Debugging

### Capture errors

```python
try:
    await goto("https://example.com")
    await click("#button")
except Exception as e:
    # Screenshot for debugging
    await screenshot(f"/tmp/error_{datetime.now().strftime('%H%M%S')}.png")

    # Check events
    events = await drain_events()
    errors = [e for e in events if e["type"] == "error"]

    print(f"Errors: {errors}")
    raise
```

### Page state dump

```python
# Dump all info
info = await page_info()
html = await get_html()
text = await get_text()
cookies = await get_cookies()

debug = {
    "page": info,
    "html_length": len(html),
    "text_length": len(text),
    "cookies": len(cookies),
    "url": info["url"]
}

print(json.dumps(debug, indent=2))
```

### Event monitoring

```python
# Monitor for dialogs
await goto("https://example.com")

# Trigger action
await click("#button")

# Check for dialog
events = await drain_events()
dialogs = [e for e in events if e["type"] == "dialog"]

if dialogs:
    print(f"Dialog appeared: {dialogs[0]['message']}")
```
