const search = document.getElementById("search");

search.addEventListener("input", function(){

    const keyword = search.value.toLowerCase();

    const cards = document.querySelectorAll(".card");

    cards.forEach(card=>{

        const text = card.innerText.toLowerCase();

        if(text.includes(keyword)){

            card.style.display="block";

        }else{

            card.style.display="none";

        }

    });

});