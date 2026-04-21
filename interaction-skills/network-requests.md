# Network Requests

Monitor and intercept network activity for debugging, API discovery, or request modification.

## Monitoring requests

Track all network requests during page load:

```python
# Set up request logging
requests = []

_page.on("request", lambda req: requests.append({
    "url": req.url,
    "method": req.method,
    "resource_type": req.resource_type
}))

# Navigate and collect requests
await goto("https://example.com")
await wait_for_load()

# Print requests
for req in requests:
    print(f"{req['method']} {req['url']}")
```

## Monitoring responses

```python
responses = []

_page.on("response", lambda res: responses.append({
    "url": res.url,
    "status": res.status,
    "headers": res.headers
}))

await goto("https://example.com")

# Find failed requests
failed = [r for r in responses if r["status"] >= 400]
for fail in failed:
    print(f"FAIL {fail['status']}: {fail['url']}")
```

## Intercepting requests

Modify or block requests:

```python
# Route all requests
async def handle_route(route):
    # Block specific domains
    if "tracker.com" in route.request.url:
        await route.abort()
    else:
        await route.continue_()

_page.route("**/*", handle_route)

# Now navigate
await goto("https://example.com")
```

## Mocking API responses

Replace API responses with test data:

```python
async def mock_api(route):
    if "/api/data" in route.request.url:
        # Return fake data
        await route.fulfill(
            status=200,
            body='{"results": ["test1", "test2"]}',
            headers={"Content-Type": "application/json"}
        )
    else:
        await route.continue_()

_page.route("**/api/**", mock_api)

await goto("https://example.com")
```

## Capturing POST data

See what data forms submit:

```python
post_data = []

async def capture_request(route):
    request = route.request
    if request.method == "POST":
        post_data.append({
            "url": request.url,
            "data": await request.post_data()
        })
    await route.continue_()

_page.route("**/*", capture_request)

await click("#submit-button")
await wait_for_load()

for post in post_data:
    print(f"POST to {post['url']}")
    print(f"Data: {post['data']}")
```

## Finding private APIs

Discover hidden API endpoints:

```python
api_calls = []

def log_request(request):
    if request.resource_type == "fetch" or request.resource_type == "xhr":
        api_calls.append({
            "url": request.url,
            "method": request.method
        })

_page.on("request", log_request)

# Interact with site
await goto("https://example.com")
await click("#load-data-button")
await wait_for_load()

# Print discovered APIs
for api in set(a["url"] for a in api_calls):
    print(f"API: {api}")
```

## Response headers

Check response headers for debugging:

```python
async def check_headers(route):
    response = await route.request.response()
    if response:
        print(f"{route.request.url}:")
        for key, value in response.headers.items():
            print(f"  {key}: {value}")
    await route.continue_()

_page.route("**/*", check_headers)
await goto("https://example.com")
```

## Blocking resources

Speed up page load by blocking unnecessary resources:

```python
# Block images, fonts, media
async def block_resources(route):
    if route.request.resource_type in ["image", "font", "media"]:
        await route.abort()
    else:
        await route.continue_()

_page.route("**/*", block_resources)

await goto("https://example.com")  # Faster load
```

## Troubleshooting

**Requests not logged:**
- Ensure handlers are set up before navigation
- Check for CORS issues (some requests may be blocked)
- Verify resource type filters

**Route not intercepting:**
- Check route pattern matches URL
- Routes are matched in order — more specific first
- Some requests may bypass service workers

**Mocked data not loading:**
- Verify response headers match expected format
- Check status code is appropriate
- Ensure Content-Type is correct

## Best Practices

1. **Set up handlers early** — before navigation/action
2. **Use specific patterns** — narrow route patterns for targeted interception
3. **Clean up handlers** — remove handlers when done to avoid memory leaks
4. **Check resource types** — filter by `fetch`, `xhr`, `stylesheet`, etc.
5. **Handle errors** — routes may fail, have fallback logic
