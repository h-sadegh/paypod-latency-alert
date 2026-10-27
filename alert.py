#!/usr/bin/env python3
"""Hourly latency alert: queries self-hosted Sentry for p95 latency of
high-traffic transactions in the last hour and sends a Telegram message
when p95 crosses the threshold.

Required environment variables:
  SENTRY_URL     e.g. https://sentry.example.com
  SENTRY_ORG     organization slug (e.g. sentry)
  SENTRY_TOKEN   Sentry auth token (org:read, project:read, event:read)
  BOT_TOKEN      Telegram bot token from @BotFather
  CHAT_ID        Telegram chat id from @userinfobot

Optional:
  P95_THRESHOLD_MS   default 10000
  MIN_COUNT          min events in window to be considered high-traffic (default 50)
"""

import json
import os
import sys
import urllib.parse
import urllib.request

SENTRY_URL = os.environ["SENTRY_URL"].rstrip("/")
SENTRY_ORG = os.environ["SENTRY_ORG"]
SENTRY_TOKEN = os.environ["SENTRY_TOKEN"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

P95_THRESHOLD_MS = float(os.environ.get("P95_THRESHOLD_MS", "10000"))
MIN_COUNT = int(os.environ.get("MIN_COUNT", "50"))
WINDOW = os.environ.get("WINDOW", "1h")


def query_sentry():
    params = urllib.parse.urlencode(
        {
            "dataset": "transactions",
            "field": [
                "transaction",
                "project",
                "count()",
                "p50(transaction.duration)",
                "p95(transaction.duration)",
            ],
            "per_page": 50,
            "sort": "-p95(transaction.duration)",
            "statsPeriod": WINDOW,
            "allowAggregateConditions": "0",
        },
        doseq=True,
    )
    url = f"{SENTRY_URL}/api/0/organizations/{SENTRY_ORG}/events/?{params}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {SENTRY_TOKEN}",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp).get("data", [])


def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = json.dumps(
        {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    ).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if not body.get("ok"):
        raise RuntimeError(f"Telegram API error: {body}")


def fmt_ms(ms):
    if ms >= 1000:
        return f"{ms / 1000:.1f}s"
    return f"{ms:.0f}ms"


def main():
    rows = query_sentry()
    offenders = [
        r
        for r in rows
        if (r.get("p95(transaction.duration)") or 0) > P95_THRESHOLD_MS
        and (r.get("count()") or 0) >= MIN_COUNT
    ]
    if not offenders:
        print(f"OK: {len(rows)} transactions checked, none above threshold.")
        return

    lines = [
        f"\U0001F534 <b>Latency Alert</b> — p95 &gt; {fmt_ms(P95_THRESHOLD_MS)} (last {WINDOW})",
        ""
    ]
    for r in offenders[:10]:
        lines.append(
            f"• <b>{r['transaction']}</b> ({r['project']}) "
            f"p95={fmt_ms(r['p95(transaction.duration)'])} "
            f"p50={fmt_ms(r['p50(transaction.duration)'])} "
            f"n={int(r['count()'])}"
        )
    send_telegram("\n".join(lines))
    print(f"ALERT sent: {len(offenders)} transactions above threshold.")


if __name__ == "__main__":
    sys.exit(main())
