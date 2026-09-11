# Project brain

See skill `project-brain` and template `PROJECT.md.template`.

## Purpose

Avoid rediscovering stack, commands, and decisions every session.

## Auto vs manual

| Action | Who |
|--------|-----|
| Track edited files | `track-edits.py` hook |
| Update stack/commands | Agent after real changes |
| Task progress | Agent + checkpoint skill |
| Architecture diagram | Agent when user approves design |

## Bootstrap

```powershell
Copy-Item "$env:USERPROFILE\cursor-kit\PROJECT.md.template" .\PROJECT.md
# macOS / Linux: cp ~/cursor-kit/PROJECT.md.template ./PROJECT.md
# Or run /setup-project / project-brain
```

Then run `project-brain` skill once to fill from repo manifests.
