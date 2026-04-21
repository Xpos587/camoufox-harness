# Cookies

Cookie management is built into camoufox-harness via Playwright's browser context.

## Get all cookies

```python
cookies = await get_cookies()
for cookie in cookies:
    print(f"{cookie['name']}: {cookie['value'][:20]}...")
```

## Set cookies

```python
await set_cookies([
    {
        "name": "session",
        "value": "abc123",
        "domain": ".example.com",
        "path": "/",
        "httpOnly": True,
        "secure": True
    }
])
```

## Cookies for specific domain

```python
# Get cookies for current page
cookies = await get_cookies()

# Filter by domain
example_cookies = [c for c in cookies if "example.com" in c.get("domain", "")]
```

## Session persistence

Save/load cookies for session persistence:

```python
# Save current session (includes cookies + localStorage)
await save_profile("my-session")

# Load saved session
await load_profile("my-session")
```

Profiles are stored in `~/.config/camoufox-harness/profiles/<name>/`:
- `cookies.json` — all cookies
- `localStorage.json` — localStorage data

## Cookie troubleshooting

**Cookies not saving:**
- Check domain matches (include leading dot for subdomains: `.example.com`)
- Verify `secure` flag matches (HTTPS cookies need `secure: True`)
- Some sites may use localStorage instead of cookies

**Session expired:**
- Use `save_profile()` after logging in
- Load profile before continuing work
- Some sites require additional validation (2FA, email confirmation)

## Cookie-based auth

For sites that use cookies for authentication:

```python
# Log in once
await goto("https://example.com/login")
await type_text("#email", "user@example.com")
await type_text("#password", "password")
await click("#login-button")
await wait_for_load()

# Save session
await save_profile("example-session")

# Later, restore session without re-login
await load_profile("example-session")
await goto("https://example.com/dashboard")
```

## Best Practices

1. **Save after login** — persist authenticated session
2. **Check domain** — ensure cookie domain matches site
3. **Use profiles** — separate profiles for different sites/accounts
4. **Verify auth** — after loading profile, check you're actually logged in
