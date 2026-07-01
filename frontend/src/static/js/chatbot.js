const askBtn = document.getElementById("askBtn");

askBtn.addEventListener("click", async ()=>{
    const llm_provider = document.getElementById("modelSelect").value;
    const top_k = parseInt(document.getElementById("topK").value);
    const question = document.getElementById("question").value;
    const loading = document.getElementById("loading");

    if (!question) {
        return;
    }

    loading.innerHTML="Thinking with <strong>${llm_provider}</strong>...";
    document.getElementById("answer").innerHTML = "";
    document.getElementById("card-result").innerHTML = "";
    askBtn.disabled = true;

    try{
        const response = await fetch("/api/ask",{
            method:"POST",
            headers:{"Content-Type":"application/json"},
            body:JSON.stringify({question, top_k, llm_provider})
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.status}`);
        }
        
        const data = await response.json();

        loading.innerHTML="";
        
        // ===== LLM answer =====
        document.getElementById("answer").innerText = data.answer;

        // ===== Provider info badge =====
        const providerBadge = `
            <div class="provider-info">
                Answered by <strong>${data.provider}</strong>
                · ${data.top_k} card${data.top_k > 1 ? "s" : ""} used as context
            </div>
        `;
        document.getElementById("answer").insertAdjacentHTML("afterbegin", providerBadge);

        // ===== Show final_card if present =====
        if (data.final_card) {
            const card = data.final_card;

            const sections = [
                ["Cashback",                card.cashback],
                ["Petrol",                  card.petrol],
                ["Rewards",                 card.rewards],
                ["Travel",                  card.travel],
                ["Premium Perks",           card.premium_perks],
                ["Balance Transfer",        card.balance_transfer],
                ["Easy Payment Plans",      card.easy_payment_plan],
                ["Fees & Charges",          card.fees],
                ["Requirements",            card.requirements],
                ["Features",                card.features],
                ["Minimum Annual Income",   card.min_annual_income]
            ];

            // Only render sections that aren't N/A or empty
            const sectionsHTML = sections
                .filter(([_, value]) => value && value !== "N/A")
                .map(([label, value]) => `
                    <div class="detail-section">
                        <h3>${label}</h3>
                        <p>${value.replace(/\n/g, "<br>")}</p>
                    </div>
                `).join("");

            document.getElementById("card-result").innerHTML = `
                <div class="card-detail">
                    <div class="card-detail-header">
                        <h2>${card.card_title}</h2>
                        <span class="bank-badge">${card.bank}</span>
                    </div>
                    <div class="detail-grid">
                        ${sectionsHTML}
                    </div>
                </div>
            `;
        }
    } catch (err) {
        loading.innerHTML = "";
        document.getElementById("answer").innerText =
            `Something went wrong: ${err.message}`;
    } finally {
        askBtn.disabled = false;
    }
    
});