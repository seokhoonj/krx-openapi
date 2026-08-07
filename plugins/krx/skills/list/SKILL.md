---
name: list
description: "List the KRX Open API's services -- the groups and the readable method names each is called by -- offline and without a key. Holds no logic of its own -- it calls the krx-openapi package's CLI (`krx list`) and shows the result to the user. Use this to turn a concept (코스피 지수, 국채) into the `group name` pair the fetch skill needs. Trigger phrases: KRX 서비스 목록, 무슨 KRX 데이터 있어, KRX 뭐 조회 가능, list KRX services, what KRX data is there, KRX groups and methods."
---

# krx — list services

Show what the KRX Open API offers and how to call it, in the same readable names the
Python client uses. `krx list` prints the accessor tree: every group and the methods
under it, one `group name` per line -- `index kospi`, `stock daily`, `bond treasury`,
... exactly the words the **fetch** skill (and the Python client) take. It reads a
catalog **bundled in the krx-openapi package**, so it runs **offline and needs no API
key**. There are no raw api_ids to memorize; the `group name` pair is the whole address.

## Prerequisite

This plugin calls the `krx` CLI, so the package must be installed:

```
pipx install krx-openapi      # or: pip install krx-openapi
```

That puts the `krx` command on PATH. `krx list` needs **no** `KRX_API_KEY` (it is
offline) -- only the **fetch** skill does.

## Running

```
krx list [GROUP]              # all groups and their methods, or one group's methods
```

- `krx list` prints every group (`index`, `stock`, `etp`, `bond`, `derivatives`,
  `commodity`, `esg`) and the methods under it.
- `krx list stock` narrows to one group.
- `--json` emits JSON instead of the text view.

## Procedure

1. **From a concept, find the `group name`.** Run `krx list` and scan for the matching
   group + method (e.g. "코스피 지수" -> `index kospi`; "국채" -> `bond treasury`;
   "ETF" -> `etp etf`).
2. **Run.**
   ```bash
   krx list
   krx list stock
   ```
3. **Relay the result.** Show the CLI's stdout. When the goal is one service, point out
   the `group name` the user needs, then offer to hand it to the **fetch** skill (or to
   the **fields** skill to see its columns first).
4. **Error handling.** An unknown group is rejected by the CLI with a usage message
   (exit 2) -- relay it.

## What this skill does not do

- It does not re-implement the catalog (the package ships it); it always calls the CLI.
- It lists groups and methods only -- for a service's columns use the **fields** skill,
  and to fetch a day's data use the **fetch** skill.
