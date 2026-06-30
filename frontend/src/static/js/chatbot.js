const askBtn = document.getElementById("askBtn");

askBtn.addEventListener("click", async ()=>{

    const question =
        document.getElementById("question").value;

    const loading =
        document.getElementById("loading");

    loading.innerHTML="Thinking...";

    const response = await fetch("/api/ask",{

        method:"POST",

        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify({
            question:question
        })

    });

    const data = await response.json();

    loading.innerHTML="";

    document.getElementById("answer").innerText =
        data.answer;

});