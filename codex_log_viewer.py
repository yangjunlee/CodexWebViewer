from __future__ import annotations

import argparse
import html
import json
import re
import socket
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DEFAULT_LOG = ROOT / "conversation_log.md"


def read_log(path: Path) -> str:
    if not path.exists():
        return f"# Log file not found\n\nExpected: `{path}`"
    return path.read_text(encoding="utf-8")


def parse_sections(markdown: str) -> list[dict[str, str]]:
    lines = markdown.splitlines()
    sections: list[dict[str, str]] = []
    title = "Overview"
    current: list[str] = []
    for line in lines:
        if line.startswith("## "):
            if current:
                sections.append({"title": title, "markdown": "\n".join(current).strip()})
                current = []
            title = line[3:].strip()
        else:
            current.append(line)
    if current or not sections:
        sections.append({"title": title, "markdown": "\n".join(current).strip()})
    return sections


def inline_markdown(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<a href='\2'>\1</a>", escaped)
    return escaped


def markdown_to_html(markdown: str) -> str:
    out: list[str] = []
    para: list[str] = []
    code_lines: list[str] = []
    in_code = False
    in_list = False

    def flush_para() -> None:
        nonlocal para
        if para:
            out.append("<p>" + "<br>".join(inline_markdown(x) for x in para) + "</p>")
            para = []

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                out.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                code_lines = []
                in_code = False
            else:
                flush_para()
                close_list()
                in_code = True
            continue
        if in_code:
            code_lines.append(line)
            continue
        if not line.strip():
            flush_para()
            close_list()
            continue
        if line.startswith("# "):
            flush_para()
            close_list()
            out.append(f"<h1>{inline_markdown(line[2:].strip())}</h1>")
        elif line.startswith("### "):
            flush_para()
            close_list()
            out.append(f"<h3>{inline_markdown(line[4:].strip())}</h3>")
        elif line.startswith("**") and line.endswith("**") and len(line) > 4:
            flush_para()
            close_list()
            out.append(f"<div class='speaker'>{inline_markdown(line.strip('*'))}</div>")
        elif line.startswith("- "):
            flush_para()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline_markdown(line[2:].strip())}</li>")
        elif re.match(r"^\d+\.\s+", line):
            flush_para()
            close_list()
            text = re.sub(r"^\d+\.\s+", "", line)
            out.append(f"<p class='numbered'>{inline_markdown(text)}</p>")
        elif line == "---":
            flush_para()
            close_list()
            out.append("<hr>")
        else:
            para.append(line)
    flush_para()
    close_list()
    if in_code:
        out.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
    return "\n".join(out)


def build_payload(path: Path) -> dict[str, object]:
    markdown = read_log(path)
    sections = []
    for idx, section in enumerate(parse_sections(markdown)):
        sections.append(
            {
                "id": f"section-{idx}",
                "title": section["title"],
                "html": markdown_to_html(section["markdown"]),
                "text": re.sub(r"\s+", " ", section["markdown"]).strip(),
            }
        )
    return {"path": str(path), "sections": sections}


APP_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Codex Log Viewer</title>
  <style>
    :root { color-scheme: light dark; --bg:#f5f6f8; --panel:#fff; --text:#202124; --muted:#6b7280; --border:#e5e7eb; --accent:#2563eb; --code:#f1f5f9; --speaker:#eef2ff; }
    @media (prefers-color-scheme: dark) { :root { --bg:#111318; --panel:#181b22; --text:#e5e7eb; --muted:#9ca3af; --border:#2b303b; --accent:#7aa2ff; --code:#10141c; --speaker:#20283a; } }
    * { box-sizing: border-box; }
    body { margin:0; font-family:Arial, "Malgun Gothic", sans-serif; background:var(--bg); color:var(--text); line-height:1.55; }
    .layout { display:grid; grid-template-columns:320px minmax(0,1fr); min-height:100vh; }
    aside { position:sticky; top:0; height:100vh; overflow:auto; border-right:1px solid var(--border); background:var(--panel); padding:18px; }
    main { padding:28px; max-width:1120px; width:100%; }
    h1 { font-size:22px; margin:0 0 12px; }
    .path { color:var(--muted); font-size:12px; word-break:break-all; margin-bottom:14px; }
    .search { width:100%; padding:10px 11px; border:1px solid var(--border); border-radius:6px; background:transparent; color:var(--text); margin-bottom:12px; font-size:14px; }
    .controls { display:flex; gap:8px; margin-bottom:14px; }
    button { border:1px solid var(--border); border-radius:6px; background:transparent; color:var(--text); padding:7px 9px; cursor:pointer; font-size:12px; }
    button:hover { border-color:var(--accent); }
    nav a { display:block; color:var(--text); text-decoration:none; padding:7px 8px; border-radius:5px; font-size:13px; margin-bottom:3px; }
    nav a:hover { background:var(--speaker); color:var(--accent); }
    .section { background:var(--panel); border:1px solid var(--border); border-radius:8px; margin-bottom:18px; overflow:hidden; }
    .section-header { display:flex; align-items:center; justify-content:space-between; gap:12px; padding:14px 16px; border-bottom:1px solid var(--border); cursor:pointer; }
    .section-header h2 { font-size:18px; margin:0; }
    .section-body { padding:16px 18px 20px; }
    .section.collapsed .section-body { display:none; }
    .speaker { display:inline-block; background:var(--speaker); border:1px solid var(--border); border-radius:5px; padding:4px 8px; font-weight:700; margin:12px 0 4px; }
    p { margin:9px 0; } ul { margin:8px 0 12px 22px; padding:0; } li { margin:4px 0; }
    pre { background:var(--code); border:1px solid var(--border); border-radius:7px; overflow:auto; padding:12px; font-size:13px; }
    code { background:var(--code); border-radius:4px; padding:1px 4px; font-family:Consolas, monospace; }
    pre code { padding:0; background:transparent; }
    hr { border:0; border-top:1px solid var(--border); margin:18px 0; }
    mark { background:#fde68a; color:#111827; padding:0 2px; border-radius:2px; }
    .hidden { display:none; }
    @media (max-width:860px) { .layout { grid-template-columns:1fr; } aside { position:relative; height:auto; } main { padding:16px; } }
  </style>
</head>
<body>
  <div class="layout">
    <aside>
      <h1>Codex Log Viewer</h1>
      <div class="path" id="path"></div>
      <input class="search" id="search" placeholder="Search..." autocomplete="off">
      <div class="controls"><button id="expand">Expand all</button><button id="collapse">Collapse all</button></div>
      <nav id="nav"></nav>
    </aside>
    <main id="content"></main>
  </div>
  <script>
    const payload = __PAYLOAD__;
    const nav = document.getElementById("nav");
    const content = document.getElementById("content");
    const search = document.getElementById("search");
    document.getElementById("path").textContent = payload.path;
    function escapeRegExp(value) { return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
    function highlight(source, query) {
      if (!query) return source;
      return source.replace(new RegExp(`(${escapeRegExp(query)})`, "gi"), "<mark>$1</mark>");
    }
    function render(query = "") {
      nav.innerHTML = ""; content.innerHTML = "";
      const q = query.trim().toLowerCase();
      payload.sections.forEach(section => {
        const hit = !q || section.title.toLowerCase().includes(q) || section.text.toLowerCase().includes(q);
        const a = document.createElement("a");
        a.href = "#" + section.id; a.textContent = section.title; a.className = hit ? "" : "hidden"; nav.appendChild(a);
        const article = document.createElement("article");
        article.className = "section" + (hit ? "" : " hidden"); article.id = section.id;
        article.innerHTML = `<div class="section-header"><h2>${section.title}</h2><button type="button">Collapse</button></div><div class="section-body">${highlight(section.html, query.trim())}</div>`;
        article.querySelector(".section-header").addEventListener("click", event => {
          if (event.target.tagName === "A") return;
          article.classList.toggle("collapsed");
          article.querySelector("button").textContent = article.classList.contains("collapsed") ? "Expand" : "Collapse";
        });
        content.appendChild(article);
      });
    }
    search.addEventListener("input", () => render(search.value));
    document.getElementById("expand").addEventListener("click", () => document.querySelectorAll(".section").forEach(s => { s.classList.remove("collapsed"); s.querySelector("button").textContent = "Collapse"; }));
    document.getElementById("collapse").addEventListener("click", () => document.querySelectorAll(".section").forEach(s => { s.classList.add("collapsed"); s.querySelector("button").textContent = "Expand"; }));
    render();
  </script>
</body>
</html>
"""


class ViewerHandler(BaseHTTPRequestHandler):
    log_path = DEFAULT_LOG

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/log":
            query = parse_qs(parsed.query)
            path = Path(query.get("path", [str(self.log_path)])[0])
            payload = build_payload(path)
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        payload = build_payload(self.log_path)
        body = APP_HTML.replace("__PAYLOAD__", json.dumps(payload, ensure_ascii=False))
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:
        return


def find_port(preferred: int) -> int:
    for port in range(preferred, preferred + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free local port found")


def main() -> int:
    parser = argparse.ArgumentParser(description="Local web viewer for Codex conversation logs")
    parser.add_argument("--log", default=str(DEFAULT_LOG), help="Markdown log path")
    parser.add_argument("--port", type=int, default=8765, help="Preferred local port")
    parser.add_argument("--no-open", action="store_true", help="Do not open browser automatically")
    args = parser.parse_args()
    ViewerHandler.log_path = Path(args.log).resolve()
    port = find_port(args.port)
    server = ThreadingHTTPServer(("127.0.0.1", port), ViewerHandler)
    url = f"http://127.0.0.1:{port}"
    print(f"Serving {ViewerHandler.log_path}")
    print(f"Open {url}")
    if not args.no_open:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping viewer.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
