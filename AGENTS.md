# AGENTS.md

What the tool is, how to use it, commands and exit codes: see [README.md](README.md).
This file covers how the code works and how to extend it.

## Invariants

- **Python 3 standard library only.** No packages, ever.
- **Read-only.** Commands receive a session whose only data method is `get(path)`, which
  refuses `.cgi`. The only POSTs, all in `core/client.py`, are the auth calls
  (`/asp/GetRandCount.asp`, `/login.cgi`, `/logout.cgi`). Every data feed answers GET, even
  the ones the web UI fetches with POST.
- **Strict or nothing.** A record must have exactly as many arguments as its pinned field
  tuple, required sections must be non-empty (`min_count`), and `var()` must find its
  variable. Otherwise `FormatError` → exit 6. Never return partial data.
- **No secrets in output.** Credential positions are pinned as `None`. `jsparse.SECRET` drops
  secret-looking field names as a backstop.
- **One login per run, never retried.** The router locks out after 3 bad logins.

## Layout

```
router.conf              host + secrets source (no secrets)
router/router            entry: dispatch, help, exit codes
router/core/client.py    session: auth, GET-only page access (cached per run), lock, lockout latch
router/core/jsparse.py   records(page, ctor, FIELDS, min_count), var(page, name)
router/core/creds.py     credentials per router.conf; new sources go in load()
router/commands/*.py     one module per command
```

## Reading a command

Each module has: a docstring, whose first line becomes the `router help` text; `PAGE` paths;
positional field tuples in the router's argument order; and `run(session) -> dict`. Pages
embed data as JavaScript, as `new Ctor("..", "..")` calls with `\xNN`-escaped strings, and
`records()` zips each call's arguments onto the tuple.

## Adding a command

1. Find the page: after login, `POST /asp/getMenuArray.asp` lists every menu id → url. Also
   check the `.asp` scripts the page includes or fetches, because data often lives there.
2. Take field names from the page's `function Ctor(...)`, but **pin the argument count of
   the real data.** This firmware defines some constructors twice behind ISP branches
   (`if TTNET2 … else …`), and the data often carries extra trailing arguments. Use `None`
   for unknown or secret positions.
3. Write `router/commands/<name>.py` and register it in `router/commands/__init__.py`.

## Testing against the router

- **Every run logs the user out of the web UI.** Ask before running live.
- **Never test with wrong credentials.** It burns lockout strikes and latches
  `.state/auth-failed`.
- The login token arrives with a UTF-8 BOM, and the client strips it.
- Page responses can contain session tokens. Don't save or commit raw pages.

## Open work

- **Firmware drift flag.** Pin `SoftwareVersion` plus the build hash on page URLs
  (`?c74d1ab6…`) in `.state/`. On change, still return the data but mark it `firmware_changed`.
- **Keyring secrets source.** Add `secret-tool` and/or systemd credentials as `source =`
  options in `creds.py`.
