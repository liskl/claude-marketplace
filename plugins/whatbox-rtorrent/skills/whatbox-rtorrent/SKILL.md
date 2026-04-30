---
name: whatbox-rtorrent
description: List and (later) control torrents on a Whatbox seedbox via rTorrent XML-RPC. Use when the user asks to list torrents, check seedbox status, manage rTorrent, or mentions Whatbox / rTorrent / a magnet link in this project.
---

# whatbox-rtorrent

Talks to a [Whatbox](https://whatbox.ca/) seedbox's rTorrent instance over XML-RPC. Ships `list` and state controls (`start`, `stop`, `pause`, `resume`). `add <magnet>` is still on the roadmap.

## Prerequisites

Three values are required. They can come from the process environment, a `.env` file in the project root, or a mix of both. **Already-exported environment variables win** — the `.env` only fills in whatever the environment is missing.

```
WHATBOX_USERNAME=<your whatbox username>
WHATBOX_PASSWORD=<your whatbox password>
WHATBOX_HOSTNAME=<your slot's rTorrent host, e.g. rtorrent.adoredstork.box.ca>
```

So any of the following work:

```bash
# all three exported, no .env needed
export WHATBOX_USERNAME=... WHATBOX_PASSWORD=... WHATBOX_HOSTNAME=...
python3 .claude/skills/whatbox-rtorrent/scripts/whatbox.py list

# .env in the project root, nothing exported
python3 .claude/skills/whatbox-rtorrent/scripts/whatbox.py list

# override one value from .env at invocation time
WHATBOX_HOSTNAME=other.host.box.ca python3 .claude/skills/whatbox-rtorrent/scripts/whatbox.py list
```

Python 3.10+ (uses PEP 604 `|` types and stdlib only — no pip install needed).

## Usage

Run from the project root (where `.env` lives):

```bash
python3 .claude/skills/whatbox-rtorrent/scripts/whatbox.py list                   # human-readable table
python3 .claude/skills/whatbox-rtorrent/scripts/whatbox.py list --json            # machine-readable JSON
python3 .claude/skills/whatbox-rtorrent/scripts/whatbox.py list --view seeding    # filter by rTorrent view

python3 .claude/skills/whatbox-rtorrent/scripts/whatbox.py start  <hash-or-name>  # start a stopped torrent
python3 .claude/skills/whatbox-rtorrent/scripts/whatbox.py stop   <hash-or-name>  # stop (close peer connections)
python3 .claude/skills/whatbox-rtorrent/scripts/whatbox.py pause  <hash-or-name>  # pause (keep connections)
python3 .claude/skills/whatbox-rtorrent/scripts/whatbox.py resume <hash-or-name>  # resume a paused torrent
```

Available views: `main` (default), `started`, `stopped`, `complete`, `incomplete`, `hashing`, `seeding`, `leeching`.

State-control commands take a hash prefix (case-insensitive) or a substring of the torrent name and require a unique match — ambiguous targets list the candidates and exit non-zero.

Example output:

```
HASH      NAME                                                SIZE      %  STATE     RATIO          UP          DN
---------------------------------------------------------------------------------------------------------------------
A1B2C3D4  ubuntu-24.04-desktop-amd64.iso                   5.6G   100.0%  seeding    1.42    12.3K/s         -
E5F6A7B8  Some.Show.S01.1080p.WEB-DL                      28.4G    47.2%  leeching   0.00         -    1.8M/s
```

## How it works

Hits `https://$WHATBOX_HOSTNAME/xmlrpc` (note: `/xmlrpc`, **not** `/RPC2` — Whatbox-specific) with HTTP basic auth, then issues a single `d.multicall2("", "main", "d.hash=", "d.name=", ...)` to pull all torrents in one round-trip. Stdlib `xmlrpc.client` only; no third-party deps.

## Troubleshooting

| Symptom | Cause |
| --- | --- |
| `401 Unauthorized` | Wrong username/password in `.env`. |
| `404 Not Found` | Wrong host, or skill is hitting `/RPC2`. |
| `ExpatError: not well-formed` | Server returned HTML — almost always wrong endpoint path or proxy error page. |
| `connection error: ... gaierror` | DNS — check `WHATBOX_HOSTNAME`. |
| Hangs forever | Network blackhole; the script sets a 30s socket timeout, so a true hang means signal trouble. Ctrl-C and check the host. |

## Reference

Full XML-RPC method catalog (multicall accessors, state-control methods, `load.start` for magnets, numeric quirks like `d.ratio` being `ratio * 1000`) lives in [`references/rtorrent_api.md`](references/rtorrent_api.md). Read that before adding new commands.
