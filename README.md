# Telegram AI Assistant

Полнофункциональный Telegram-бот с тремя режимами работы: личный чат, инлайн и мини-приложение для просмотра ответов.

## Возможности

- Стриминг ответов из OpenAI Chat Completions с обновлением сообщений раз в ~1 секунду.
- Inline-режим `@bot <запрос>` с подсказками и кнопками перехода.
- Мини-приложение (Telegram WebApp) с поддержкой Markdown, таблиц, подсветки кода и кнопкой «Сгенерировать изображение» для инлайн режима.
- Хранение ответов и метаданных в базе (SQLite по умолчанию).
- FastAPI-сервер: вебхук для бота, API мини-приложения, статика.

## Архитектура

```
app/
  bot/
    handlers/        # message, inline, ошибки
    keyboards/       # инлайн-клавиатуры и web_app кнопки
    utils/           # стриминг ответов
  services/          # OpenAI клиент, Markdown утилиты
  storage/           # SQLAlchemy модели и репозитории
  web/               # FastAPI приложение и мини-апп
main.py              # точка входа (см. ниже)
```

## Быстрый старт

1. **Установите зависимости**

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e .[dev]
```

2. **Настройте переменные окружения**

| Переменная | Описание |
| ---------- | -------- |
| `TELEGRAM_BOT_TOKEN` | токен бота от BotFather |
| `TELEGRAM_BOT_USERNAME` | юзернейм бота без `@` (опционально) |
| `OPENAI_API_KEY` | API ключ OpenAI |
| `BASE_WEBAPP_URL` | публичный URL мини-аппа, например `https://example.com` |
| `WEBHOOK_URL` | публичный URL вебхука `https://example.com/webhook` |
| `DATABASE_URL` | строка подключения SQLAlchemy, по умолчанию `sqlite+aiosqlite:///./bot.db` |
| `OPENAI_MODEL` | имя модели, по умолчанию `gpt-4o-mini` |
| `OPENAI_TEMPERATURE` | температура выборки |

Создайте файл `.env` и заполните значения:

```
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_BOT_USERNAME=my_bot
OPENAI_API_KEY=sk-...
BASE_WEBAPP_URL=https://your.domain
WEBHOOK_URL=https://your.domain/webhook
DATABASE_URL=sqlite+aiosqlite:///./bot.db
```

3. **Запуск локально**

```bash
make dev
```

Команда запускает FastAPI (uvicorn) на `http://127.0.0.1:8000`. Для приёма обновлений используйте туннель, например:

```bash
# Ngrok
ngrok http 8000
# либо Cloudflare Tunnel
cloudflared tunnel --url http://localhost:8000
```

Укажите публичный адрес туннеля в `BASE_WEBAPP_URL` и `WEBHOOK_URL`, затем выполните:

```bash
curl -X POST https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/setWebhook \
  -d url=$WEBHOOK_URL
```

4. **Альтернативный запуск (polling)**

Для разработки можно запустить бота в режиме polling:

```bash
python -m main bot
```

FastAPI-приложение отдельно:

```bash
python -m main web
```

## Тесты и линтинг

```bash
make lint
make test
```

## Mini-app

- `/view?mid=<id>` — отображение сохранённого ответа (Markdown → HTML).
- `/inline` — страница для инлайн режима с кнопкой «Сгенерировать изображение» (подставляет `Generate image ` в поле ввода через WebApp API).
- Подписи `initData` проверяются на сервере (HMAC с токеном бота).

## Настройка BotFather

1. Создайте бота, получите токен.
2. Включите режим inline (`/setinline`), задайте placeholder.
3. Включите WebApp кнопку (меню `Bot Settings` → `Menu Button`).
4. Укажите домен мини-аппа (раздел *Web Apps* в BotFather) — должен совпадать с `BASE_WEBAPP_URL`.

После деплоя убедитесь, что `/healthz` возвращает `{ "status": "ok" }`.

