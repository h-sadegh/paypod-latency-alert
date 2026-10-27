# paypod-latency-alert

hourly p95 latency alert for paypod apps, reading a self-hosted Sentry via its API
and notifying a Telegram chat when p95 of any high-traffic page exceeds the threshold.

## one-time setup

1. create a **private** github repo named `paypod-latency-alert` and push this folder to it.
2. in the repo: **settings → secrets and variables → actions → new repository secret**, add:

   | secret | value |
   |---|---|
   | `SENTRY_URL` | `https://logger.fnpy.ir` |
   | `SENTRY_ORG` | `sentry` |
   | `SENTRY_TOKEN` | an auth token from your sentry (see below) |
   | `BOT_TOKEN` | the token @BotFather gave you |
   | `CHAT_ID` | your numeric telegram chat id |

3. sentry token: in sentry go to **settings → auth tokens → create new token**,
   scope `org:read` + `project:read` (or `event:read`).
4. in the repo: **actions tab → enable the `latency-alert` workflow**, then click
   **run workflow** once to test. check the run log; if a page is slow you get a
   telegram message, otherwise the run just logs the checked pages.

## tuning

- threshold and minimum traffic are env vars in `.github/workflows/alert.yml`
  (`P95_THRESHOLD_MS`, `MIN_COUNT`).
