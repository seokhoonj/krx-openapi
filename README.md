# krx-openapi

[![check](https://github.com/seokhoonj/krx-openapi/actions/workflows/check.yml/badge.svg)](https://github.com/seokhoonj/krx-openapi/actions/workflows/check.yml)
[![PyPI](https://img.shields.io/pypi/v/krx-openapi)](https://pypi.org/project/krx-openapi/)
[![Python](https://img.shields.io/pypi/pyversions/krx-openapi)](https://pypi.org/project/krx-openapi/)
[![License](https://img.shields.io/pypi/l/krx-openapi)](https://github.com/seokhoonj/krx-openapi/blob/main/LICENSE)

[English](https://github.com/seokhoonj/krx-openapi/blob/main/README.en.md) | **한국어**

한국거래소 **KRX Open API**의 일별 시장 데이터를 읽어옵니다.

지수(KRX·KOSPI·KOSDAQ·채권·파생), 주식 일별매매정보와 종목기본정보, ETF·ETN·ELW,
채권(국채·일반·소액), 선물·옵션, 석유·금·배출권, 그리고 ESG까지 — **공식 API가
제공하는 7개 서비스, 31개 항목**을 다룹니다.

## 1. 설치

```bash
pip install krx-openapi
```

무료 인증키는 <https://openapi.krx.co.kr> 에서 발급받습니다. **인증키만으로는 호출이
안 되고**, '서비스 이용' 메뉴에서 사용할 개별 API를 신청하고 승인을 받아야 합니다.

**config 파일 (모든 OS 공통, 권장)** — `~/.config/krx-openapi/credentials.json`
(`~`는 홈 폴더 — Linux `/home/이름`, macOS `/Users/이름`, Windows `C:\Users\이름`):

```json
{ "KRX_API_KEY": "발급받은-키" }
```

**환경변수** — macOS·Linux: `export KRX_API_KEY=...` / Windows PowerShell:
`setx KRX_API_KEY "..."`.

## 2. 빠른 시작

```python
from krx_openapi import KRX

krx = KRX(api_key="your-key")                   # 또는 KRX() — 저장해둔 키(env/config)를 자동으로 찾음

rows = krx.index.kospi("20200414")              # KOSPI 시리즈 지수, 하루치

krx.stock.daily("20200414", market="KOSPI")     # KOSPI 전종목 일별매매정보
krx.etp.etf("20200414")                         # ETF 일별매매정보
```

날짜(`date`)는 `YYYYMMDD` 거래일입니다. 반환은 `dict`의 목록(`list`)이라, 표(DataFrame)로
한 줄에 바뀝니다 (pandas는 필수가 아닙니다).

```python
# pandas
import pandas as pd
pd.DataFrame(rows)

# polars
import polars as pl
pl.DataFrame(rows)
```

## 3. API

| 접근자 | 서비스 |
|---|---|
| `krx.index` | KRX·KOSPI·KOSDAQ 시리즈, 채권지수, 파생상품지수 일별시세 |
| `krx.stock` | KOSPI/KOSDAQ/KONEX 일별매매·종목기본정보, 신주인수권증권·증서 |
| `krx.etp` | ETF·ETN·ELW 일별매매정보 |
| `krx.bond` | 국채전문·일반·소액채권 일별매매정보 |
| `krx.derivatives` | 선물·옵션·주식선물·주식옵션 일별매매정보 |
| `krx.commodity` | 석유·금·배출권 일별매매정보 |
| `krx.esg` | 사회책임투자채권·ESG 지수·ESG 증권상품 |

전체 메서드 (모든 인자 `date` = `YYYYMMDD` 거래일):

```text
KRX()
├─ index                                       # 지수
│   ├─ .krx(date)                              KRX 시리즈 일별시세
│   ├─ .kospi(date)                            KOSPI 시리즈 일별시세
│   ├─ .kosdaq(date)                           KOSDAQ 시리즈 일별시세
│   ├─ .bond(date)                             채권지수 시세
│   └─ .derivatives(date)                      파생상품지수 시세
├─ stock                                       # 주식
│   ├─ .info(date, market="KOSPI")             종목기본정보 (KOSPI/KOSDAQ/KONEX)
│   ├─ .daily(date, market="KOSPI")            일별매매정보 (KOSPI/KOSDAQ/KONEX)
│   ├─ .warrant(date)                          신주인수권증권
│   └─ .right(date)                            신주인수권증서
├─ etp                                         # 증권상품
│   ├─ .etf(date)                              ETF
│   ├─ .etn(date)                              ETN
│   └─ .elw(date)                              ELW
├─ bond                                        # 채권
│   ├─ .treasury(date)                         국채전문유통시장
│   ├─ .general(date)                          일반채권시장
│   └─ .small_lot(date)                        소액채권시장
├─ derivatives                                 # 파생상품
│   ├─ .futures(date)                          선물 (주식선물外)
│   ├─ .options(date)                          옵션 (주식옵션外)
│   ├─ .stock_futures(date, market="KOSPI")    주식선물 (KOSPI/KOSDAQ)
│   └─ .stock_options(date, market="KOSPI")    주식옵션 (KOSPI/KOSDAQ)
├─ commodity                                   # 일반상품
│   ├─ .oil(date)                              석유시장
│   ├─ .gold(date)                             금시장
│   └─ .emissions(date)                        배출권시장
└─ esg                                         # ESG
    ├─ .sri_bond(date)                         사회책임투자채권
    ├─ .index(date)                            ESG 지수
    └─ .etp(date)                              ESG 증권상품
```

어떤 서비스에 어떤 필드가 오는지는 네트워크 없이 오프라인으로 확인할 수 있습니다.

```python
from krx_openapi import catalog

catalog.groups()                  # ['index', 'stock', ...]
catalog.methods("bond")           # ['treasury', 'general', 'small_lot']
catalog.fields("index", "kospi")  # 이 서비스가 돌려주는 필드명 (컬럼)
```

## 4. 커맨드라인

명령줄은 세 명령 `list` · `fields` · `fetch`를 씁니다. `list`·`fields`는 오프라인(키
불필요)으로 뭐가 있고 어떤 컬럼이 오는지 훑고, `fetch`는 하루치 데이터를 가져옵니다 —
`krx fetch <그룹> <메서드> <날짜>` (예: `krx fetch index kospi 20200414` =
`krx.index.kospi("20200414")`). 명령은 `krx` 또는 `python -m krx_openapi`로 실행하고,
어디에 `--json`을 붙이면 JSON으로 나옵니다.

```bash
# 무슨 서비스가 있나 / 어떤 컬럼이 오나 (오프라인, 키 불필요)
krx list                      # 전체 그룹·메서드
krx list stock                # 한 그룹만
krx fields index kospi        # 이 서비스가 돌려주는 컬럼

# 데이터 조회 (KRX_API_KEY 필요)
krx fetch index kospi 20200414
krx fetch stock daily 20200414 --market KOSDAQ
krx fetch bond treasury 20200414
```

## 5. AI 코딩 에이전트에서 사용

- 이 저장소는 Claude Code·Codex용 플러그인 마켓플레이스도 겸합니다.
- `list`·`fields`·`fetch` 스킬을 제공하며, 각각 같은 이름의 `krx` 명령을 호출합니다
  (`krx list`, `krx fields <그룹> <이름>`, `krx fetch <그룹> <이름> <날짜>`).
- 먼저 위에서 패키지를 설치하세요 (`list`·`fields`는 키 없이, `fetch`는 API 키가 필요합니다).

### 5.1 Claude Code

Claude Code 채팅창에서 마켓플레이스를 추가하고 설치합니다:

```
/plugin marketplace add seokhoonj/krx-openapi
/plugin install krx@krx-openapi
```

설치 후 평범하게 물어보거나("코스피 전종목 시세 가져와", "무슨 KRX 서비스 있어"), 스킬을
직접 부르세요 — `/krx:list`, `/krx:fields index kospi`, `/krx:fetch index kospi 20200414`.

### 5.2 Codex

터미널에서 마켓플레이스를 추가하고 설치합니다:

```
codex plugin marketplace add seokhoonj/krx-openapi
codex plugin add krx@krx-openapi
```

### 5.3 플러그인 없이 (symlink)

플러그인으로 설치하지 않고 쓰려면, 스킬을 각 에이전트의 스킬 디렉터리에 symlink합니다.

```sh
for s in list fields fetch; do
  ln -s "$PWD/plugins/krx/skills/$s" ~/.claude/skills/$s   # Claude Code → /$s
  ln -s "$PWD/plugins/krx/skills/$s" ~/.codex/skills/$s    # Codex → $krx:$s
done
```

Claude Code는 바로 인식하고, Codex는 재시작해야 로딩됩니다.

## 6. 주의사항

- **일별 데이터만.** 당일·실시간·장중 데이터는 없습니다. 전일 데이터가 **다음 영업일
  오전 8시**에 갱신됩니다. 주말·공휴일, 갱신 전 조회는 빈 결과입니다.
- **호출 한도**: 인증키당 **하루 10,000회**(IP 아님, 자정 리셋). 초과 시
  `KRXRateLimitError`(HTTP 429). 과도한 호출은 IP 차단 사유가 됩니다.
- **단순주가(원주가)만** 제공합니다. 수정주가는 없습니다.
- **API 미제공 데이터**: 투자자별 거래실적, 외국인 보유량, 공매도, PER/PBR,
  ETF 구성종목(PDF), 지정내역(투자경고·거래정지·관리종목) 등은 제공되지 않습니다.
- **이용약관**: 비상업적 목적(개인 연구·투자)만 허용됩니다. 가공하여 표출할 때는 **출처
  "한국거래소 통계정보"**를 표기하고, 원천 데이터를 제3자에게 재배포할 수 없습니다.
  자세한 내용은 KRX Open API 이용약관을 확인하세요.

## 7. 에러

모든 에러는 `KRXError`를 상속합니다.

| 예외 | 언제 |
|---|---|
| `KRXConfigError` | 인증키를 찾을 수 없음 (요청 전) |
| `KRXAuthError` | 키 거부 또는 **미신청 서비스** (respCode 401) |
| `KRXRateLimitError` | 일일 호출 한도 초과 (HTTP 429) |
| `KRXResponseError` | 그 밖의 벤더 에러 (respCode) |
| `KRXNetworkError` | 전송 실패·비-JSON 응답·기타 HTTP 에러 |

잘못된 `market` 코드는 `ValueError`, 모르는 서비스 이름은 `KeyError`입니다.

## 8. 라이선스

[MIT](LICENSE). 이 패키지의 코드에 대한 라이선스이며, KRX 데이터 자체의 이용 조건은 위 KRX
이용약관을 따릅니다.
