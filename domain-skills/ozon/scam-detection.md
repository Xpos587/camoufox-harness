# Ozon — Scam Detection & Trust Analysis

> **Anti-fraud patterns for Ozon marketplace**

## Quick Check: Red Flags

Immediate disqualification if ANY of these are present:

| Flag | Pattern | Action |
|------|---------|--------|
| **Price anomaly** | 40%+ below market for identical specs | ❌ Skip |
| **New seller + high value** | Seller <3 months old, item >10k₽ | ❌ Skip |
| **Review bot spike** | All reviews within 48h, >50 total | ❌ Skip |
| **Vague specs** | "Intel i7" without model, "4K" without resolution | ❌ Skip |
| **Rating distortion** | >95% are 5★ with 10+ reviews | ❌ Skip |
| **Stock photos only** | All images are manufacturer renders | ⚠️ Caution |
| **No returns** | "Возврат невозможен" for electronics | ⚠️ Caution |

## Yellow Flags (Investigate)

| Flag | Pattern | Check |
|------|---------|-------|
| **Price too good** | 20-40% below market | Verify specs match |
| **Mixed sentiment** | High rating but negative review text | Read recent reviews |
| **Few products, many sales** | Suspicious inventory ratio | Check seller profile |
| **Copy-paste specs** | Specs identical to other sellers | Cross-reference |
| **Review velocity** | Sudden spike in reviews | Check review dates |
| **Seller inactive** | No responses to reviews | Red flag |

## Trust Signals (Positive)

| Signal | Pattern | Confidence |
|--------|---------|------------|
| **Official store** | Brand name matches manufacturer | ✅ High |
| **Review timeline** | Reviews spread over months | ✅ High |
| **Photo reviews** >20% | Real product photos | ✅ High |
| **Seller activity** | Responds to questions/reviews | ✅ Medium |
| **Consistent specs** | Match official manufacturer page | ✅ High |

## Scam Pattern Detection

### 1. Price Anomaly Detection

```python
import json

async def check_price_anomaly(product_data, market_price_range):
    """
    product_data: dict from product-analysis.md
    market_price_range: (min, max) tuple for this product category
    """
    price = int(product_data['product']['price'])
    min_market, max_market = market_price_range

    if price < min_market * 0.6:
        return {"verdict": "SCAM", "reason": f"Price {price}₽ is 40%+ below market ({min_market}-{max_market}₽)"}
    elif price < min_market * 0.8:
        return {"verdict": "SUSPICIOUS", "reason": f"Price {price}₽ is 20-40% below market"}
    else:
        return {"verdict": "OK", "price_ratio": price / max_market}

# Usage
result = await check_price_anomaly(data, (5000, 8000))  # Mechanical keyboard market range
```

### 2. Seller Trust Check

```python
async def check_seller_trust(product_data):
    """Extract seller info from product page, check trust signals."""
    seller_url = product_data['product'].get('seller_url', '')

    if not seller_url:
        return {"verdict": "UNKNOWN", "reason": "No seller info"}

    # Navigate to seller page
    await goto(seller_url)
    await wait_for_load()
    await wait(1)

    seller_info = await js("""
    (function() {
      const nameEl = document.querySelector('h1, [class*="seller-name"]');
      const ratingEl = document.querySelector('[class*="rating"]');
      const ageEl = document.querySelector('[class*="seller-age"], .since');
      const productsEl = document.querySelector('[class*="products-count"]');

      return {
        name: nameEl ? nameEl.innerText.trim() : '',
        rating: ratingEl ? ratingEl.innerText.trim() : '',
        age_months: ageEl ? ageEl.innerText.match(/(\\d+)/)?.[1] : '',
        products_count: productsEl ? productsEl.innerText.match(/(\\d+)/)?.[1] : ''
      };
    })()
    """)

    seller = json.loads(seller_info)

    # Trust score calculation
    score = 0
    reasons = []

    if seller.get('rating') and float(seller['rating']) >= 4.5:
        score += 3
        reasons.append("Good seller rating")
    elif seller.get('rating') and float(seller['rating']) < 3.5:
        score -= 2
        reasons.append("Poor seller rating")

    if seller.get('age_months'):
        months = int(seller['age_months'])
        if months >= 12:
            score += 2
            reasons.append(f"Established seller ({months} months)")
        elif months < 3:
            score -= 3
            reasons.append(f"New seller ({months} months)")

    if seller.get('products_count'):
        products = int(seller['products_count'])
        if products > 100:
            score += 1
            reasons.append("Large inventory")

    verdict = "TRUSTED" if score >= 4 else "SUSPICIOUS" if score >= 0 else "UNTRUSTED"

    return {
        "verdict": verdict,
        "score": score,
        "reasons": reasons,
        "seller": seller
    }
```

### 3. Review Authenticity Check

```python
async def check_review_authenticity(product_url, max_reviews=30):
    """Analyze reviews for bot patterns."""
    await goto(product_url)
    await wait_for_load()
    await wait(2)

    # Scroll to reviews section to trigger rating distribution load
    await scroll("down", 500)
    await wait(1)

    reviews_data = await js("""
    (function() {
      const reviews = [];
      document.querySelectorAll('[class*="review"], [data-widget="review"]').forEach(el => {
        const author = el.querySelector('[class*="author"]')?.innerText.trim() || '';
        const rating = el.querySelector('[class*="rating"]')?.innerText.match(/([1-5])/)?.[1] || '';
        const date = el.querySelector('[class*="date"], time')?.innerText.trim() || '';
        const text = el.querySelector('[class*="text"], [class*="body"]')?.innerText.trim() || '';
        const has_photo = !!el.querySelector('img[src*="review"], img[src*="photo"]');

        reviews.push({author, rating, date, text, has_photo});
      });
      return JSON.stringify(reviews);
    })()
    """)

    reviews = json.loads(reviews_data)

    if not reviews:
        return {"verdict": "UNKNOWN", "reason": "No reviews found"}

    # Analyze patterns
    # 1. Review velocity (check if all posted within short window)
    dates = []
    for r in reviews:
        if r['date']:
            # Parse Russian date format
            date_str = r['date']  # e.g. "15 апреля 2026"
            # Simple heuristic: extract day/month
            parts = date_str.split()
            if len(parts) >= 2:
                dates.append(parts[0] + parts[1])  # "15апреля"

    # 2. Rating distribution (check for 5-star spam)
    ratings = [int(r['rating']) for r in reviews if r['rating']]
    five_star_pct = len([r for r in ratings if r == 5]) / len(ratings) * 100 if ratings else 0

    # 3. Photo reviews (indicate real purchases)
    photo_reviews = len([r for r in reviews if r['has_photo']])
    photo_pct = photo_reviews / len(reviews) * 100

    # 4. Text length (short reviews may be bots)
    avg_text_length = sum(len(r['text']) for r in reviews) / len(reviews)

    # Calculate trust score
    score = 0
    red_flags = []

    if five_star_pct > 95 and len(reviews) > 10:
        red_flags.append(f"Suspicious rating distribution: {five_star_pct:.0f}% are 5-star")

    if photo_pct < 5:
        red_flags.append(f"Few photo reviews: {photo_pct:.0f}%")

    if avg_text_length < 50:
        red_flags.append(f"Suspiciously short reviews: avg {avg_text_length:.0f} chars")

    # Review velocity check (simplified)
    if len(dates) >= 10:
        unique_dates = len(set(dates))
        if unique_dates < 3:
            red_flags.append(f"Review velocity anomaly: {len(reviews)} reviews posted within {unique_dates} unique dates")

    verdict = "AUTHENTIC" if not red_flags else "SUSPICIOUS"

    return {
        "verdict": verdict,
        "total_reviews": len(reviews),
        "five_star_pct": five_star_pct,
        "photo_pct": photo_pct,
        "avg_text_length": avg_text_length,
        "red_flags": red_flags
    }
```

## Full Scam Check Workflow

```python
async def full_scam_check(product_url):
    """Run all scam detection checks."""
    # 1. Get product data
    await goto(product_url)
    await wait_for_load()
    await wait(2)

    product_data = json.loads(await js("/* extraction code */"))

    # 2. Price check (requires external market data)
    # price_check = await check_price_anomaly(product_data, market_range)

    # 3. Seller check
    seller_check = await check_seller_trust(product_data)

    # 4. Review check
    review_check = await check_review_authenticity(product_url)

    # 5. Overall verdict
    score = 0
    red_flags = []
    green_flags = []

    if seller_check['verdict'] == "UNTRUSTED":
        score -= 3
        red_flags.extend(seller_check['reasons'])
    elif seller_check['verdict'] == "TRUSTED":
        score += 2
        green_flags.extend(seller_check['reasons'])

    if review_check['verdict'] == "SUSPICIOUS":
        score -= 2
        red_flags.extend(review_check['red_flags'])
    elif review_check['verdict'] == "AUTHENTIC":
        score += 1

    verdict = "SAFE" if score >= 2 else "CAUTION" if score >= 0 else "AVOID"

    return {
        "verdict": verdict,
        "score": score,
        "red_flags": red_flags,
        "green_flags": green_flags,
        "checks": {
            "seller": seller_check,
            "reviews": review_check
        },
        "product": product_data['product']
    }

# Usage
result = await full_scam_check("https://www.ozon.ru/product/...")
print(f"Verdict: {result['verdict']} (score: {result['score']})")
print(f"Red flags: {result['red_flags']}")
```

## Reference Scam Patterns

Common scams on Ozon:

1. **Fake brand items**: Generic products with brand stickers. Check specs against official manufacturer site.

2. **Bait and switch**: Show quality product photos, ship cheap knockoff. Check review photos.

3. **Review manipulation**: New sellers with hundreds of 5-star reviews in days. Check review dates.

4. **Price trapping**: Attractive price, but "only 1 left" and redirect to different product.

5. **Warranty evasion**: "Гарантия предоставляется продавцом" but seller disappears in 2 months.

6. **Spec inflation**: Claims "4K" but actually 1080p. Cross-reference specs.

## Quick Reference: Trust Score Calculation

```
+3: Seller rating >= 4.5
+2: Seller >= 12 months old
+2: Official brand store
+1: Authentic reviews (photos, spread over time)
+1: Large seller inventory (>100 products)

-3: Seller < 3 months old
-2: Seller rating < 3.5
-2: Suspicious review patterns
-3: Price 40%+ below market
```

Score ≥ 2: **SAFE** | 0-1: **CAUTION** | < 0: **AVOID**
