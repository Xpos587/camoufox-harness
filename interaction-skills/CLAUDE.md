# Mainframe — Home Server

## Server

- **OS**: Debian 13
- **IP**: `78.40.209.34`
- **Access**: `ssh -i ~/.ssh/id_rsa_remote_nopass root@78.40.209.34`
- **Runtime**: Podman + podman-compose (NOT Docker)

## Architecture

Caddy reverse proxy (Cloudflare DNS challenge) terminates TLS for all services. Single PostgreSQL instance with `init-dbs.sh` provisions per-service databases. Valkey provides caching for RSSHub, Windmill, and SearXNG.

### Active Services

| Subdomain  | Service        | Port(s)                | Notes                          |
|:-----------|:---------------|:-----------------------|:-------------------------------|
| `rss`      | Miniflux       | 8080                   | RSS reader                     |
| `feeds`    | RSSHub         | 1200                   | RSS feed generator             |
| `wm`       | Windmill       | 8000/3001 (LSP)        | Workflow automation            |
| `search`   | SearXNG        | 8080                   | Meta-search (Tor proxy)        |
| `monitor`  | cAdvisor       | 8080                   | Container metrics (basic_auth) |
| `ntfy`     | ntfy           | 80                     | Push notifications             |
| `litellm`  | LiteLLM        | 4000                   | LLM proxy gateway              |
| `sync`     | Syncthing      | 8384, 22000, 21027     | File sync (P2P ports exposed)  |
| `qbit`     | qBittorrent    | 8080, 6881             | Torrent client (P2P exposed)   |
| `crawl`    | Crawl4AI       | 11235                  | Web scraper (WARP proxy)       |
| `dav`      | Baikal         | 80                     | CalDAV/CardDAV                 |
| `mqtt`     | Mosquitto      | 1883, 8883, 9001       | MQTT broker                    |

### Infrastructure

| Service     | Purpose                        |
|:------------|:-------------------------------|
| Caddy       | Reverse proxy + TLS (Cloudflare) |
| PostgreSQL  | Shared database (6 databases)  |
| Valkey      | Cache (databases 0-2)          |
| WARP        | Cloudflare SOCKS5 proxy        |
| Tor         | SOCKS5 proxy (SearXNG)         |

### Commented Out (in compose.yaml)

- **MetaMCP** — MCP server manager
- **CLI-Proxy-API** — CLI proxy service

## Deployment

```bash
scp compose.yaml Caddyfile init-dbs.sh .env root@78.40.209.34:/root/
ssh root@78.40.209.34 'cd /root && podman-compose up -d'
```

## Key Files

- `compose.yaml` — all service definitions
- `Caddyfile` — reverse proxy routes
- `init-dbs.sh` — PostgreSQL database provisioning
- `.env` — secrets and config (never commit)

## Critical Rules

### Data Protection

**NEVER delete podman volumes, databases, or persistent data without explicit user approval.** This is non-negotiable.

- **Volume deletion** (`podman volume rm`, `podman-compose down -v`) — always ask first
- **Database resets** (dropping DBs, recreating postgres volume) — always ask first
- **Config file replacement** (removing and re-creating) — always ask first
- When a fix requires destructive action, present alternatives if they exist

### Database Backups

Backups are done via `pg_dump`. All 6 databases live in a single PostgreSQL instance.

```bash
# Dump a single database
podman exec mainframe_postgres_1 pg_dump -U postgres <dbname> > backup_<dbname>.sql

# Dump all databases
for db in miniflux windmill litellm baikal metamcp cliproxyapi; do
  podman exec mainframe_postgres_1 pg_dump -U postgres $db > backup_${db}.sql
done
```

### File Mount Safety

When deploying files to server via `scp`, always verify on the server that the target is a **file**, not a directory. Directories silently shadow file mounts — a recurring issue with this project.

```bash
# After scp, verify it's a file, not a directory
ssh root@78.40.209.34 'test -f /root/mainframe/<file> && echo OK || echo BROKEN'
```

Files that have historically become directories on the server:
- `Caddyfile`, `init-dbs.sh`, `litellm.yaml` — always verify after upload

## Known Issues

- **podman-compose multiline env vars**: Truncated at first line (issue #908). Workaround: mount config files instead of inline env vars.
