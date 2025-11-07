const tg = window.Telegram?.WebApp;
const root = document.body;
const mode = root.dataset.mode;
const answerId = root.dataset.answerId;
const botUsername = root.dataset.botUsername;
const statusEl = document.getElementById('status');
const answerEl = document.getElementById('answer');
const metaEl = document.getElementById('meta');
const shareBtn = document.getElementById('share-btn');
const openBotBtn = document.getElementById('open-bot-btn');
const generateImageBtn = document.getElementById('generate-image-btn');

let hljs = null;

async function ensureHighlight() {
    if (hljs) return hljs;
    const mod = await import('https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/es/core.min.js');
    const js = await import('https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/es/languages/javascript.min.js');
    const py = await import('https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/es/languages/python.min.js');
    const bash = await import('https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/es/languages/bash.min.js');
    mod.default.registerLanguage('javascript', js.default);
    mod.default.registerLanguage('python', py.default);
    mod.default.registerLanguage('bash', bash.default);
    hljs = mod.default;
    return hljs;
}

function applyTheme() {
    if (!tg) return;
    root.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#0f1117');
    root.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#f5f6f8');
}

async function renderAnswer(data) {
    const sanitized = DOMPurify.sanitize(data.html || '');
    answerEl.innerHTML = sanitized;
    const info = data.meta || {};
    const created = info.created_at ? new Date(info.created_at).toLocaleString() : '';
    metaEl.textContent = `Модель: ${info.model || '—'} • Режим: ${info.mode || '—'} • Время: ${created}`;
    statusEl.textContent = 'Готово';
    const highlighter = await ensureHighlight();
    document.querySelectorAll('pre code').forEach((block) => {
        highlighter.highlightElement(block);
    });
}

async function fetchAnswer(mid) {
    if (!mid) {
        statusEl.textContent = 'Ответ не найден';
        return;
    }
    try {
        const resp = await fetch(`/api/answers?mid=${encodeURIComponent(mid)}`, {
            headers: {
                'X-Telegram-Init-Data': tg?.initData || '',
            },
        });
        if (!resp.ok) {
            throw new Error('Ответ не найден');
        }
        const data = await resp.json();
        await renderAnswer(data);
    } catch (error) {
        statusEl.textContent = error.message || 'Ошибка загрузки';
    }
}

function setupButtons() {
    shareBtn.addEventListener('click', async () => {
        if (!answerId) return;
        const url = new URL(window.location.href);
        url.searchParams.set('mid', answerId);
        await navigator.clipboard.writeText(url.toString());
        statusEl.textContent = 'Ссылка скопирована';
        setTimeout(() => (statusEl.textContent = 'Готово'), 2000);
    });

    openBotBtn.addEventListener('click', () => {
        const link = `https://t.me/${botUsername}`;
        if (tg?.openTelegramLink) {
            tg.openTelegramLink(link);
        } else {
            window.open(link, '_blank');
        }
    });

    generateImageBtn.addEventListener('click', () => {
        if (tg?.switchInlineQuery) {
            tg.switchInlineQuery('Generate image ', true);
        } else {
            statusEl.textContent = 'Откройте бот в Telegram';
        }
    });
}

function configureInlineMode() {
    if (mode !== 'inline') {
        generateImageBtn.classList.add('hidden');
        return;
    }
    generateImageBtn.classList.remove('hidden');
    statusEl.textContent = 'Готово к генерации';
    if (tg) {
        tg.MainButton.setText('Сгенерировать изображение');
        tg.MainButton.onClick(() => tg.switchInlineQuery('Generate image ', true));
        tg.MainButton.show();
        tg.BackButton.show();
        tg.BackButton.onClick(() => tg.close());
    }
}

(async function init() {
    if (tg) {
        tg.ready();
        applyTheme();
    }
    setupButtons();
    configureInlineMode();
    if (mode === 'view' && answerId) {
        await fetchAnswer(answerId);
    } else if (mode === 'view') {
        statusEl.textContent = 'Передан пустой идентификатор ответа';
    }
})();

