# Codex Log Viewer

A small local web viewer for Markdown conversation logs exported from Codex or other chat tools.

It is designed for long technical conversations where scrolling through the raw terminal log is inconvenient.

## Features

- Local-only web server
- Markdown log rendering
- Section table of contents
- Search
- Expand/collapse all sections
- Per-section collapse
- Light/dark mode via system preference
- No external Python dependencies

## Quick Start

```powershell
python .\codex_log_viewer.py --log .\sample_log.md
```

Then open:

```text
http://127.0.0.1:8765
```

By default, the browser opens automatically.

## Use Your Own Log

```powershell
python .\codex_log_viewer.py --log "C:\path\to\conversation_log.md"
```

If port `8765` is occupied, the viewer automatically tries the next available port.

## Options

```text
--log PATH     Markdown log file to view
--port PORT    Preferred local port, default 8765
--no-open      Do not open the browser automatically
```

## Markdown Format

The viewer works best with logs that use:

```markdown
## 1. Topic

**User**

Message text

**Assistant**

Reply text
```

It also supports code blocks, inline code, bullet lists, and simple links.

## Privacy

This app serves files from your local machine only. Do not commit private conversation logs, trading records, secrets, or `.env` files to a public repository.
