# router-peek

Read-only command line for a TIM-branded Huawei OptiXstar router (DN8245X6-8X). Each run
logs in, reads one status page, logs out, and prints JSON.

Built for scheduled watchers on a home server: *which device is this MAC?*, *is Wi-Fi still
off?*, *is the line up?*

## Philosophy

- **Read, never write.** It only fetches status pages and never submits a form. The only
  POSTs it sends are login and logout.
- **Wrong data is worse than no data.** Parsing is strict. If the router's pages change
  shape, the call fails (exit 6) instead of guessing.
- **Nothing to install.** Python 3 standard library only. Clone and run.
- **Automate the checks.** The router offers no API. Its web UI is the only way to read
  its state, and that's built for a person clicking. This tool exists to make that state
  scriptable.

## Install

```bash
git clone https://github.com/ermirbeqiraj/router-peek.git && cd router-peek
chmod +x router/router
sudo ln -s "$PWD/router/router" /usr/local/bin/router
```

## Configure

[router.conf](router.conf) holds the router address and describes the two places the login
can come from, without choosing one. Each machine chooses in its own `router.local.conf`, a
gitignored file next to it, by copying one block from [router.conf](router.conf) and removing
the `#` from its settings.

A dev machine uses a credentials file kept outside the repo and readable only by you. A
headless host uses systemd's encrypted credentials, so the login never sits on disk in plain
text: the unit that runs the tool hands it over, and the tool keeps its lock and auth-failed
marker in the unit's state folder. Each block in [router.conf](router.conf) says what it needs.

## Use

```bash
router hosts
router help     # commands, exit codes and rules as JSON
```

| Command | Returns |
|---|---|
| `info` | model, firmware, serial, MACs, uptime, CPU/memory, NAT sessions |
| `hosts` | LAN devices: name, IP, MAC, online state, port, link speed, lease |
| `wifi` | global switch, radios, SSIDs, traffic, associated clients |
| `wan` | IP/PPP connections, addresses, state, uptime, counters |
| `dsl` | sync rates, noise margins, attenuation, error counters |
| `ethernet` | LAN/WAN port link, speed and counters |
| `voip` | phone lines and registration status |
| `mabr` | IPTV multicast ABR status |

Field names and values are the router's own, passed through as strings.

Exit code 0 means stdout is the data. Anything else means stdout is
`{"error": ..., "message": ...}`:

| Code | Meaning |
|---|---|
| 2 | busy: skip this cycle |
| 3 | wrong credentials |
| 4 | blocked: router lockout, or a previous failure is latched |
| 5 | router unreachable or unexpected response |
| 6 | a page changed shape (firmware update?) |

## Caveats

- **A run logs out anyone using the web UI.** The router allows one admin session, and the
  newest login wins.
- **The router locks out after 3 bad logins.** After one rejected login the tool writes an
  `auth-failed` file in its state folder (`.state/`, or the systemd unit's) and refuses to try
  again. Fix the credentials, then delete that file.
- Tested on firmware `AGHDS_1.0.8` only.
