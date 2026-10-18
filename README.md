# Web Photo MCP (OpenCode)

MCP-сервер, который скачивает изображение **с интернета** (по URL) и отправляет его в чат OpenCode через внутренний HTTP API. Использует тот же проверенный подход, что и `photo-upload-mcp` (`POST /session/{sid}/prompt_async`) — без буфера обмена, фокуса окна и горячих клавиш.

> Исследование: [RESEARCH.md](RESEARCH.md) · Близнец для локальных файлов: [POMXARK/photo-upload-mcp](https://github.com/POMXARK/photo-upload-mcp)

---

## Русский

### Что делает
- Инструмент **`send_web_photo(url, text?, session_id?)`**.
- Скачивает изображение по HTTP(S) URL, кодирует в base64 (data-URL) и отправляет как `FilePartInput`.
- Фото рендерится в desktop UI OpenCode.
- MIME определяется из заголовка `Content-Type`; при отсутствии — по расширению URL.
- **Сам находит** адрес API (PID `OpenCode.exe` ∩ LISTENING-сокеты) и **сам выбирает** сессию (самая недавняя).

### Параметры инструмента
| Параметр | Тип | Обязательный | Описание |
|---|---|---|---|
| `url` | string | да | HTTP(S) URL изображения в интернете |
| `text` | string | нет | Подпись/комментарий к фото |
| `session_id` | string | нет | ID сессии; по умолчанию — самая недавняя |

### Требования
- **Windows** (поиск порта использует `tasklist` и `netstat`).
- **Python 3.x** с пакетами: `mcp` (MCP SDK) и `requests`.
- Запущенный **OpenCode Desktop** на `127.0.0.1` с паролем сервера.
- Доступ в интернет для загрузки изображения.

### Переменные окружения
| Переменная | По умолчанию | Описание |
|---|---|---|
| `OPENCODE_SERVER_USERNAME` | `opencode` | Логин для Basic-авторизации |
| `OPENCODE_SERVER_PASSWORD` | — | Пароль сервера (наследуется дочерним процессом MCP) |

### Установка / регистрация
1. Положите `server.py` в любую папку, например `C:/tests_model/web-photo-mcp/`.
2. В `opencode.json` добавьте запись под ключом `mcp`:
   ```json
   {
     "mcp": {
       "web-photo": {
         "type": "local",
         "command": ["C:\\Python314\\python.exe", "C:/tests_model/web-photo-mcp/server.py"],
         "enabled": true
       }
     }
   }
   ```
   (замените путь к `python.exe` и к `server.py` на свои)
3. Перезапустите OpenCode — инструмент `send_web_photo` станет доступен агенту.

### Использование
- Вызов: `send_web_photo(url="https://example.com/a.png", text="Вот фото")`.
- `session_id` опционален — сессия подхватится автоматически.

---

## English

### What it does
- Tool **`send_web_photo(url, text?, session_id?)`**.
- Downloads an image from an HTTP(S) URL, base64-encodes it (data-URL) and sends it as a `FilePartInput`.
- The photo renders in the OpenCode desktop UI.
- MIME is taken from the `Content-Type` header; if absent — from the URL extension.
- **Finds the API address itself** (`OpenCode.exe` PIDs ∩ LISTENING sockets) and **picks the session itself** (most recent).

### Tool parameters
| Parameter | Type | Required | Description |
|---|---|---|---|
| `url` | string | yes | HTTP(S) URL of the image on the internet |
| `text` | string | no | Caption/comment for the photo |
| `session_id` | string | no | Session ID; defaults to the most recent one |

### Requirements
- **Windows** (port discovery uses `tasklist` and `netstat`).
- **Python 3.x** with packages: `mcp` (MCP SDK) and `requests`.
- A running **OpenCode Desktop** on `127.0.0.1`, with a server password set.
- Internet access to download the image.

### Environment variables
| Variable | Default | Description |
|---|---|---|
| `OPENCODE_SERVER_USERNAME` | `opencode` | Basic-auth username |
| `OPENCODE_SERVER_PASSWORD` | — | Server password (inherited by the MCP child process) |

### Installation / registration
1. Place `server.py` in any folder, e.g. `C:/tests_model/web-photo-mcp/`.
2. Add an entry under the `mcp` key in `opencode.json`:
   ```json
   {
     "mcp": {
       "web-photo": {
         "type": "local",
         "command": ["C:\\Python314\\python.exe", "C:/tests_model/web-photo-mcp/server.py"],
         "enabled": true
       }
     }
   }
   ```
   (replace the `python.exe` and `server.py` paths with your own)
3. Restart OpenCode — the `send_web_photo` tool becomes available to the agent.

### Usage
- Call: `send_web_photo(url="https://example.com/a.png", text="Here is the photo")`.
- The `session_id` field is optional — a session is picked automatically.

---

## Files
- `server.py` — the MCP server.
- `RESEARCH.md` — research and rationale for the chosen approach.
- `.gitignore`
