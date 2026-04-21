# Ozon Domain Skills

> **Product search, analysis, and scam detection for Ozon.ru marketplace**

Field-tested against ozon.ru using camoufox-harness (Playwright async API + Camoufox anti-detect).

## Quick Start

```python
# Search products
await goto("https://www.ozon.ru/search/?text=ноутбук+ASUS&from_global=true")
await wait_for_load()
await wait(2)

# Extract product cards
products = json.loads(await js("/* see search.md */"))
print(f"Found {len(products)} products")

# Analyze specific product
await goto(products[0]['url'])
await wait_for_load()
await wait(2)

product_data = json.loads(await js("/* see product-analysis.md */"))
print(f"{product_data['title']} — {product_data['price']}₽")
```

## Skills

| Skill | Description |
|-------|-------------|
| **[search.md](search.md)** | Product search, extract listings, filter results |
| **[product-analysis.md](product-analysis.md)** | Parse product page: specs, price, seller, variants |
| **[scam-detection.md](scam-detection.md)** | Detect fraud patterns, calculate trust score |

## Authentication (Recommended)

Ozon may block anonymous browsers. Authenticate once:

```bash
# Set profile name for persistent session
CH_NAME=ozon uv run run.py <<'PY'
await goto("https://www.ozon.ru")
await wait_for_load()
# Log in manually - session saves automatically
PY
```

Reuse profile: `CH_NAME=ozon uv run run.py <<'PY' ...`

## Workflow Examples

### Quick product search

```python
await goto("https://www.ozon.ru/search/?text=механическая+клавиатура&from_global=true")
await wait_for_load()
await wait(2)

# Scroll to load more
await scroll("down", 800)
await wait(0.5)
await scroll("down", 800)
await wait(1)

# Extract results
products = json.loads(await js("""
  (function() {
    const tiles = document.querySelectorAll('[class*="tile-root"]');
    return Array.from(tiles).slice(0, 10).map(tile => {
      const link = tile.querySelector('a[href*="/product/"]');
      const priceMatch = tile.innerText.match(/(\\d[\\d\\s]*)\\s*₽/);
      return {
        title: tile.querySelector('span')?.innerText || '',
        price: priceMatch ? priceMatch[1].replace(/\\s/g, '') : '',
        url: link ? link.href : ''
      };
    });
  })()
"""))

for p in products:
    if p['url']:
        print(f"{p['title'][:50]} — {p['price']}₽")
```

### Deep product analysis

```python
await goto("https://www.ozon.ru/product/...")
await wait_for_load()
await wait(2)

# Extract product data
product = json.loads(await js("/* from product-analysis.md */"))

# Extract specs
specs = json.loads(await js("/* from product-analysis.md */"))

# Print key info
print(f"Бренд: {specs.get('Бренд', 'N/A')}")
print(f"Гарантия: {specs.get('Гарантия', 'N/A')}")
print(f"Продавец: {product['seller']}")
print(f"Рейтинг: {product['rating']}")
```

### Scam check

```python
# Run full scam detection (from scam-detection.md)
result = await full_scam_check("https://www.ozon.ru/product/...")

if result['verdict'] == "SAFE":
    print(f"✅ Trusted seller, good reviews")
elif result['verdict'] == "CAUTION":
    print(f"⚠️  Check carefully: {result['red_flags']}")
else:
    print(f"❌ Avoid: {result['red_flags']}")
```

## Common Tasks

### Filter search results

```python
# By price range
affordable = [p for p in products if p['price'] and 1000 <= int(p['price']) <= 5000]

# By rating
top_rated = [p for p in products if p['rating'] and float(p['rating']) >= 4.5]

# By discount
deals = [p for p in products if p['discount_pct'] and int(p['discount_pct']) >= 20]
```

### Compare products

```python
async def compare_products(urls):
    results = []
    for url in urls:
        await goto(url)
        await wait_for_load()
        await wait(2)
        data = json.loads(await js("/* extraction */"))
        results.append(data)
    return results

products = await compare_products([
    "https://www.ozon.ru/product/...1",
    "https://www.ozon.ru/product/...2"
])

# Compare prices
for p in products:
    print(f"{p['title']}: {p['price']}₽ — {p['seller']}")
```

### Track price changes

```python
# Save product data with timestamp
import json
from datetime import datetime

snapshot = {
    'url': url,
    'price': current_price,
    'timestamp': datetime.now().isoformat()
}

with open('price_history.json', 'a') as f:
    f.write(json.dumps(snapshot) + '\\n')
```

## Gotchas

- **Captcha**: Frequent searches may trigger captcha. Use authenticated session.
- **Dynamic classes**: Use `[class*="pattern"]` selectors, not exact class names.
- **Lazy loading**: Scroll down to load all product cards.
- **Variant prices**: Price changes when selecting color/size variants.
- **Seller pages**: Some sellers redirect to external sites — handle gracefully.

## See Also

- **[Interaction Skills](../../interaction-skills/)** — reusable UI patterns (dialogs, dropdowns, etc.)
- **[helpers.py](../../helpers.py)** — core API reference
