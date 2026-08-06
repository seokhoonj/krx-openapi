---
name: fetch
description: "Fetch one day of KRX market data from the KRX Open API, by the same readable names the Python client uses. Holds no logic of its own -- it calls the krx-openapi package's CLI (`krx <group> <name> <date>`) and shows the result to the user. Needs a group + method (find them with the catalog skill) and a trade date. Trigger phrases: KRX 시세 가져와, KRX 일별 데이터, 코스피 전종목 시세, KRX 지수 조회, 국채 시세, fetch KRX data, KRX daily prices, KOSPI stocks on a date, KRX index for."
---

# krx — fetch one day of a service

Take a KRX service (a `group name` pair, e.g. `index kospi`, `stock daily`) and a
trade date, and print that day's rows. The command reads exactly like the Python
call: `krx.index.kospi("20200414")` is `krx index kospi 20200414`. The request, the
KRX status contract, and parsing live in the krx-openapi package (on PyPI); this
skill is a thin wrapper that calls its CLI and relays the result. A rejected key, an
un-applied service, or a quota error comes back as a one-line `krx: <message>` --
relay it as-is rather than throwing a stack trace.

**One date, not a range.** Every KRX endpoint is a per-date snapshot: one call
returns that whole market on that one day (all stocks, all bonds, ...), not a time
series. For a range, call once per trading day.

## Prerequisite

This plugin calls the `krx` CLI, so the package must be installed and an API key set:

```
pipx install krx-openapi      # or: pip install krx-openapi
export KRX_API_KEY=...         # a free key from https://openapi.krx.co.kr
```

The key can also be stored in `~/.config/krx-openapi/credentials.json` as
`{"KRX_API_KEY": "..."}`. **A key alone is not enough** -- each service must also be
applied for and approved under "서비스 이용" on the KRX account, or the call returns 401.
(The **catalog** skill needs no key at all -- it is offline.)

## Running

```
krx <GROUP> <NAME> <YYYYMMDD> [--market KOSPI|KOSDAQ|KONEX] [--json]
```

- `GROUP NAME` is the readable service pair -- `index kospi`, `stock daily`,
  `bond treasury`, `derivatives futures`, `etp etf`, ... Get it from the **catalog**
  skill (`krx list`).
- The date is a `YYYYMMDD` trade date (a past business day).
- `--market` applies only to `stock daily`, `stock info`, `derivatives stock_futures`,
  and `derivatives stock_options` (KOSPI default; case-insensitive). Other services
  ignore/reject it.
- `--json` emits the full rows; the text view shows an aligned table (first 20 rows)
  and a total count.

## Procedure

1. **Get the `group name`.** If the user gave a concept ("코스피 지수", "국채 시세") but no
   names, use the **catalog** skill first (`krx list`), then come back here.
2. **Pick a valid date.** KRX serves the previous business day's data from 08:00 KST
   the next morning; a weekend, holiday, same-day, or pre-08:00 date returns empty
   (not an error). Default to the last completed trading day.
3. **Run.**
   ```bash
   krx index kospi 20200414
   krx stock daily 20200414 --market KOSDAQ
   ```
4. **Relay the result.** Show the CLI's stdout. You may trim a long table, but keep
   the count line. Use `--json` when the user wants the whole day or machine-readable
   data.
5. **Error handling.** Relay the one-line `krx: <message>` from stderr as-is. Common
   ones:
   - `command not found: krx` -> not installed; point the user at `pipx install krx-openapi`.
   - `no KRX API key ...` -> no key was found (env var and config file both empty).
   - `KRX 401: ...` -> the key was rejected **or the service was not applied for**; tell
     the user to apply for that API under "서비스 이용" and wait for approval.
   - `KRX daily call quota exceeded ...` -> the 10,000-calls-per-key-per-day limit (429);
     wait until midnight KST.
   - An empty table (`(no rows)`) is not an error -- it usually means a non-trading date
     or data not yet published; suggest an earlier business day.

## What this skill does not do

- It does not re-implement fetching or parsing (the package does); it always calls the CLI.
- It returns one day of one service -- to discover the groups, methods, and columns,
  use the **catalog** skill. It cannot return investor trading, short selling, PER/PBR,
  adjusted prices, or intraday data (the KRX Open API does not serve those).
