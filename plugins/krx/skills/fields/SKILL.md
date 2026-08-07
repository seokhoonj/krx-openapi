---
name: fields
description: "Show the columns a KRX Open API service returns -- the field (column) names of one service, in order -- offline and without a key. Holds no logic of its own -- it calls the krx-openapi package's CLI (`krx fields <group> <name>`) and shows the result to the user. Use it to see what a service returns before fetching it. Trigger phrases: 이 서비스 컬럼, KRX 필드, 무슨 컬럼 오나, what columns does, KRX field schema, what fields does this service return."
---

# krx — a service's fields

Show the columns one KRX service returns, by the readable `group name` pair the Python
client uses. `krx fields <group> <method>` prints the field (column) names in the order
KRX returns them -- `krx fields index kospi` gives `BAS_DD`, `IDX_CLSS`, `IDX_NM`,
`CLSPRC_IDX`, ... It reads a schema **bundled in the krx-openapi package**, so it runs
**offline and needs no API key**.

## Prerequisite

This plugin calls the `krx` CLI, so the package must be installed:

```
pipx install krx-openapi      # or: pip install krx-openapi
```

That puts the `krx` command on PATH. `krx fields` needs **no** `KRX_API_KEY` (it is
offline) -- only the **fetch** skill does.

## Running

```
krx fields <GROUP> <NAME>     # the field (column) names that service returns
```

- `GROUP NAME` is the readable service pair -- `index kospi`, `stock daily`,
  `bond treasury`, ... If you don't have it, use the **list** skill (`krx list`) first.
- `--json` emits JSON instead of the text view.

## Procedure

1. **Have the `group name`.** If the user gave only a concept, use the **list** skill
   (`krx list`) to find the pair first.
2. **Run.**
   ```bash
   krx fields index kospi
   ```
3. **Relay the result.** Show the CLI's stdout -- the column names the fetched rows will
   carry. Offer to hand the same `group name` to the **fetch** skill for the data.
4. **Error handling.** An unknown method exits 2 with `krx: unknown service ...` -- relay
   it and suggest `krx list <group>` to find the right name.

## What this skill does not do

- It does not re-implement the schema (the package ships it); it always calls the CLI.
- It shows column names only -- to list groups and methods use the **list** skill, and to
  fetch a day's data use the **fetch** skill.
