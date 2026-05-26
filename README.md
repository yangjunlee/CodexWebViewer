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

---

# Codex Log Viewer 한국어 안내

Codex나 다른 채팅 도구에서 내보낸 Markdown 대화 로그를 로컬 웹페이지로 보기 위한 작은 뷰어입니다.

긴 기술 대화를 터미널이나 원본 Markdown에서 위아래로 스크롤하며 보는 불편함을 줄이기 위해 만들었습니다.

## 주요 기능

- 로컬 전용 웹 서버
- Markdown 로그 렌더링
- 섹션 목차
- 검색
- 전체 펼침/접기
- 섹션별 접기/펼치기
- 시스템 설정에 따른 라이트/다크 모드
- 외부 Python 패키지 불필요

## 빠른 시작

```powershell
python .\codex_log_viewer.py --log .\sample_log.md
```

그 다음 브라우저에서 아래 주소를 엽니다.

```text
http://127.0.0.1:8765
```

기본적으로 브라우저는 자동으로 열립니다.

## 내 로그 파일 보기

```powershell
python .\codex_log_viewer.py --log "C:\path\to\conversation_log.md"
```

`8765` 포트가 이미 사용 중이면 자동으로 다음 사용 가능한 포트를 찾습니다.

## 옵션

```text
--log PATH     볼 Markdown 로그 파일 경로
--port PORT    선호하는 로컬 포트, 기본값 8765
--no-open      브라우저를 자동으로 열지 않음
```

## 권장 Markdown 형식

아래와 같은 형식의 로그에서 가장 잘 동작합니다.

```markdown
## 1. Topic

**User**

Message text

**Assistant**

Reply text
```

코드 블록, 인라인 코드, bullet list, 간단한 링크도 지원합니다.

## 개인정보 주의

이 앱은 로컬 머신에서만 파일을 서빙합니다. 하지만 공개 GitHub 저장소에는 개인 대화 로그, 거래기록, 비밀번호, `.env` 파일을 커밋하지 마세요.
