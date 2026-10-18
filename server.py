import asyncio
import base64
import os
import subprocess
import time
from urllib.parse import urlparse

import requests
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
import mcp.types as types


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "mcp_errors.log")

USER = os.environ.get("OPENCODE_SERVER_USERNAME", "opencode")
PASSWORD = os.environ.get("OPENCODE_SERVER_PASSWORD", "")
AUTH = "Basic " + base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()


def log_error(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def _opencode_pids():
    out = subprocess.check_output(
        ["tasklist", "/FI", "IMAGENAME eq OpenCode.exe", "/FO", "CSV", "/NH"],
        text=True, stderr=subprocess.STDOUT,
    )
    pids = set()
    for line in out.splitlines():
        parts = [p.strip().strip('"') for p in line.split(",")]
        if len(parts) >= 2 and parts[0] == "OpenCode.exe" and parts[1].isdigit():
            pids.add(parts[1])
    return pids


def _candidate_ports(pids):
    netstat = subprocess.check_output(
        ["netstat", "-ano", "-p", "tcp"], text=True, stderr=subprocess.STDOUT
    )
    cands = []
    for line in netstat.splitlines():
        f = line.split()
        if len(f) < 5:
            continue
        state, pid = f[3], f[4]
        if state != "LISTENING" or pid not in pids:
            continue
        host, sep, port = f[1].rpartition(":")
        if not sep or not port.isdigit():
            continue
        cands.append((host, int(port)))
    return cands


def _probe(host, port):
    try:
        r = requests.get(f"http://{host}:{port}/session", headers={"Authorization": AUTH}, timeout=5)
        if r.status_code == 200:
            data = r.json()
            return isinstance(data, list) or isinstance(data, dict)
    except Exception as e:
        log_error(f"probe {host}:{port} failed: {e}")
    return False


def find_api():
    """Возвращает (host, port, base_url) живого API OpenCode или None."""
    try:
        pids = _opencode_pids()
    except Exception as e:
        log_error(f"tasklist failed: {e}")
        return None
    if not pids:
        return None
    for host, port in _candidate_ports(pids):
        if _probe(host, port):
            return host, port, f"http://{host}:{port}"
    return None


_EXT_MIME = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".svg": "image/svg+xml",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
}


def _mime_from_url(url):
    path = urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    return _EXT_MIME.get(ext, "application/octet-stream")


def _pick_session(base):
    r = requests.get(f"{base}/session", headers={"Authorization": AUTH}, timeout=10)
    r.raise_for_status()
    data = r.json()
    sessions = data if isinstance(data, list) else data.get("data", [])
    sessions = [s for s in sessions if isinstance(s, dict) and s.get("id")]
    if not sessions:
        raise RuntimeError("Список сессий пуст")
    sessions.sort(key=lambda s: (s.get("time") or {}).get("updated", 0), reverse=True)
    return sessions[0]["id"]


def fetch_image(url, timeout=30):
    """Скачивает изображение по URL. Возвращает (bytes, mime, filename)."""
    r = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "opencode-web-photo-mcp/1.0"},
    )
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code} при загрузке {url}")
    data = r.content
    if not data:
        raise RuntimeError("Пустой ответ при загрузке изображения")
    ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    if not ctype.startswith("image/"):
        ctype = _mime_from_url(url)
    filename = os.path.basename(urlparse(url).path) or "image"
    return data, ctype, filename


def send_web_photo(url, text=None, session_id=None):
    found = find_api()
    if not found:
        raise RuntimeError("Не найден активный сервер OpenCode (нет LISTENING-сокета).")
    host, port, base = found

    sid = session_id or _pick_session(base)

    data, mime, filename = fetch_image(url)
    b64 = base64.b64encode(data).decode()

    parts = []
    if text:
        parts.append({"type": "text", "text": text})
    parts.append({
        "type": "file",
        "mime": mime,
        "filename": filename,
        "url": f"data:{mime};base64,{b64}",
    })

    r = requests.post(
        f"{base}/session/{sid}/prompt_async",
        headers={"Authorization": AUTH, "Content-Type": "application/json"},
        json={"parts": parts},
        timeout=30,
    )
    return sid, port, r.status_code, (r.text or "")[:500]


server = Server("opencode-web-photo-mcp")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="send_web_photo",
            description=(
                "Скачивает изображение с интернета (по URL) и отправляет его в чат OpenCode "
                "через внутренний API (POST /session/{sid}/prompt_async). "
                "Не требует буфера обмена, фокуса окна или горячих клавиш."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "HTTP(S) URL изображения в интернете"},
                    "text": {"type": "string", "description": "Необязательная подпись/комментарий к фото"},
                    "session_id": {"type": "string", "description": "Необязательный ID сессии; по умолчанию — самая недавняя"},
                },
                "required": ["url"],
            },
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
    arguments = arguments or {}
    if name != "send_web_photo":
        raise ValueError("Unknown tool")

    url = arguments.get("url")
    text = arguments.get("text")
    session_id = arguments.get("session_id")

    try:
        sid, port, status, body = send_web_photo(url, text, session_id)
    except Exception as e:
        log_error(f"send_web_photo failed: {e}")
        return [types.TextContent(type="text", text=f"Ошибка отправки фото: {e}")]

    if 200 <= status < 300:
        return [types.TextContent(
            type="text",
            text=f"Фото отправлено в чат (сессия {sid}, порт {port}, HTTP {status}).",
        )]
    return [types.TextContent(type="text", text=f"Сервер вернул HTTP {status}: {body}")]


async def main():
    from mcp.server.stdio import stdio_server
    try:
        async with stdio_server() as (r, w):
            await server.run(
                r, w,
                InitializationOptions(
                    server_name="opencode-web-photo-mcp",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(NotificationOptions(), {}),
                ),
            )
    except Exception as e:
        log_error(f"Критическая ошибка запуска stdio сервера: {e}")


if __name__ == "__main__":
    asyncio.run(main())
