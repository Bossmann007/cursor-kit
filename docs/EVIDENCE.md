# Evidence and limits

What this setup proves, and what it does not. Checked on this Mac, October 2026.

## Verified

| Claim | Evidence |
|---|---|
| Kit tests and secret scan pass | `python -m unittest discover -s tests`, `scripts/secret-scan.sh --all`, CI on every PR |
| ai-memory runs local-only | version 2.6.2, listens on 127.0.0.1:49374, `curl /mcp` returns 405 |
| Hooks are fast | each Claude hook runs in 30 ms or less (one session-start hook, about 250 ms) |
| RTK saves tokens | `rtk gain`: 36.4% saved over 9,581 commands (1.8M tokens) |
| te-filter does NOT reach the model in Claude Code | 2026-10-19: 3,570-token Bash output, ledger said applied (3570 to 43), model got the full output, no footer. Hook removed |
| pstack is the official Claude Code build | `pstack@cursor-plugins` 0.15.25 |

## Not verified

| Claim | How to check |
|---|---|
| The Caveman output style shortens replies | new session; compare reply length |
| `/goal` behavior and limits | read https://code.claude.com/docs/en/goal and try it on a small task |
| sandcastle, Orca, Gemini wiring | not installed or tested |

Rule: a claim moves to "Verified" only with a command and its output.
