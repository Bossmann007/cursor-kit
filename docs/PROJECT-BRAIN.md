# Project brain

`PROJECT.md` is the durable project brain. There is no separate `project-brain`
skill anymore — `/setup-project` fills it from manifests, or the agent refreshes
it when stack/commands change.

Template: `PROJECT.md.template`.

## Purpose

Avoid rediscovering stack, commands, and decisions every session.

## Auto vs manual

| Action | Who |
|--------|-----|
| Track edited files | `track-edits.py` hook |
| Update stack/commands | Agent after real changes |
| Task progress | Agent writes `.cursor/state/checkpoint.json` |
| Architecture diagram | Agent when user approves design |

## Bootstrap

```powershell
Copy-Item "$env:USERPROFILE\cursor-kit\PROJECT.md.template" .\PROJECT.md
# macOS / Linux: cp ~/cursor-kit/PROJECT.md.template ./PROJECT.md
# Or run /setup-project
```

Then fill from repo manifests (or let `/setup-project` do it).
