from __future__ import annotations

import html
from dataclasses import dataclass

import bleach
from markdown_it import MarkdownIt
from mdit_py_plugins.amsmath import amsmath_plugin
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin
from mdit_py_plugins.tasklists import tasklists_plugin

__all__ = [
    "markdown_to_html",
    "render_for_telegram",
    "truncate_for_telegram",
    "RenderedMessage",
]

_markdown = MarkdownIt("commonmark", {'linkify': True, 'typographer': True})
_markdown.enable('table')
_markdown.enable('strikethrough')
_markdown.use(tasklists_plugin)
_markdown.use(footnote_plugin)
_markdown.use(dollarmath_plugin)
_markdown.use(amsmath_plugin)

_ALLOWED_TAGS = {
    "a",
    "abbr",
    "b",
    "blockquote",
    "code",
    "del",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "img",
    "li",
    "ol",
    "p",
    "pre",
    "span",
    "strong",
    "sup",
    "sub",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "ul",
}

_ALLOWED_ATTRS = {
    "a": ["href", "title", "target", "rel"],
    "img": ["src", "alt", "title", "width", "height"],
    "th": ["align"],
    "td": ["align"],
    "span": ["class"],
    "code": ["class"],
}

_ALLOWED_PROTOCOLS = ["http", "https", "tg", "mailto", "data"]


def markdown_to_html(markdown_text: str) -> str:
    """Render Markdown into sanitized HTML suitable for the mini-app."""
    raw_html = _markdown.render(markdown_text)
    cleaned = bleach.clean(
        raw_html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )
    return cleaned


def render_for_telegram(text: str) -> str:
    """Escape text for Telegram HTML parse mode."""
    return html.escape(text, quote=False)


@dataclass(slots=True)
class RenderedMessage:
    text: str
    truncated: bool


def truncate_for_telegram(text: str, limit: int = 3900) -> RenderedMessage:
    if len(text) <= limit:
        return RenderedMessage(text=text, truncated=False)

    truncated_text = text[:limit - 40].rsplit(" ", 1)[0]
    truncated_text = truncated_text.rstrip() + "\n\n<b>См. полностью в мини-аппе</b>"
    return RenderedMessage(text=truncated_text, truncated=True)

