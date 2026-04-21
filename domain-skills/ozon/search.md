# Ozon — Product Search

> **Adapted from browser-harness to camoufox-harness (Playwright API)**

Field-tested against ozon.ru. Anti-bot protection may require authentication for heavy use.

## Authentication (Recommended)

Ozon may block anonymous browsers with captcha. Authenticate once:

```bash
# Manual login - session persists in profile
CH_NAME=ozon uv run run.py <<'PY'
await goto("https://www.ozon.ru")
await wait_for_load()
# Log in manually in browser window
# Session saves to ~/.config/camoufox-harness/profiles/ozon/
PY
```

After login, cookies persist. Reuse profile: `CH_NAME=ozon uv run run.py ...`

## Search Products

### Direct search URL (fastest)

```python
await goto("https://www.ozon.ru/search/?text=ноутбук+ASUS&from_global=true")
await wait_for_load()
await wait(2)  # Dynamic content loads after readyState
```

### Search via input field

```python
await goto("https://www.ozon.ru")
await wait_for_load()

# Click search box and type
await click('[aria-label*="earch" i], [placeholder*="оиск" i], .search-input')
await type_text('[aria-label*="earch" i], [placeholder*="оиск" i], .search-input', "механическая клавиатура")
await press_key("Enter")
await wait_for_load()
await wait(2)
```

## Extract Product Cards

Ozon uses dynamic classes with `tile-root` pattern. Extract from search results:

```python
import json

# Scroll to load more results
await scroll("down", 800)
await wait(0.5)
await scroll("down", 800)
await wait(1)

# Extract product tiles
products = await js("""
(function() {
  const tiles = document.querySelectorAll('[class*="tile-root"]');
  const results = [];

  tiles.forEach(tile => {
    const link = tile.querySelector('a[href*="/product/"]');
    if (!link) return;

    const href = link.href.split('?')[0];
    if (!href) return;

    // Extract title (skip noise like "Hit", "Sale")
    const spans = Array.from(tile.querySelectorAll('span'));
    let title = '';
    for (const s of spans) {
      const cls = s.className || '';
      const text = s.innerText?.trim() || '';
      if (cls.includes('tsBody500Medium') && text.length > 15) {
        title = text;
        break;
      }
    }

    // Fallback: get longest text line
    if (!title) {
      const lines = tile.innerText.split('  ');
      const candidates = lines
        .map(l => l.trim())
        .filter(l => l.length > 20 && !/^[\\d\\s]+₽/.test(l));
      title = candidates.sort((a,b) => b.length - a.length)[0] || '';
    }

    // Price (may have old price for discounts)
    const priceMatch = tile.innerText.match(/(\\d[\\d\\s]*)\\s*₽/g);
    const prices = priceMatch ? priceMatch.map(p => p.replace(/[\\s₽]/g, '')) : [];

    // Rating
    const ratingMatch = tile.innerText.match(/(?<!\\d)([1-5])\\s*[,\\.]\\s*(\\d)(?!\\d)/);
    const rating = ratingMatch ? `${ratingMatch[1]}.${ratingMatch[2]}` : '';

    // Reviews count
    const revMatch = tile.innerText.match(/(\\d+)\\s*отзыв/i);
    const reviews = revMatch ? revMatch[1] : '';

    // Discount
    const discMatch = tile.innerText.match(/−(\\d+)%/);
    const discount = discMatch ? discMatch[1] : '';

    // Image
    const img = tile.querySelector('img');
    const image = img ? (img.src || img.dataset.src || '') : '';

    // Delivery date
    const delivMatch = tile.innerText.match(
      /(\\d+\\s+(?:марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря|января|февраля))/
    );
    const delivery = delivMatch ? delivMatch[1] : '';

    results.push({
      title: title.substring(0, 200),
      price: prices[0] || '',
      old_price: prices[1] || '',
      discount_pct: discount,
      url: href,
      rating: rating,
      reviews_count: reviews,
      image: image,
      delivery: delivery
    });
  });

  return results;
})()
""")

# Parse JSON response
products_data = json.loads(products)
print(f"Found {len(products_data)} products")
```

## Output Format

```python
# Example product card
{
  "title": "Клавиатура механическая Redragon Kumara K552 RGB",
  "price": "3490",
  "old_price": "4990",
  "discount_pct": "30",
  "url": "https://www.ozon.ru/product/klaviatura-mekhanicheskaya-redragon-kumara-k552-rgb-123456789/",
  "rating": "4.8",
  "reviews_count": "1247",
  "image": "https://.../thumbnail.jpg",
  "delivery": "15 апреля"
}
```

## Pagination

Load more results by scrolling:

```python
# Scroll to bottom multiple times to trigger lazy loading
for i in range(3):
    await scroll("down", 1000)
    await wait(1)

# Extract again (will include newly loaded items)
products = await js("...")  # Same extraction code
```

## Filter Results

```python
# Filter by price range
filtered = [p for p in products_data
            if p['price'] and 1000 <= int(p['price']) <= 5000]

# Filter by rating
high_rated = [p for p in products_data
              if p['rating'] and float(p['rating']) >= 4.5]

# Filter by discount
discounted = [p for p in products_data
              if p['discount_pct'] and int(p['discount_pct']) >= 20]
```

## Gotchas

- **Dynamic classes**: Ozon uses CSS modules with hashed class names. Always use attribute selectors like `[class*="tile-root"]` (contains) rather than exact class matches.

- **Tile noise text**: Badges like "Хит продаж", "Новинка", "Оригинал" appear in tile text. The extraction logic filters these by checking text length (>20 chars) and excluding common patterns.

- **Price format**: Russian locale with spaces as thousand separators and `₽` symbol: `1 234 567 ₽`. Strip spaces and symbol before parsing as int.

- **Rating format**: Decimal with comma or dot: `4,8` or `4.8`. May be missing for new products.

- **Empty titles**: Some tiles are ads or promotions. Skip if title extraction fails or is very short.

- **Captcha**: If Ozon suspects bot activity, may show captcha. Signs: page title contains "Captcha" or "Подтверждение", no product tiles load. Authenticate with real account if this happens frequently.

- **Delivery date**: Text format varies: "15 апреля", "завтра", "через 2 дня". The regex captures specific date patterns only.
