# Downloads

Handle browser-triggered downloads vs direct HTTP fetches.

## Browser-triggered downloads

Downloads initiated by clicking download buttons:

```python
# Set up download handler before clicking
async with _page.expect_download() as download_info:
    await click("#download-button")

download = await download_info.value

# Save to file
await download.save_as("/path/to/save/file.pdf")

# Or get as bytes
content = await download.read()
```

## Download with filename

```python
async with _page.expect_download() as download_info:
    await click("#download-button")

download = await download_info.value
print(f"Downloaded: {download.suggested_filename}")
await download.save_as(f"/tmp/{download.suggested_filename}")
```

## Multiple downloads

For pages that trigger multiple downloads:

```python
downloads = []

# Click multiple times
for i in range(3):
    async with _page.expect_download() as download_info:
        await click(f"#download-{i}")
    downloads.append(await download_info.value)

# Save all
for dl in downloads:
    await dl.save_as(f"/tmp/{dl.suggested_filename}")
```

## Download failure handling

```python
try:
    async with _page.expect_download(timeout=30000) as download_info:
        await click("#download-button")
    download = await download_info.value
    await download.save_as("/tmp/file.pdf")
except Exception as e:
    print(f"Download failed: {e}")
```

## Direct HTTP downloads (no browser)

For simple file downloads, use HTTP directly:

```python
import urllib.request

urllib.request.urlretrieve("https://example.com/file.pdf", "/tmp/file.pdf")
```

This is faster and doesn't require browser overhead.

## Download verification

Verify download completed:

```python
import os

async with _page.expect_download() as download_info:
    await click("#download-button")

download = await download_info.value
path = f"/tmp/{download.suggested_filename}"
await download.save_as(path)

# Verify file exists
if os.path.exists(path):
    size = os.path.getsize(path)
    print(f"Downloaded {size} bytes")
else:
    print("Download failed")
```

## Download progress tracking

Playwright doesn't provide progress callbacks. For large files:

```python
# Use direct HTTP for progress tracking
import urllib.request
from tqdm import tqdm

url = "https://example.com/large-file.zip"
filename = "/tmp/large-file.zip"

with urllib.request.urlopen(url) as response:
    total = int(response.headers.get('content-length', 0))
    with open(filename, 'wb') as f:
        with tqdm(total=total, unit='B', unit_scale=True) as pbar:
            while True:
                chunk = response.read(8192)
                if not chunk:
                    break
                f.write(chunk)
                pbar.update(len(chunk))
```

## Troubleshooting

**Download doesn't start:**
- Check if button actually triggers download
- Verify download permissions
- Check for popup blockers

**Download fails midway:**
- Increase timeout: `async with _page.expect_download(timeout=60000)`
- Check network connection
- Verify server supports resume (for large files)

**Wrong file downloaded:**
- Verify button selector is correct
- Check for dynamic download URLs
- Screenshot before clicking to confirm

## Best Practices

1. **Use expect_download()** — set up handler before clicking
2. **Check suggested_filename** — use server's filename
3. **Verify after download** — check file exists and size
4. **Handle timeouts** — downloads may take time
5. **Use HTTP for simple cases** — faster for direct file URLs
