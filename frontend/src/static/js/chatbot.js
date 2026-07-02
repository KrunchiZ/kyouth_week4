/* ============================================================
   State
   ============================================================ */

const session = []; // { income_bracket, question, answer, final_card, match_scores, timestamp }

/* ============================================================
   DOM refs
   ============================================================ */

const chatLog      = document.getElementById("chatLog");
const chatEntries  = document.getElementById("chatEntries");
const chatEmpty    = document.getElementById("chatEmpty");
const askBtn       = document.getElementById("askBtn");
const downloadBtn  = document.getElementById("downloadBtn");
const inputError   = document.getElementById("inputError");
const questionEl   = document.getElementById("question");
const incomeEl     = document.getElementById("incomeBracket");

/* ============================================================
   Auto-grow textarea
   ============================================================ */

questionEl.addEventListener("input", () => {
    questionEl.style.height = "auto";
    questionEl.style.height = questionEl.scrollHeight + "px";
});

/* ============================================================
   Helpers
   ============================================================ */

function scrollToBottom() {
    chatLog.scrollTop = chatLog.scrollHeight;
}

function showError(msg) {
    inputError.textContent = msg;
    inputError.classList.remove("d-none");
}

function clearError() {
    inputError.textContent = "";
    inputError.classList.add("d-none");
}

/* ============================================================
   Render helpers
   ============================================================ */

function renderCondensed(entry) {
    const div = document.createElement("div");
    div.className = "entry-condensed";
    div.innerHTML = `
        <div class="entry-meta">
            <span class="entry-income-badge">${entry.income_bracket}</span>
            <span class="entry-question">${escHtml(entry.question)}</span>
        </div>
        <p class="entry-answer-condensed">${escHtml(entry.answer)}</p>
    `;
    return div;
}

function renderCardSpotlight(card, match_scores) {
    const isNA = !card || card.card_title === "N/A";

    if (isNA) {
        return `<div class="no-match">No specific card match found for your question. Try rephrasing or ask about a different card type.</div>`;
    }

    const sections = [
        ["Cashback",            card.cashback],
        ["Petrol",              card.petrol],
        ["Rewards",             card.rewards],
        ["Travel",              card.travel],
        ["Premium Perks",       card.premium_perks],
        ["Balance Transfer",    card.balance_transfer],
        ["Easy Payment Plans",  card.easy_payment_plan],
        ["Fees & Charges",      card.fees],
        ["Requirements",        card.requirements],
        ["Features",            card.features],
        ["Min. Annual Income",  card.min_annual_income],
    ]
    .filter(([_, v]) => v && v !== "N/A")
    .map(([label, value]) => {
        // min_annual_income is a plain number string — no heading to strip
        const isPlain = label === "Min. Annual Income";
        const cleaned = isPlain ? escHtml(value) : renderMarkdown(stripFirstLine(value));
        return `
            <div class="card-detail-section">
                <h4>${label}</h4>
                <p>${cleaned}</p>
            </div>
        `;
    }).join("");

    const scoreHTML = match_scores
        ? `<span class="match-score-badge">${match_scores}% match</span>`
        : "";

    return `
        <div class="card-spotlight">
            <p class="card-spotlight-label">Recommended card</p>
            <div class="card-spotlight-header">
                <h3 class="card-spotlight-title">${escHtml(card.card_title)}</h3>
                <span class="card-bank-badge">${escHtml(card.bank)}</span>
                ${scoreHTML}
            </div>
            <div class="card-detail-grid">${sections}</div>
        </div>
    `;
}

function renderLatest(entry) {
    const div = document.createElement("div");
    div.className = "entry-latest";
    div.innerHTML = `
        <div class="entry-latest-header">
            <div class="entry-meta">
                <span class="entry-income-badge">${entry.income_bracket}</span>
                <span class="entry-question">${escHtml(entry.question)}</span>
            </div>
        </div>
        <div class="entry-latest-answer">${escHtml(entry.answer)}</div>
        ${renderCardSpotlight(entry.final_card, entry.match_scores)}
    `;
    return div;
}

/* ============================================================
   Re-render all entries
   Each call: all but the last become condensed, last is full.
   ============================================================ */

function renderAll() {
    chatEntries.innerHTML = "";

    if (!session.length) {
        chatEmpty.style.display = "";
        downloadBtn.disabled = true;
        return;
    }

    chatEmpty.style.display = "none";
    downloadBtn.disabled = false;

    session.forEach((entry, i) => {
        const el = i < session.length - 1
            ? renderCondensed(entry)
            : renderLatest(entry);
        chatEntries.appendChild(el);
    });

    scrollToBottom();
}

/* ============================================================
   Ask
   ============================================================ */

askBtn.addEventListener("click", async () => {
    clearError();

    const income   = incomeEl.value;
    const question = questionEl.value.trim();

    if (!income) { showError("Please select your monthly income range."); return; }
    if (!question) { showError("Please enter your question."); return; }

    // Build composite prompt
    const compositeQuestion = `My monthly income is ${income}. ${question}`;

    // Show loading
    askBtn.disabled = true;
    const loader = document.createElement("div");
    loader.className = "entry-loading";
    loader.innerHTML = `<div class="loading-spinner"></div> Thinking…`;
    chatEntries.appendChild(loader);
    chatEmpty.style.display = "none";
    scrollToBottom();

    try {
        const res = await fetch("/api/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question:     compositeQuestion,
                top_k:        7,
                llm_provider: "gemini-3.1-flash-lite",
            }),
        });

        if (!res.ok) throw new Error(`Server error: ${res.status}`);

        const data = await res.json();

        session.push({
            income_bracket: income,
            question:       question,          // display the original, not composite
            answer:         data.answer,
            final_card:     data.final_card,
            match_scores:   data.match_scores,
            timestamp:      new Date().toISOString(),
        });

        // Clear textarea
        questionEl.value = "";
        questionEl.style.height = "auto";

    } catch (err) {
        showError(`Something went wrong: ${err.message}`);
    } finally {
        loader.remove();
        askBtn.disabled = false;
        renderAll();
    }
});

/* ============================================================
   Download session as JSON
   ============================================================ */

downloadBtn.addEventListener("click", () => {
    if (!session.length) return;

    const payload = {
        exported_at: new Date().toISOString(),
        session,
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    const ts   = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);

    a.href     = url;
    a.download = `credit-card-advisor-session-${ts}.json`;
    a.click();
    URL.revokeObjectURL(url);
});

/* ============================================================
   Allow Shift+Enter in textarea, Enter to submit
   ============================================================ */

questionEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        askBtn.click();
    }
});

/* ============================================================
   Also update api.py default — reminder comment
   (top_k hardcoded to 7 in fetch above, llm_provider to gemini-3.1-flash-lite)
   ============================================================ */