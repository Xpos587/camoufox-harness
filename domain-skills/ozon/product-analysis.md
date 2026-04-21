# Ozon — Product Page Analysis

> **Adapted from browser-harness to camoufox-harness (Playwright API)**

Extract full product details: specs, price, seller, delivery options.

## Navigate to Product

```python
url = "https://www.ozon.ru/product/klaviatura-mekhanicheskaya-123456789/"
await goto(url)
await wait_for_load()
await wait(2)  # Wait for dynamic widgets
```

## Extract Product Data

```python
import json

product = await js("""
(function() {
  // Product title
  const titleEl = document.querySelector('h1, [data-widget="webProductHeading"]');
  const title = titleEl ? titleEl.innerText.trim() : '';

  // Price (current and old if discounted)
  const priceEl = document.querySelector('[class*="price"] span, .tsHeadline500Medium');
  const priceText = priceEl ? priceEl.innerText.replace(/[^\\d]/g, '') : '';

  const oldPriceEl = document.querySelector('[class*="oldPrice"] span, .tsBodyControlLargeStrike');
  const oldPriceText = oldPriceEl ? oldPriceEl.innerText.replace(/[^\\d]/g, '') : '';

  // Overall rating (widget: webSingleProductScore)
  const scoreWidget = document.querySelector('[data-widget="webSingleProductScore"]');
  let rating = '';
  if (scoreWidget) {
    const ratingText = scoreWidget.innerText;
    const match = ratingText.match(/([1-5])[,\\.]\\d/);
    rating = match ? match[1] + '.' + (match[2] || '0') : '';
  }

  // Reviews count
  const reviewsLink = document.querySelector('a[href*="/reviews"]');
  const reviewsMatch = reviewsLink ? reviewsLink.innerText.match(/(\\d+)/) : null;
  const reviews_count = reviewsMatch ? reviewsMatch[1] : '0';

  // Seller info
  const sellerLink = document.querySelector('a[href*="/seller/"], [class*="seller"]');
  const seller = sellerLink ? sellerLink.innerText.trim() : '';

  // Seller link
  const sellerHref = sellerLink ? sellerLink.href : '';

  // Delivery options
  const deliveryEl = document.querySelector('[class*="delivery"]');
  const delivery = deliveryEl ? deliveryEl.innerText.trim() : '';

  // Stock status
  const stockEl = document.querySelector('[class*="stock"], [class*="available"]');
  const in_stock = stockEl ? !/нет в наличии/i.test(stockEl.innerText) : true;

  // Product ID (from URL or page)
  const urlMatch = window.location.href.match(/\\/product\\/([\\w-]+)/);
  const product_id = urlMatch ? urlMatch[1] : '';

  // Images
  const images = [];
  document.querySelectorAll('img[src*="ozon"], img[src*="cdn1"]').forEach(img => {
    const src = img.src || img.dataset.src;
    if (src && src.includes('thumbnail')) {
      images.push(src.replace('thumbnail', '700'));
    }
  });

  return {
    title: title,
    price: priceText,
    old_price: oldPriceText,
    rating: rating,
    reviews_count: reviews_count,
    seller: seller,
    seller_url: sellerHref,
    delivery: delivery,
    in_stock: in_stock,
    product_id: product_id,
    images: images.slice(0, 5)
  };
})()
""")

data = json.loads(product)
print(data['title'], data['price'], data['seller'])
```

## Extract Specifications

Ozon stores specs in a structured widget. Extract key attributes:

```python
specs = await js("""
(function() {
  const specs = {};

  // Method 1: Spec attributes widget
  document.querySelectorAll('[data-widget="webSpecsAttributes"]').forEach(widget => {
    const rows = widget.querySelectorAll('tr, [class*="attribute"]');
    rows.forEach(row => {
      const label = row.querySelector('td:first-child, div:first-child, [class*="label"]');
      const value = row.querySelector('td:last-child, div:last-child, [class*="value"]');
      if (label && value) {
        const key = label.innerText.trim();
        const val = value.innerText.trim();
        if (key && val) {
          specs[key] = val;
        }
      }
    });
  });

  // Method 2: Description lists
  document.querySelectorAll('dl, .specs-list').forEach(list => {
    const terms = list.querySelectorAll('dt, [class*="term"]');
    const defs = list.querySelectorAll('dd, [class*="definition"]');
    terms.forEach((term, i) => {
      if (defs[i]) {
        specs[term.innerText.trim()] = defs[i].innerText.trim();
      }
    });
  });

  return specs;
})()
""")

# Parse as dict
import json
specs_data = json.loads(specs)

# Get specific spec
brand = specs_data.get('Бренд', 'N/A')
model = specs_data.get('Модель', 'N/A')
warranty = specs_data.get('Гарантия', 'N/A')
```

## Extract Description

```python
description = await js("""
(function() {
  const descEl = document.querySelector('[data-widget="webTextDescription"], .product-description');
  return descEl ? descEl.innerText.trim() : '';
})()
""")
```

## Check Variants

Products often have variants (color, size, storage):

```python
variants = await js("""
(function() {
  const variants = [];
  const buttons = document.querySelectorAll('[class*="variant"] button, [class*="color"] button');

  buttons.forEach(btn => {
    const label = btn.innerText.trim();
    const disabled = btn.disabled || btn.getAttribute('aria-disabled') === 'true';
    const selected = btn.classList.contains('selected') || btn.getAttribute('aria-pressed') === 'true';

    variants.push({
      label: label,
      available: !disabled,
      selected: selected
    });
  });

  return variants;
})()
""")

variants_data = json.loads(variants)
available = [v['label'] for v in variants_data if v['available']]
```

## Full Product Summary

```python
async def analyze_ozon_product(url):
    await goto(url)
    await wait_for_load()
    await wait(2)

    # Extract all data
    product = json.loads(await js("/* product extraction code */"))
    specs = json.loads(await js("/* specs extraction code */"))
    description = await js("/* description extraction */")

    return {
        'product': product,
        'specs': specs,
        'description': description,
        'url': url,
        'scraped_at': datetime.now().isoformat()
    }

# Usage
result = await analyze_ozon_product("https://www.ozon.ru/product/...")
print(f"{result['product']['title']} — {result['product']['price']}₽")
print(f"Бренд: {result['specs'].get('Бренд', 'N/A')}")
```

## Output Format

```json
{
  "product": {
    "title": "Клавиатура механическая Redragon Kumara K552 RGB",
    "price": "3490",
    "old_price": "4990",
    "rating": "4.8",
    "reviews_count": "1247",
    "seller": "Ozon",
    "seller_url": "https://www.ozon.ru/seller/ozon-123/",
    "delivery": "Доставка 15 апреля",
    "in_stock": true,
    "product_id": "klaviatura-mekhanicheskaya-redragon-kumara-k552-rgb-123456789",
    "images": ["https://...", "https://..."]
  },
  "specs": {
    "Бренд": "Redragon",
    "Тип": "Механическая",
    "Подсветка": "RGB",
    "Подключение": "Проводное",
    "Гарантия": "12 месяцев"
  },
  "description": "Механическая клавиатура...",
  "url": "https://www.ozon.ru/product/...",
  "scraped_at": "2026-04-21T22:30:00"
}
```

## Gotchas

- **Dynamic widgets**: Specs, reviews, and related products load asynchronously. Wait 2-3 seconds after page load.

- **Seller URL format**: `https://www.ozon.ru/seller/{slug}-{id}/`. Extract seller ID from URL for detailed seller info.

- **Price per variant**: Price may change when selecting different variants (color, size). Check price after variant selection.

- **Out of stock**: Products with variants may show some as unavailable. Check `disabled` attribute on variant buttons.

- **Description truncation**: Long descriptions may be collapsed. Click "Показать ещё" or similar to expand.

- **Image CDN**: Ozon uses CDN URLs with quality parameters. `thumbnail/700` is good quality, `thumbnail/1000` for high-res.
