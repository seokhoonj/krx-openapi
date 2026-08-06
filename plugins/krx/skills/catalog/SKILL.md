---
name: catalog
description: "Browse the KRX Open API's services and the columns they return, offline and without a key. Holds no logic of its own -- it calls the krx-openapi package's CLI (`krx list` / `krx fields`) and shows the result to the user. Use this to find the readable `group name` a service is called by (e.g. index kospi, bond treasury) and to see what fields it returns. Trigger phrases: KRX 서비스 목록, 무슨 KRX 데이터 있어, 이 서비스 컬럼, KRX 필드, list KRX services, what KRX data, what columns does, KRX field schema."
---

# krx — catalog (list services and fields)

Discover what the KRX Open API offers and how to call it, in the same readable names
the Python client uses. `krx list` shows the accessor tree (groups and their
methods -- `index kospi`, `stock daily`, `bond treasury`, ...); `krx fields <group>
<name>` shows the columns one service returns. Both read a catalog **bundled in the
krx-openapi package**, so they run **offline and need no API key** -- this is the
skill to reach for first, before the key-gated **fetch**. There are no raw api_ids
to memorize; the `group name` pair is the whole address.

## Prerequisite

This plugin calls the `krx` CLI, so the package must be installed:

```
pipx install krx-openapi      # or: pip install krx-openapi
```

That puts the `krx` command on PATH. `list` and `fields` need **no** `KRX_API_KEY`
(they are offline) -- only the **fetch** skill does.

## Running

```
krx list [GROUP]              # all groups and their methods, or one group's methods
krx fields <GROUP> <NAME>     # the field (column) names that service returns
```

- `krx list` prints every group (`index`, `stock`, `etp`, `bond`, `derivatives`,
  `commodity`, `esg`) and the methods under it, one `group name` per line -- exactly
  the words the **fetch** skill (and the Python client) take.
- `krx list stock` narrows to one group.
- `krx fields index kospi` prints the columns that service returns (e.g. `BAS_DD`,
  `IDX_NM`, `CLSPRC_IDX`, ...).
- `--json` on either emits JSON instead of the text view.

## Procedure

1. **From a concept, find the `group name`.** Run `krx list` and scan for the
   matching group + method (e.g. "코스피 지수" -> `index kospi`; "국채" -> `bond
   treasury`; "ETF" -> `etp etf`).
2. **Run.**
   ```bash
   krx list
   krx fields index kospi
   ```
3. **Relay the result.** Show the CLI's stdout. When the goal is one service, point
   out the `group name` the user needs, then offer to hand it to the **fetch** skill.
4. **Error handling.** An unknown group is rejected by the CLI with a usage message
   (exit 2); an unknown method to `krx fields` exits 2 with `krx: unknown service ...`
   -- relay it and suggest `krx list <group>` to find the right name.

## What this skill does not do

- It does not re-implement the catalog (the package ships it); it always calls the CLI.
- It lists services and columns only -- to fetch a day's data, use the **fetch**
  skill (which needs a key and an approved service).
