# Uploads

File uploads via `<input type="file">` elements. Playwright handles this cleanly without needing to click the input.

## Direct file upload (preferred)

Playwright can set files directly on the input element:

```python
# Single file
await _page.locator("input[type='file']").set_input_files("/path/to/file.pdf")

# Multiple files
await _page.locator("input[type='file']").set_input_files([
    "/path/to/file1.pdf",
    "/path/to/file2.pdf"
])
```

This is the cleanest approach — no dialog handling, no OS interaction.

## Hidden file inputs

Many sites hide the file input and trigger it via a button. Two approaches:

### Option A: Reveal the input (cleaner)

```python
# Make input visible
await js("""
    const input = document.querySelector('input[type="file"]');
    if (input) {
        input.style.display = 'block';
        input.style.visibility = 'visible';
    }
""")

# Now upload directly
await _page.locator("input[type='file']").set_input_files("/path/to/file.pdf")
```

### Option B: Click and handle dialog

```python
# Click the button that triggers file picker
await click("#upload-button")

# This will open OS file picker — NOT AUTOMATABLE via Playwright
# Use Option A instead
```

**Recommendation:** Always use Option A. OS file pickers cannot be automated reliably.

## Upload with temp files

When generating files dynamically:

```python
import tempfile

# Create temp file
with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
    f.write("content")
    temp_path = f.name

# Upload
await _page.locator("input[type='file']").set_input_files(temp_path)

# Cleanup later
import os
os.unlink(temp_path)
```

## Upload with progress tracking

Some sites show progress bars. Monitor for completion:

```python
# Upload file
await _page.locator("input[type='file']").set_input_files("/path/to/file.pdf")

# Wait for upload completion
await _page.wait_for_selector(".upload-complete", timeout=30000)
# or
await _page.wait_for_selector(".progress-bar", state="hidden")
```

## Drag-and-drop uploads

Some zones accept files via drag-and-drop:

```python
# Playwright supports this in newer versions
await _page.locator(".drop-zone").dispatch_event("drop", {
    "dataTransfer": {
        "files": ["/path/to/file.pdf"]
    }
})
```

**Alternative:** Reveal hidden file input and use `set_input_files()`.

## Multiple file inputs

Pages with multiple upload fields:

```python
# Identify specific input
await _page.locator("#avatar-upload").set_input_files("/path/to/avatar.jpg")
await _page.locator("#document-upload").set_input_files("/path/to/doc.pdf")
```

## File validation handling

Sites may validate file type/size:

```python
# Check for error messages after upload
await _page.locator("input[type='file']").set_input_files("/path/to/file.pdf")
await wait_for_load()

# Check for errors
error = await _page.locator(".upload-error").text_content()
if error:
    print(f"Upload failed: {error}")
```

## Best Practices

1. **Always use `set_input_files()`** — don't try to click file inputs
2. **Reveal hidden inputs** — make input visible with JS if needed
3. **Handle validation** — check for error messages after upload
4. **Wait for completion** — use wait_for_selector or wait_for_load
5. **Clean up temp files** — delete after upload if using temp files
6. **Test file types** — verify accepted formats (PDF, JPG, PNG, etc.)

## Framework-Specific Notes

**Dropzone.js:**
- Uses `.dropzone` class
- Has hidden file input with `name="file"`
- May need to trigger `click` on dropzone element

**React Dropzone:**
- Input is hidden, need to reveal with JS
- May have `accept` attribute for file types

**jQuery File Upload:**
- Uses `input[type="file"]` with `multiple` attribute
- Progress tracking via `.progress` class

**AWS S3 uploads:**
- May use direct POST to S3
- Check network tab for actual upload endpoint
- Sometimes faster to POST directly rather than via browser
