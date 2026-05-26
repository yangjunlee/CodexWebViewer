$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogPath = if ($args.Count -gt 0) { $args[0] } else { "$Root\sample_log.md" }
Set-Location $Root
python "$Root\codex_log_viewer.py" --log $LogPath
