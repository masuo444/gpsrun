/**
 * GPS RUNNER Chatbot Widget
 * CarSensor-inspired UI / Mobile-first
 */
(function() {
    'use strict';

    const scriptTag = document.currentScript;
    const knowledgePath = scriptTag?.getAttribute('data-knowledge') || './knowledge.json';
    const primaryColor = scriptTag?.getAttribute('data-primary-color') || '#FFE500';
    const greetingOverride = scriptTag?.getAttribute('data-greeting') || '';
    const geminiKey = scriptTag?.getAttribute('data-gemini-key') || '';

    let knowledge = null;
    let settings = {};
    let conversationHistory = [];

    // --- CSS ---
    function loadCSS() {
        const cssPath = scriptTag?.src?.replace('chatbot.js', 'chatbot.css') || './chatbot.css';
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = cssPath;
        document.head.appendChild(link);

        if (!document.querySelector('link[href*="Noto+Sans+JP"]')) {
            const font = document.createElement('link');
            font.rel = 'stylesheet';
            font.href = 'https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600&display=swap';
            document.head.appendChild(font);
        }
    }

    // --- Knowledge ---
    async function loadKnowledge() {
        try {
            const res = await fetch(knowledgePath);
            if (!res.ok) throw new Error('not found');
            const data = await res.json();
            knowledge = data.entries || [];
            settings = data.settings || {};
        } catch (e) {
            knowledge = [];
            settings = {
                bot_name: 'サポート',
                greeting: 'こんにちは！ご質問をどうぞ。',
                fallback: 'お問い合わせフォームからご連絡ください。',
                quick_replies: []
            };
        }
    }

    // --- Gemini API ---
    function buildSystemPrompt() {
        const knowledgeText = (knowledge || []).map(e =>
            `【${e.category || ''}】\nQ: ${(e.questions || []).join(' / ')}\nA: ${e.answer}`
        ).join('\n\n');

        return `あなたはGPS RUNNER（志水直樹）の公式サイトに設置されたサポートチャットボットです。
ルール:
- 丁寧だが簡潔に（150文字以内を目安）
- ナレッジベースの情報のみ回答。不明な点は「お問い合わせフォームからご連絡ください」と案内
- 「AI」「人工知能」という言葉は使わない
- 返答に改行を適度に使い読みやすくする

ナレッジベース:
${knowledgeText}`;
    }

    async function askGemini(userMessage) {
        if (!geminiKey) return null;
        conversationHistory.push({ role: 'user', parts: [{ text: userMessage }] });
        const recentHistory = conversationHistory.slice(-10);
        try {
            const res = await fetch(
                `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${geminiKey}`,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        system_instruction: { parts: [{ text: buildSystemPrompt() }] },
                        contents: recentHistory,
                        generationConfig: { temperature: 0.3, maxOutputTokens: 250 }
                    })
                }
            );
            if (!res.ok) return null;
            const data = await res.json();
            const reply = data?.candidates?.[0]?.content?.parts?.[0]?.text || null;
            if (reply) conversationHistory.push({ role: 'model', parts: [{ text: reply }] });
            return reply;
        } catch { return null; }
    }

    // --- Keyword matching ---
    function findAnswerByKeyword(userMessage) {
        if (!knowledge || knowledge.length === 0) return null;
        const msg = userMessage.toLowerCase().replace(/[？?！!。、\s]/g, '');
        let bestMatch = null, bestScore = 0;
        for (const entry of knowledge) {
            let score = 0;
            for (const kw of (entry.keywords || [])) {
                if (msg.includes(kw.toLowerCase().replace(/\s/g, ''))) score += 10;
            }
            for (const q of (entry.questions || [])) {
                const qNorm = q.toLowerCase().replace(/[？?！!。、\s]/g, '');
                if (msg.includes(qNorm) || qNorm.includes(msg)) score += 15;
                const common = [...msg].filter(c => qNorm.includes(c)).length;
                if (common / Math.max(msg.length, qNorm.length) > 0.5) score += 5;
            }
            if (score > bestScore) { bestScore = score; bestMatch = entry; }
        }
        return bestScore >= 5 ? bestMatch?.answer : null;
    }

    async function getAnswer(userMessage) {
        if (geminiKey) {
            const reply = await askGemini(userMessage);
            if (reply) return reply;
        }
        const kw = findAnswerByKeyword(userMessage);
        if (kw) return kw;
        const fallbackUrl = settings.fallback_url || 'contact.html';
        const fallbackLabel = settings.fallback_url_label || 'お問い合わせフォームへ';
        return `${settings.fallback || 'うまく答えられませんでした。'}\n\n<a href="${escapeHtml(fallbackUrl)}" style="color:inherit;font-weight:600;text-decoration:underline;">${escapeHtml(fallbackLabel)}</a>`;
    }

    // --- UI ---
    function buildWidget() {
        document.documentElement.style.setProperty('--saqt-primary', primaryColor);

        // Floating button
        const btn = document.createElement('button');
        btn.className = 'saqt-chat-btn';
        btn.setAttribute('aria-label', 'チャットを開く');
        btn.innerHTML = `
            <svg class="saqt-icon-chat" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            <svg class="saqt-icon-close" viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12" stroke="#0A0A0A" stroke-width="2.5" stroke-linecap="round" fill="none"/></svg>
            <span class="saqt-chat-badge">1</span>
        `;

        // Chat window
        const win = document.createElement('div');
        win.className = 'saqt-chat-window';
        win.setAttribute('role', 'dialog');
        win.setAttribute('aria-label', 'サポートチャット');

        const botName = settings.bot_name || 'サポート';
        const greeting = greetingOverride || settings.greeting || 'こんにちは！';

        win.innerHTML = `
            <div class="saqt-chat-header">
                <div class="saqt-chat-avatar">🏃</div>
                <div class="saqt-chat-header-info">
                    <h3>${escapeHtml(botName)}</h3>
                    <p><span class="saqt-status-dot"></span>オンライン</p>
                </div>
                <button class="saqt-header-close" aria-label="チャットを閉じる">
                    <svg viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12" stroke-linecap="round" stroke-linejoin="round"/></svg>
                </button>
            </div>
            <div class="saqt-chat-messages" id="saqt-messages" role="log" aria-live="polite"></div>
            <div class="saqt-quick-replies" id="saqt-quick" aria-label="クイック返信"></div>
            <div class="saqt-chat-input-area">
                <input type="text" class="saqt-chat-input" id="saqt-input"
                    placeholder="メッセージを入力..." autocomplete="off"
                    inputmode="text" enterkeyhint="send">
                <button class="saqt-chat-send" id="saqt-send" aria-label="送信">
                    <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
                </button>
            </div>
            <div class="saqt-chat-powered">GPS RUNNER 公式サポート</div>
        `;

        document.body.appendChild(btn);
        document.body.appendChild(win);

        const messagesEl = win.querySelector('#saqt-messages');
        const inputEl    = win.querySelector('#saqt-input');
        const sendBtn    = win.querySelector('#saqt-send');
        const quickEl    = win.querySelector('#saqt-quick');
        const closeBtn   = win.querySelector('.saqt-header-close');
        const badge      = btn.querySelector('.saqt-chat-badge');
        let isOpen = false;
        let isProcessing = false;

        function openChat() {
            isOpen = true;
            win.classList.add('open');
            btn.classList.add('active');
            badge.classList.add('hidden');
            // スマホでキーボードが遅れて開くのを防ぐため少し待つ
            setTimeout(() => inputEl.focus(), 300);
        }

        function closeChat() {
            isOpen = false;
            win.classList.remove('open');
            btn.classList.remove('active');
        }

        btn.addEventListener('click', () => isOpen ? closeChat() : openChat());
        closeBtn.addEventListener('click', closeChat);

        // スマホ: ウィンドウ外タップで閉じる
        document.addEventListener('click', (e) => {
            if (isOpen && !win.contains(e.target) && !btn.contains(e.target)) {
                closeChat();
            }
        });

        // 初期メッセージ
        addBotMessage(greeting);
        showQuickReplies();

        async function handleSend() {
            const text = inputEl.value.trim();
            if (!text || isProcessing) return;
            inputEl.value = '';
            isProcessing = true;
            hideQuickReplies();
            addUserMessage(text);
            showTyping();
            const answer = await getAnswer(text);
            removeTyping();
            addBotMessage(answer);
            showQuickReplies();
            isProcessing = false;
        }

        sendBtn.addEventListener('click', handleSend);
        inputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.isComposing) { e.preventDefault(); handleSend(); }
        });

        function addBotMessage(html) {
            const row = document.createElement('div');
            row.className = 'saqt-msg saqt-msg-bot';
            row.innerHTML = `
                <div class="saqt-msg-avatar">🏃</div>
                <div class="saqt-msg-bubble">${nl2br(html)}</div>
            `;
            messagesEl.appendChild(row);
            scrollToBottom();
        }

        function addUserMessage(text) {
            const row = document.createElement('div');
            row.className = 'saqt-msg saqt-msg-user';
            row.innerHTML = `<div class="saqt-msg-bubble">${escapeHtml(text)}</div>`;
            messagesEl.appendChild(row);
            scrollToBottom();
        }

        function showTyping() {
            const el = document.createElement('div');
            el.className = 'saqt-typing';
            el.id = 'saqt-typing';
            el.innerHTML = '<div class="saqt-typing-dot"></div><div class="saqt-typing-dot"></div><div class="saqt-typing-dot"></div>';
            messagesEl.appendChild(el);
            scrollToBottom();
        }

        function removeTyping() {
            document.getElementById('saqt-typing')?.remove();
        }

        function showQuickReplies() {
            const replies = settings.quick_replies || [];
            if (!replies.length) return;
            quickEl.innerHTML = '';
            for (const text of replies) {
                const qbtn = document.createElement('button');
                qbtn.className = 'saqt-quick-btn';
                qbtn.textContent = text;
                qbtn.addEventListener('click', () => {
                    inputEl.value = text;
                    handleSend();
                });
                quickEl.appendChild(qbtn);
            }
        }

        function hideQuickReplies() { quickEl.innerHTML = ''; }
        function scrollToBottom() {
            requestAnimationFrame(() => {
                messagesEl.scrollTop = messagesEl.scrollHeight;
            });
        }
    }

    function escapeHtml(str) {
        const d = document.createElement('div');
        d.textContent = String(str || '');
        return d.innerHTML;
    }

    // リンクタグは許可しつつ改行を<br>に変換
    function nl2br(str) {
        // すでにHTMLが含まれている場合（リンク等）はそのまま改行だけ変換
        return str.replace(/\n/g, '<br>');
    }

    async function init() {
        loadCSS();
        await loadKnowledge();
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', buildWidget);
        } else {
            buildWidget();
        }
    }

    init();
})();
