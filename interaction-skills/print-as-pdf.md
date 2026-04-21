# Print As PDF

Generate PDF from pages via Playwright's PDF API.

## Direct PDF generation

Generate PDF without print dialog:

```python
# Generate PDF of current page
pdf_bytes = await _page.pdf()

# Save to file
with open("/tmp/page.pdf", "wb") as f:
    f.write(pdf_bytes)
```

## PDF with options

Control PDF generation:

```python
pdf_bytes = await _page.pdf(
    format="A4",
    print_background=True,
    margin={
        "top": "1cm",
        "right": "1cm",
        "bottom": "1cm",
        "left": "1cm"
    }
)
```

## PDF of specific element

Generate PDF of single element:

```python
# Get element
element = await _page.locator("#article-content").pdf()

# Save
with open("/tmp/article.pdf", "wb") as f:
    f.write(element)
```

## Multi-page PDF

For pages with pagination:

```python
all_pages = []

# Click through pages
while True:
    # Add current page to PDF
    all_pages.append(await _page.pdf())

    # Check if next button exists
    next_button = await _page.query_selector("#next-page")
    if not next_button:
        break

    # Click next
    await next_button.click()
    await wait_for_load()

# Combine pages (requires PyPDF2 or similar)
from PyPDF2 import PdfMerger

merger = PdfMerger()
for i, page_bytes in enumerate(all_pages):
    with open(f"/tmp/page_{i}.pdf", "wb") as f:
        f.write(page_bytes)
    merger.append(f"/tmp/page_{i}.pdf")

merger.write("/tmp/combined.pdf")
merger.close()
```

## Sites with "Print" button

Some sites require clicking print button first:

```python
# Click print button
async with _page.expect_popup() as popup_info:
    await click("#print-button")

popup = await popup_info.value

# Generate PDF from popup
pdf_bytes = await popup.pdf()
with open("/tmp/print.pdf", "wb") as f:
    f.write(pdf_bytes)
```

## Print dialog handling

If site shows browser print dialog:

```python
# Set up print handler before action
async def handle_print(dialog):
    # Playwright auto-accepts print dialogs in headless mode
    # For visible mode, you may need to handle
    await dialog.accept()

_page.on("dialog", handle_print)

# Trigger print
await click("#print-button")
```

## PDF to image conversion

Convert PDF pages to images:

```python
pdf_bytes = await _page.pdf()

# Use pdf2image library
from pdf2image import convert_from_bytes
images = convert_from_bytes(pdf_bytes)

# Save first page
images[0].save("/tmp/page-1.png", "PNG")
```

## Troubleshooting

**PDF is empty:**
- Page may not be fully loaded: `await wait_for_load()`
- Content may be lazy-loaded: scroll to trigger load
- Check for JavaScript-rendered content

**PDF has wrong content:**
- Screenshot first to verify page state
- Check for dynamic content that changes after PDF generation
- Verify CSS is applying correctly

**PDF generation fails:**
- Some sites block PDF generation
- Check for CORS issues with external resources
- Try print background option: `print_background=True`

## Best Practices

1. **Wait for load** — ensure page is fully rendered before PDF
2. **Use print_background** — include background colors/graphics
3. **Set appropriate margins** — avoid content cutoff
4. **Verify content** — screenshot before generating PDF
5. **Handle large pages** — consider page size for multi-content documents
