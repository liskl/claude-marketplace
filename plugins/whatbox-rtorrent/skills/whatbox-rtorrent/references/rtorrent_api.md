# Whatbox rTorrent XML-RPC: Wire-Level Reference

Canonical reference for the `whatbox-rtorrent` skill. Sourced from the [Whatbox wiki](https://whatbox.ca/wiki/Using_XMLRPC_with_Python) and the [rakshasa/rtorrent wiki](https://github.com/rakshasa/rtorrent/wiki).

## 1. Endpoint

**Whatbox uses `/xmlrpc`, not `/RPC2`.** Most generic rTorrent guides assume `/RPC2`; that path on Whatbox returns HTML and surfaces as a confusing `xmlrpc.client.ExpatError: not well-formed`.

```
https://<WHATBOX_HOSTNAME>/xmlrpc
```

HTTPS only, port 443. SCGI is reachable only from inside the slot, never from outside.

## 2. Authentication

HTTP Basic Auth with the Whatbox account credentials. `xmlrpc.client.ServerProxy` only supports basic auth via the URL, so credentials get embedded:

```python
url = f"https://{user}:{quote(pw, safe='')}@{host}/xmlrpc"
```

The password **must** be percent-encoded (`urllib.parse.quote(pw, safe="")`) — characters like `@ : / # ? %` and any non-ASCII will otherwise break URL parsing.

- `401 Unauthorized` → bad creds, or unencoded special char in password
- `403 Forbidden` → wrong host, or rTorrent stopped on the slot
- `404 Not Found` → wrong path (probably `/RPC2`)

## 3. Listing torrents

Two valid approaches.

### Preferred: `d.multicall2` (single round-trip)

Signature: `d.multicall2(target, view, accessor1, accessor2, ...)`.

- `target` is `""` (legacy slot id, unused).
- `view` is one of `main`, `started`, `stopped`, `complete`, `incomplete`, `hashing`, `seeding`, `leeching`. Empty string returns nothing — always pass `"main"` for "all torrents."
- Each accessor is a getter command literal ending in `=`.

```python
rows = server.d.multicall2(
    "", "main",
    "d.hash=",            # str, uppercase 40-char SHA1
    "d.name=",            # str
    "d.size_bytes=",      # int
    "d.completed_bytes=", # int
    "d.state=",           # int (0=stopped, 1=started)
    "d.is_active=",       # int (0/1) — NOT a bool
    "d.complete=",        # int (0/1)
    "d.ratio=",           # int — ratio * 1000 (1.5 -> 1500)
    "d.up.rate=",         # int (bytes/sec)
    "d.down.rate=",       # int (bytes/sec)
    "d.message=",         # str (tracker error msg or "")
)
```

Returns a list of lists in accessor order.

### Alternative: `download_list` + per-hash calls

```python
hashes = server.download_list("", "main")
for h in hashes:
    name = server.d.name(h)
```

Simple but N+1 — used only for sanity-checking from a REPL.

## 4. State control

All take the infohash (uppercase hex) as the only arg. Each returns `0` on success.

```python
server.d.start(h)    # start (or resume from stopped)
server.d.stop(h)     # stop (close peer connections; can re-check on next start)
server.d.pause(h)    # pause (keep connections, halt transfer)
server.d.resume(h)   # resume from pause
server.d.close(h)    # close (stronger than stop — frees file handles)
server.d.erase(h)    # remove from rTorrent — does NOT delete files on disk
```

Pause/resume and start/stop are **independent state machines.** A paused torrent is still `is_active=1`; a stopped torrent is not.

## 5. Add a magnet link

`load.start(target, uri, [cmd1, cmd2, ...])`. `target` is `""`. Trailing args are rTorrent commands run against the new download (label, directory, etc.).

```python
server.load.start("", "magnet:?xt=urn:btih:...&dn=...&tr=...")

# With label and custom download dir:
server.load.start(
    "",
    magnet_uri,
    'd.custom1.set="my-label"',
    'd.directory.set="/home/user/files/movies"',
)
```

| Method          | Starts?    | Use when                                    |
| --------------- | ---------- | ------------------------------------------- |
| `load.normal`   | No         | Add stopped, configure before starting      |
| `load.start`    | Yes        | Normal "add and seed" flow                  |
| `load.raw`      | No         | Adding raw bencoded `.torrent` bytes        |
| `load.raw_start`| Yes        | Same as above, started immediately          |

**Returns `0`, not the infohash.** For magnets the hash is unknown until DHT/peer metadata fetch completes — poll `download_list` (~5s) to find the new hash, or compute it from the `xt=urn:btih:` parameter (uppercase the hex; if it's base32, decode and re-hex).

## 6. Stdlib client pattern

Stdlib `xmlrpc.client` only — zero deps. Pattern used in `scripts/whatbox.py`:

```python
import socket, urllib.parse, xmlrpc.client

socket.setdefaulttimeout(30)  # ServerProxy default is None — will hang forever
url = f"https://{user}:{urllib.parse.quote(pw, safe='')}@{host}/xmlrpc"
server = xmlrpc.client.ServerProxy(url, allow_none=True)

# Smoke test — returns rTorrent version like "0.9.8"
print(server.system.client_version())
```

Errors to catch:

- `xmlrpc.client.Fault` — server-side error; has `.faultCode` and `.faultString`.
- `xmlrpc.client.ProtocolError` — HTTP-level; has `.errcode` (401, 403, 404...).
- `xmlrpc.client.ExpatError` — non-XML response; almost always wrong endpoint path.
- `socket.gaierror` / `ConnectionError` / `TimeoutError` — network-level.

## 7. Common pitfalls

- **`/xmlrpc` vs `/RPC2`** — Whatbox = `/xmlrpc`. Self-hosted rtorrent.rc examples use `/RPC2`. Wrong path → `ExpatError` (not 404, because the proxy returns an HTML error page).
- **SCGI vs HTTPS** — Don't reach for `scgi://` libraries; SCGI isn't exposed externally.
- **Numeric fields that look wrong:**
  - `d.ratio` is `int(ratio * 1000)`. Divide by 1000 to display.
  - Sizes / rates are bytes / bytes-per-sec.
  - `d.is_active`, `d.complete`, `d.state` are 0/1 ints, not bools.
  - `d.hash` is uppercase hex; magnet `xt=urn:btih:` infohashes are often lowercase or base32 — normalize before comparing.
- **`load.start` doesn't return the hash** — for magnets it returns `0`. Poll `download_list` if you need the hash back.
- **`socket.setdefaulttimeout(...)` is essential** — `ServerProxy` will hang forever on a stalled connection without it.

## Citations

- https://whatbox.ca/wiki/Using_XMLRPC_with_Python
- https://whatbox.ca/wiki/rTorrent
- https://github.com/rakshasa/rtorrent/wiki/RPC-Setup-XMLRPC
- https://github.com/rakshasa/rtorrent/wiki/User-Guide
