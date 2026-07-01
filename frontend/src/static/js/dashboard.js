/* ============================================================
   State
   ============================================================ */

const PAGE_SIZE = 6;
let allCards    = [];   // full card detail objects, fetched once
let filtered    = [];   // subset after applying filters
let currentPage = 1;

/* ============================================================
   DOM refs
   ============================================================ */

const cardGrid     = document.getElementById("cardGrid");
const gridEmpty    = document.getElementById("gridEmpty");
const gridLoading  = document.getElementById("gridLoading");
const paginationBar = document.getElementById("paginationBar");
const prevBtn      = document.getElementById("prevBtn");
const nextBtn      = document.getElementById("nextBtn");
const pageInfo     = document.getElementById("pageInfo");

const filterBank    = document.getElementById("filterBank");
const filterIncome  = document.getElementById("filterIncome");
const filterSearch  = document.getElementById("filterSearch");

/* ============================================================
   Charts (data injected server-side by Jinja2)
   ============================================================ */

const CHART_COLORS = {
    accent: "#3B5BFF",
    mint:   "#16A34A",
};

function initCharts() {
    if (typeof BANK_COUNTS === "undefined") return;

    const sharedOptions = {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
            y: {
                beginAtZero: true,
                ticks: { stepSize: 1, color: "#94A3B8" },
                grid: { color: "#E4E7EC" },
            },
            x: {
                ticks: { color: "#64748B" },
                grid: { display: false },
            },
        },
    };

    new Chart(document.getElementById("bankChart"), {
        type: "bar",
        data: {
            labels: Object.keys(BANK_COUNTS),
            datasets: [{
                data: Object.values(BANK_COUNTS),
                backgroundColor: CHART_COLORS.accent,
                borderRadius: 6,
            }],
        },
        options: sharedOptions,
    });
}

/* ============================================================
   Fetch all cards client-side (batches of 6)
   ============================================================ */

async function fetchAllCards() {
    const cards  = [];
    let offset   = 0;
    const limit  = 6;

    while (true) {
        const res = await fetch(`/api/cards?offset=${offset}&limit=${limit}&paginate=true`);
        if (!res.ok) throw new Error(`Failed to fetch cards: ${res.status}`);
        const data  = await res.json();
        const batch = data.cards ?? [];
        if (!batch.length) break;
        cards.push(...batch);
        if (batch.length < limit) break;
        offset += limit;
    }

    return cards;
}

/* ============================================================
   Render helpers
   ============================================================ */

function formatIncome(val) {
    if (!val || val === "N/A") return "Not specified";
    const n = parseInt(val, 10);
    if (!isNaN(n)) return `RM${n.toLocaleString()} / yr`;
    return val; // "Invitation Only", "Any Business..."
}

function renderCard(card) {
    const col = document.createElement("div");
    col.className = "col-12 col-sm-6 col-lg-4";
    col.innerHTML = `
        <div class="card-tile">
            <span class="card-tile-bank">${escHtml(card.bank)}</span>
            <div class="card-tile-title">${escHtml(card.card_title)}</div>
            <div class="card-tile-income">${escHtml(formatIncome(card.min_annual_income))}</div>
            <a class="card-tile-btn" href="/dashboard/${encodeURIComponent(card.card_title)}">
                View Details
            </a>
        </div>
    `;
    return col;
}

function escHtml(str) {
    if (!str) return "";
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
}

/* ============================================================
   Filter + paginate
   ============================================================ */

function applyFilters() {
    const bank   = filterBank.value;
    const income = filterIncome.value;
    const search = filterSearch.value.toLowerCase().trim();

    filtered = allCards.filter(card => {
        if (bank   && card.bank !== bank)                        return false;
        if (income && card.min_annual_income !== income)         return false;
        if (search && !card.card_title.toLowerCase().includes(search)) return false;
        return true;
    });

    currentPage = 1;
    renderPage();
}

function renderPage() {
    cardGrid.innerHTML = "";

    const total = filtered.length;
    const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
    currentPage = Math.min(currentPage, pages);

    const start = (currentPage - 1) * PAGE_SIZE;
    const slice = filtered.slice(start, start + PAGE_SIZE);

    if (!total) {
        gridEmpty.classList.remove("d-none");
        paginationBar.style.visibility = "hidden";
    } else {
        gridEmpty.classList.add("d-none");
        paginationBar.style.visibility = "visible";
        slice.forEach(card => cardGrid.appendChild(renderCard(card)));
    }

    pageInfo.textContent = total ? `${currentPage} / ${pages}` : "";
    prevBtn.disabled = currentPage <= 1;
    nextBtn.disabled = currentPage >= pages;
}

/* ============================================================
   Pagination controls
   ============================================================ */

if (prevBtn) prevBtn.addEventListener("click", () => { currentPage--; renderPage(); });
if (nextBtn) nextBtn.addEventListener("click", () => { currentPage++; renderPage(); });

/* ============================================================
   Filter listeners
   ============================================================ */

if (filterBank && filterIncome) {
    [filterBank, filterIncome].forEach(el =>
        el.addEventListener("change", applyFilters)
    );
}
if (filterSearch) filterSearch.addEventListener("input", applyFilters);

/* ============================================================
   Boot
   ============================================================ */

async function init() {
    initCharts();

    try {
        allCards = await fetchAllCards();
        filtered = allCards;
    } catch (err) {
        if (gridLoading) gridLoading.innerHTML = `<span style="color:#dc2626">Failed to load cards: ${err.message}</span>`;
        return;
    }

    if (gridLoading) gridLoading.style.display = "none";
    renderPage();
}

if (cardGrid) init();