# krx-openapi

[![check](https://github.com/seokhoonj/krx-openapi/actions/workflows/check.yml/badge.svg)](https://github.com/seokhoonj/krx-openapi/actions/workflows/check.yml)
[![PyPI](https://img.shields.io/pypi/v/krx-openapi)](https://pypi.org/project/krx-openapi/)
[![Python](https://img.shields.io/pypi/pyversions/krx-openapi)](https://pypi.org/project/krx-openapi/)
[![License](https://img.shields.io/pypi/l/krx-openapi)](https://github.com/seokhoonj/krx-openapi/blob/main/LICENSE)

**English** | [한국어](https://github.com/seokhoonj/krx-openapi/blob/main/README.md)

Read daily market data from the Korea Exchange **KRX Open API**.

Indices (KRX / KOSPI / KOSDAQ / bond / derivatives), stock daily trades and the
issue master, ETF / ETN / ELW, bonds (treasury / general / small-lot), futures and
options, oil / gold / emissions, and ESG — the **seven official services, 31
endpoints**.

## 1. Install

```bash
pip install krx-openapi
```

Get a free key at <https://openapi.krx.co.kr>. **A key alone is not enough** — each
individual API must be applied for and approved under "서비스 이용".

**Config file (all OSes, recommended)** — `~/.config/krx-openapi/credentials.json`
(`~` is your home folder — Linux `/home/name`, macOS `/Users/name`, Windows `C:\Users\name`):

```json
{ "KRX_API_KEY": "..." }
```

**Environment variable** — macOS/Linux: `export KRX_API_KEY=...` / Windows
PowerShell: `setx KRX_API_KEY "..."`.

## 2. Quick start

```python
from krx_openapi import KRX

krx = KRX()                                     # finds the stored key
rows = krx.index.kospi("20200414")              # KOSPI index series, one day

krx.stock.daily("20200414", market="KOSPI")     # all KOSPI stocks, one day
krx.etp.etf("20200414")                         # ETF daily trades
```

`date` is a `YYYYMMDD` trade date. Rows come back as a `list` of `dict`, so they
frame into a table in one line (pandas is not required).

```python
# pandas
import pandas as pd
pd.DataFrame(rows)

# polars
import polars as pl
pl.DataFrame(rows)
```

## 3. Services

| accessor | services |
|---|---|
| `krx.index` | KRX / KOSPI / KOSDAQ series, bond index, derivatives index (daily) |
| `krx.stock` | KOSPI / KOSDAQ / KONEX daily trades and issue master, warrants (SW/SR) |
| `krx.etp` | ETF / ETN / ELW daily trades |
| `krx.bond` | treasury / general / small-lot bond daily trades |
| `krx.derivatives` | futures / options / stock-futures / stock-options daily trades |
| `krx.commodity` | oil / gold / emissions daily trades |
| `krx.esg` | SRI bonds / ESG index / ESG securities |

Full method tree (every argument `date` = `YYYYMMDD` trade date):

```text
KRX()
├─ index                                       # indices
│   ├─ .krx(date)                              KRX series
│   ├─ .kospi(date)                            KOSPI series
│   ├─ .kosdaq(date)                           KOSDAQ series
│   ├─ .bond(date)                             bond index
│   └─ .derivatives(date)                      derivatives index
├─ stock                                       # stocks
│   ├─ .info(date, market="KOSPI")             issue master (KOSPI/KOSDAQ/KONEX)
│   ├─ .daily(date, market="KOSPI")            daily trades (KOSPI/KOSDAQ/KONEX)
│   ├─ .warrant(date)                          subscription warrant
│   └─ .right(date)                            subscription right
├─ etp                                         # ETP
│   ├─ .etf(date)                              ETF
│   ├─ .etn(date)                              ETN
│   └─ .elw(date)                              ELW
├─ bond                                        # bonds
│   ├─ .treasury(date)                         KTS government-bond market
│   ├─ .general(date)                          general bond market
│   └─ .small_lot(date)                        small-lot bond market
├─ derivatives                                 # derivatives
│   ├─ .futures(date)                          futures (ex-stock)
│   ├─ .options(date)                          options (ex-stock)
│   ├─ .stock_futures(date, market="KOSPI")    stock futures (KOSPI/KOSDAQ)
│   └─ .stock_options(date, market="KOSPI")    stock options (KOSPI/KOSDAQ)
├─ commodity                                   # commodities
│   ├─ .oil(date)                              oil
│   ├─ .gold(date)                             gold
│   └─ .emissions(date)                        emissions
└─ esg                                         # ESG
    ├─ .sri_bond(date)                         SRI bonds
    ├─ .index(date)                            ESG index
    └─ .etp(date)                              ESG securities
```

The bundled offline catalog describes every service without a call:

```python
from krx_openapi import catalog

catalog.groups()                   # ['index', 'stock', ...]
catalog.methods("bond")            # ['treasury', 'general', 'small_lot']
catalog.fields("index", "kospi")   # the columns this service returns
```

## 4. Command line

The command line uses the same names as Python — `krx <group> <method> <date>`
(e.g. `krx index kospi 20200414` == `krx.index.kospi("20200414")`). Run it as `krx`
or `python -m krx_openapi`; add `--json` to any command for JSON.

```bash
# fetch data (the same words as krx.index.kospi("20200414"); needs KRX_API_KEY)
krx index kospi 20200414
krx stock daily 20200414 --market KOSDAQ
krx bond treasury 20200414

# what exists / what columns it returns (offline, no key)
krx list                # every group and its methods
krx list stock          # one group
krx fields index kospi  # the columns this service returns
```

## 5. AI coding agents

- This repo doubles as a plugin marketplace for Claude Code and Codex.
- It ships two skills, `catalog` and `fetch`, each calling the `krx` command
  (catalog = `krx list` / `krx fields`, fetch = `krx <group> <method> <date>`).
- Install the package first (catalog works without a key; fetch needs an API key).

### 5.1 Claude Code

```
/plugin marketplace add seokhoonj/krx-openapi
/plugin install krx@krx-openapi
```

Then ask in plain language ("get today's KOSPI stocks", "what KRX services are there"),
or call a skill directly — `/krx:catalog`, `/krx:fetch index kospi 20200414`.

### 5.2 Codex

```
codex plugin marketplace add seokhoonj/krx-openapi
codex plugin add krx@krx-openapi
```

### 5.3 Without the plugin (symlink)

To use the skills without installing the plugin, symlink them into each agent's
skills directory:

```sh
ln -s "$PWD/plugins/krx/skills/fetch" ~/.claude/skills/fetch   # Claude Code → /fetch
ln -s "$PWD/plugins/krx/skills/fetch" ~/.codex/skills/fetch    # Codex → $krx:fetch
```

Claude Code picks it up immediately; Codex needs a restart.

## 6. Cautions

- **Daily data only** — no same-day / realtime / intraday. A day's data is published
  the next business day at 08:00 KST; weekends, holidays, and pre-update queries
  return empty.
- **Rate limit**: 10,000 calls per key per day (not per IP), reset at midnight; over
  it raises `KRXRateLimitError` (HTTP 429). Excessive traffic can get an IP blocked.
- **Unadjusted prices only** (원주가); no adjusted-price series.
- **Not served by the API**: investor trading, foreign holdings, short selling,
  PER/PBR, ETF constituents, designation status (warnings / halts / management).
- **Terms**: non-commercial use only (personal research / investment); attribute
  "한국거래소 통계정보" and do not redistribute the raw data to third parties. See the
  KRX Open API terms of service.

## 7. Errors

All derive from `KRXError`.

| exception | when |
|---|---|
| `KRXConfigError` | no API key could be resolved (before any request) |
| `KRXAuthError` | key rejected or **service not applied for** (respCode 401) |
| `KRXRateLimitError` | daily call quota exceeded (HTTP 429) |
| `KRXResponseError` | any other vendor error (respCode) |
| `KRXNetworkError` | transport failure / non-JSON response / other HTTP error |

An invalid `market` code raises `ValueError`; an unknown service name raises `KeyError`.

## 8. License

MIT — for this package's code. KRX data itself is governed by the KRX terms above.
