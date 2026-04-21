# 
> **Adapted from browser-harness to camoufox-harness (Playwright API)**
>
> Original browser-harness code used CDP/sync calls. This has been adapted to use Playwright async API.
>
> If you find issues, check `helpers.py` for available functions.


TikTok Studio — Upload Video

URL: `https://www.tiktok.com/tiktokstudio/upload?from=upload&lang=en` (always append `&lang=en`)

## Prerequisites

- Logged into TikTok in the Chrome profile browser-harness is attached to
- Video file on local disk (mp4, <50MB)

## Stale draft banner

TikTok shows "A video you were editing wasn't saved" if a previous upload was abandoned. Dismiss it:

1. Find the banner Discard button (y < 300 in the page)
2. CDP `await click(x, y)` on it
3. A confirmation modal appears — find the red Discard button (y > 300) and CDP `await click(x, y)`
4. Repeat if multiple stale drafts are stacked

## Upload flow

### 1. Attach file

```python
upload_file('input[type="file"]', "/path/to/video.mp4")
await wait(12)  # processing takes ~10s for 5-10MB
```

### 2. Caption

TikTok pre-fills caption with the filename. Clear it first:

```python
await js("document.querySelector('div[contenteditable=\"true\"][role=\"combobox\"]').focus()")
await press_key("End")
async for _ in range(25): await press_key("Backspace")  # clear filename
await type_text("your caption here #hashtag1 #hashtag2")
await press_key("Escape")  # dismiss hashtag suggestions
await click(700, 50)        # click away to deselect
```

Verify: `await js('document.querySelector(\'div[contenteditable="true"][role="combobox"]\').innerText')`

### 3. Schedule

Click the Schedule radio label:
```python
await js("(()=>{var l=document.querySelectorAll('label');for(var i=0;i<l.length;i++){if(l[i].textContent.trim()==='Schedule'){l[i].await click();break}}})()")
```

**Time picker** — uses a scroll-wheel list, NOT a native select. Each `scroll(dy=32)` steps +1 unit, `dy=-32` steps -1 unit.

```python
# 1. ScrollIntoView and open the time picker
await js("...scrollIntoView the time input...")
await click(time_input_x, time_input_y)

# 2. Read default time, calculate difference
default_hour, default_min = 13, 5  # from input value
target_hour, target_min = 20, 25

# 3. Scroll hour column (left, x ≈ 349)
async for _ in range(target_hour - default_hour):
    scroll(349, dropdown_y, dy=32)  # +1 hour per step

# 4. Scroll minute column (right, x ≈ 437)
async for _ in range((target_min - default_min) // 5):
    scroll(437, dropdown_y, dy=32)  # +5 min per step

# 5. Close and verify
await press_key("Escape")
```

**Date picker** — click the date input, then click the target day number span.

### 4. AI-generated content disclosure

Under "Show more" section. Toggle is `[aria-checked]` inside the "AI-generated content" parent.

```python
# Expand settings
await js("...click 'Show more' span...")
# ScrollIntoView the toggle
await js("...scrollIntoView 'ai-generated content' span...")
# Read state and click if false
# A "Turn on" confirmation dialog may appear — click it
```

### 5. Submit

Scroll the Schedule button into view, then CDP `await click(x, y)`. After success, page redirects to `/tiktokstudio/content`.

```python
await js("...scrollIntoView Schedule button (offsetWidth > 100)...")
await click(button_x, button_y)
await wait(6)
assert "content" in await page_info()["url"]
```

## Gotchas

- **JS `.await click()` doesn't work on TikTok's time picker items** — must use CDP `await click(x, y)`
- **Time picker uses virtual scroll** — `scroll(x, y, dy=32)` changes value, NOT regular DOM scroll
- **Caption contenteditable appends on type** — always clear with End + Backspace first, never set innerHTML (breaks React state)
- **beforeunload dialog** blocks navigation if upload is in progress — use `cdp("Page.handleJavaScriptDialog", accept=True)` to dismiss (see `interaction-skills/dialogs.md`)
- **Schedule button text** is "Schedule" only after the Schedule radio is selected (otherwise "Post")
- **"Show more" section** expands the page and pushes the time picker off-viewport — collapse it before adjusting time, expand after
- **Unicode narrow no-break space** (char 8239) appears between time and AM/PM in scheduled post listings — use `.indexOf('12:30')` not exact string match
