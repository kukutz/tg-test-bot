from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from app.config import get_settings


def webapp_button(text: str, *, path: str = "") -> InlineKeyboardButton:
    settings = get_settings()
    url = f"{settings.base_webapp_url.rstrip('/')}/{path.lstrip('/')}"
    return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url))


def start_keyboard() -> InlineKeyboardMarkup:
    button = webapp_button("Открыть мини-апп", path="view")
    return InlineKeyboardMarkup(
        inline_keyboard=[[button]],
    )


def answer_keyboard(answer_id: str) -> InlineKeyboardMarkup:
    settings = get_settings()
    url = f"{settings.base_webapp_url.rstrip('/')}/view?mid={answer_id}"
    button = InlineKeyboardButton(text="Открыть полный ответ", web_app=WebAppInfo(url=url))
    return InlineKeyboardMarkup(
        inline_keyboard=[[button]],
    )


def inline_suggestions_keyboard() -> InlineKeyboardMarkup:
    settings = get_settings()
    username = settings.telegram_bot_username or settings.telegram_bot_token.split(":")[0]
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Перейти в бота", url=f"https://t.me/{username}")],
            [InlineKeyboardButton(
                text="Мини-апп",
                web_app=WebAppInfo(
                    url=f"{settings.base_webapp_url.rstrip('/')}/inline?source=inline",
                ),
            )],
        ],
    )


def inline_answer_keyboard(answer_id: str) -> InlineKeyboardMarkup:
    settings = get_settings()
    username = settings.telegram_bot_username or settings.telegram_bot_token.split(":")[0]
    view_button = InlineKeyboardButton(
        text="Открыть полный ответ",
        web_app=WebAppInfo(
            url=f"{settings.base_webapp_url.rstrip('/')}/view?mid={answer_id}",
        ),
    )
    open_bot = InlineKeyboardButton(text="Перейти в бота", url=f"https://t.me/{username}")
    return InlineKeyboardMarkup(
        inline_keyboard=[[view_button], [open_bot]],
    )

