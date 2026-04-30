#!/usr/bin/env python3
"""Whatbox rTorrent XML-RPC client. Phase 1: list torrents."""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import urllib.parse
import xmlrpc.client
from pathlib import Path

ENV_KEYS = ("WHATBOX_USERNAME", "WHATBOX_PASSWORD", "WHATBOX_HOSTNAME")
DEFAULT_TIMEOUT = 30

LIST_ACCESSORS = (
    "d.hash=",
    "d.name=",
    "d.size_bytes=",
    "d.completed_bytes=",
    "d.state=",
    "d.is_active=",
    "d.complete=",
    "d.ratio=",
    "d.up.rate=",
    "d.down.rate=",
    "d.message=",
)
LIST_FIELDS = (
    "hash", "name", "size_bytes", "completed_bytes",
    "state", "is_active", "complete",
    "ratio", "up_rate", "down_rate", "message",
)


def load_env(path: Path) -> dict[str, str]:
    """Resolve creds from process env first, falling back to a .env file.

    Process env always wins; the .env file is optional if everything is already
    exported. Missing-key error names whichever sources were actually checked.
    """
    file_env: dict[str, str] = {}
    if path.exists():
        for raw in path.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            file_env[key.strip()] = val.strip().strip('"').strip("'")

    env = {k: os.environ.get(k) or file_env.get(k, "") for k in ENV_KEYS}
    missing = [k for k in ENV_KEYS if not env[k]]
    if missing:
        sources = "environment" if not path.exists() else f"environment or {path}"
        die(f"missing {', '.join(missing)} in {sources}")
    return env


def make_server(env: dict[str, str]) -> xmlrpc.client.ServerProxy:
    socket.setdefaulttimeout(DEFAULT_TIMEOUT)
    user = urllib.parse.quote(env["WHATBOX_USERNAME"], safe="")
    pw = urllib.parse.quote(env["WHATBOX_PASSWORD"], safe="")
    host = env["WHATBOX_HOSTNAME"]
    url = f"https://{user}:{pw}@{host}/xmlrpc"
    return xmlrpc.client.ServerProxy(url, allow_none=True)


def fmt_bytes(n: int) -> str:
    n = float(n)
    for unit in ("B", "K", "M", "G", "T"):
        if n < 1024 or unit == "T":
            return f"{n:6.1f}{unit}"
        n /= 1024
    return f"{n:.1f}T"


def fmt_rate(n: int) -> str:
    return fmt_bytes(n) + "/s" if n else "       -"


def state_label(state: int, is_active: int, complete: int) -> str:
    if not state:
        return "stopped"
    if not is_active:
        return "paused"
    return "seeding" if complete else "leeching"


def resolve_target(server: xmlrpc.client.ServerProxy, query: str) -> tuple[str, str]:
    """Match a hash prefix (case-insensitive) or a name substring.

    Returns (hash, name) for the unique match; dies if zero or multiple matches.
    """
    rows = server.d.multicall2("", "main", "d.hash=", "d.name=")
    q = query.lower()
    matches = [(h, n) for h, n in rows if h.lower().startswith(q) or q in n.lower()]
    if not matches:
        die(f"no torrent matched {query!r}")
    if len(matches) > 1:
        lines = [f"{query!r} matched {len(matches)} torrents:"]
        lines.extend(f"  {h[:8]}  {n}" for h, n in matches)
        die("\n".join(lines))
    return matches[0]


def _control(server, args, method_name, verb):
    h, name = resolve_target(server, args.target)
    getattr(server.d, method_name)(h)
    print(f"{verb}: {h[:8]}  {name}")
    return 0


def cmd_start(server, args):  return _control(server, args, "start",  "started")
def cmd_stop(server, args):   return _control(server, args, "stop",   "stopped")
def cmd_pause(server, args):  return _control(server, args, "pause",  "paused")
def cmd_resume(server, args): return _control(server, args, "resume", "resumed")


def cmd_list(server: xmlrpc.client.ServerProxy, args: argparse.Namespace) -> int:
    rows = server.d.multicall2("", args.view, *LIST_ACCESSORS)
    records = [dict(zip(LIST_FIELDS, r)) for r in rows]

    if args.json:
        json.dump(records, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0

    if not records:
        print(f"(no torrents in view '{args.view}')")
        return 0

    name_w = min(max((len(r["name"]) for r in records), default=4), 50)
    header = f"{'HASH':<8}  {'NAME':<{name_w}}  {'SIZE':>7}  {'%':>5}  {'STATE':<8}  {'RATIO':>6}  {'UP':>10}  {'DN':>10}"
    print(header)
    print("-" * len(header))
    for r in records:
        size = r["size_bytes"]
        done = r["completed_bytes"]
        pct = (done / size * 100) if size else 0.0
        name = r["name"]
        if len(name) > name_w:
            name = name[: name_w - 1] + "…"
        print(
            f"{r['hash'][:8]:<8}  "
            f"{name:<{name_w}}  "
            f"{fmt_bytes(size):>7}  "
            f"{pct:>4.1f}%  "
            f"{state_label(r['state'], r['is_active'], r['complete']):<8}  "
            f"{r['ratio']/1000:>6.2f}  "
            f"{fmt_rate(r['up_rate']):>10}  "
            f"{fmt_rate(r['down_rate']):>10}"
        )
        if r["message"]:
            print(f"           ! {r['message']}")
    return 0


def die(msg: str, code: int = 1) -> "None":
    print(f"whatbox: {msg}", file=sys.stderr)
    sys.exit(code)


def handle_xmlrpc_errors(fn):
    def wrapper(*a, **kw):
        try:
            return fn(*a, **kw)
        except xmlrpc.client.ProtocolError as e:
            if e.errcode == 401:
                die("401 Unauthorized — check WHATBOX_USERNAME / WHATBOX_PASSWORD "
                    "(special chars in the password are URL-encoded automatically; "
                    "verify the raw value in .env is correct)")
            if e.errcode == 404:
                die("404 Not Found — Whatbox uses /xmlrpc, not /RPC2. "
                    "Also confirm WHATBOX_HOSTNAME points at the slot's rTorrent host.")
            die(f"HTTP {e.errcode} {e.errmsg} from {e.url}")
        except xmlrpc.client.Fault as e:
            die(f"rTorrent fault {e.faultCode}: {e.faultString}")
        except xmlrpc.client.ExpatError:
            die("server returned non-XML — almost always a wrong endpoint path "
                "(should be /xmlrpc) or an HTML error page from the proxy.")
        except (socket.gaierror, ConnectionError, TimeoutError, OSError) as e:
            die(f"connection error: {e} (check WHATBOX_HOSTNAME and your network)")
    return wrapper


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="whatbox", description=__doc__)
    parser.add_argument(
        "--env-file", type=Path, default=Path(".env"),
        help="path to .env (default: ./.env)",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="list torrents")
    p_list.add_argument(
        "--view", default="main",
        help="rTorrent view: main, started, stopped, complete, incomplete, "
             "hashing, seeding, leeching (default: main)",
    )
    p_list.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    p_list.set_defaults(func=cmd_list)

    for verb, fn, helptxt in (
        ("start",  cmd_start,  "start a stopped torrent"),
        ("stop",   cmd_stop,   "stop a torrent (close peer connections)"),
        ("pause",  cmd_pause,  "pause a torrent (keep connections)"),
        ("resume", cmd_resume, "resume a paused torrent"),
    ):
        p = sub.add_parser(verb, help=helptxt)
        p.add_argument("target", help="hash prefix or substring of the torrent name (must match exactly one)")
        p.set_defaults(func=fn)

    args = parser.parse_args(argv)
    env = load_env(args.env_file)
    server = make_server(env)
    return handle_xmlrpc_errors(args.func)(server, args)


if __name__ == "__main__":
    sys.exit(main())
