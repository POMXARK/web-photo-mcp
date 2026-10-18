# Research: sending internet images into OpenCode chat

## Russian

### Цель
Отправлять изображение, взятое **с интернета по URL**, в чат OpenCode desktop UI — тем же подтверждённым способом, что и `photo-upload-mcp` (локальный диск).

### Рабочий механизм (общий с photo-upload-mcp)
- `POST /session/{sid}/prompt_async` с `FilePartInput` (data-URL) в `parts` → **204**, фото рендерится в UI.
- Форма payload:
```json
{
  "parts": [
    { "type": "text", "text": "..." },
    { "type": "file", "mime": "image/png", "filename": "x.png", "url": "data:image/png;base64,...." }
  ]
}
```
- Поиск API: `tasklist` (PID OpenCode.exe) → `netstat -ano -p tcp` (LISTENING на 127.0.0.1 с этими PID) → проба `GET /session` с Basic auth → 200 = живой API.
- Автовыбор сессии: `GET /session`, сортировка по `time.updated` desc, первая.
- Auth: Basic, логин `opencode`, пароль из env `OPENCODE_SERVER_PASSWORD`.

### Специфика web-photo-mcp
1. **Загрузка по URL** — `requests.get(url)` с User-Agent; проверка HTTP 200 и непустого тела.
2. **Определение MIME**:
   - приоритет — заголовок `Content-Type` (если начинается с `image/`);
   - fallback — расширение файла в URL (`.png`, `.jpg`, `.gif`, `.webp`, …), иначе `application/octet-stream`.
3. **Filename** — basename пути URL, fallback `image`.
4. Остальной конвейер (base64 → data-URL → prompt_async) идентичен photo-upload-mcp.

### Почему отдельный проект
- Разные источники данных: локальный файл vs удалённый URL.
- Разные параметры и ошибки (сеть, таймауты, MIME из заголовков).
- Пользователь явно попросил «создать новый MCP».

### Факты окружения (на момент тестирования)
- Live-сервер: порт `60843`, exe `OpenCode.exe`.
- Тестовый URL: `https://picsum.photos/400/300` (JPEG, Content-Type `image/jpeg`).

## English

### Goal
Send an image fetched **from the internet by URL** into the OpenCode desktop chat — using the same confirmed mechanism as `photo-upload-mcp` (local disk).

### Working mechanism (shared with photo-upload-mcp)
- `POST /session/{sid}/prompt_async` with a `FilePartInput` (data-URL) in `parts` → **204**, photo renders in UI.
- Payload shape:
```json
{
  "parts": [
    { "type": "text", "text": "..." },
    { "type": "file", "mime": "image/png", "filename": "x.png", "url": "data:image/png;base64,...." }
  ]
}
```
- API discovery: `tasklist` (OpenCode.exe PIDs) → `netstat -ano -p tcp` (LISTENING on 127.0.0.1 with those PIDs) → probe `GET /session` with Basic auth → 200 = live API.
- Session auto-pick: `GET /session`, sort by `time.updated` desc, take first.
- Auth: Basic, user `opencode`, password from env `OPENCODE_SERVER_PASSWORD`.

### web-photo-mcp specifics
1. **URL fetch** — `requests.get(url)` with User-Agent; checks HTTP 200 and non-empty body.
2. **MIME detection**:
   - prefer `Content-Type` header (if it starts with `image/`);
   - fallback — file extension in the URL (`.png`, `.jpg`, `.gif`, `.webp`, …), else `application/octet-stream`.
3. **Filename** — basename of the URL path, fallback `image`.
4. The rest of the pipeline (base64 → data-URL → prompt_async) is identical to photo-upload-mcp.

### Why a separate project
- Different data source: local file vs remote URL.
- Different parameters and failure modes (network, timeouts, header-based MIME).
- The user explicitly asked for a new MCP.

### Environment facts (at test time)
- Live server: port `60843`, exe `OpenCode.exe`.
- Test URL: `https://picsum.photos/400/300` (JPEG, Content-Type `image/jpeg`).
