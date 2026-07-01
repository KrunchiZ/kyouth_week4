/* ============================================================
   Shared utilities
   utils.js — included by chatbot.html and card_detail.html
   ============================================================ */

function escHtml(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

function stripFirstLine(text) {
    // Remove the redundant section heading that is always the first line of
    // each card field (e.g. "Cashback\nGet cash rebates..." → "Get cash rebates...")
    const idx = text.indexOf("\n");
    return idx !== -1 ? text.slice(idx + 1).trim() : text.trim();
}

function buildTable(rows) {
    if (!rows.length) return "";
    const [head, ...body] = rows;
    const ths = head.map(c => `<th>${escHtml(c)}</th>`).join("");
    const trs = body.map(row => {
        const tds = row.map(c => `<td>${escHtml(c)}</td>`).join("");
        return `<tr>${tds}</tr>`;
    }).join("");
    return `<div class="card-table-wrap"><table class="card-table"><thead><tr>${ths}</tr></thead><tbody>${trs}</tbody></table></div>`;
}

function renderMarkdown(text) {
    const lines = text.split("\n");
    const out   = [];
    let tableRows = [];

    const isTableRow  = l => l.trim().startsWith("|") && l.trim().endsWith("|");
    const isSeparator = l => /^\|[\s\-|]+\|$/.test(l.trim());

    for (const line of lines) {
        if (isSeparator(line)) {
            // skip separator rows
        } else if (isTableRow(line)) {
            const cells = line.trim().slice(1, -1).split("|").map(c => c.trim());
            tableRows.push(cells);
        } else {
            if (tableRows.length) {
                out.push(buildTable(tableRows));
                tableRows = [];
            }
            out.push(escHtml(line));
        }
    }
    if (tableRows.length) out.push(buildTable(tableRows));

    return out.join("\n").replace(/\n{2,}/g, "</p><p>").replace(/\n/g, "<br>");
}