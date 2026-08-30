document.addEventListener("DOMContentLoaded",()=>{
    const countdown = document.querySelector(".live-countdown");

    if (!countdown)return;

    // Fecha de ejemplo del proximo live.
    // Mas adelante esta fecha vendra desde el panel del administrador.

    const liveDate = new Date("2026-09-06T20:00:00");

    const units = countdown.querySelectorAll("strong");

    function updateCountdown(){
        const now = new Date();
        const difference = liveDate - now;

        if (difference <= 0){
            units[0].textContent = "00";
            units[1].textContent = "00";
            units[2].textContent = "00";
            units[3].textContent = "00";
            
            return;
        }

        const days = Math.floor(difference/(1000*60*60*24));
        const hours = Math.floor(
            (difference / (1000*60)) % 24
        );
        const minutes = Math.floor(
            (difference / (100*60)) % 60
        )

        const seconds = Math.floor(
            (difference/1000) % 60
        );
        units[0].textContent = String(days).padStart(2, "0");
        units[1].textContent = String(hours).padStart(2, "0");
        units[2].textContent = String(minutes).padStart(2, "0");
        units[3].textContent = String(seconds).padStart(2, "0");
    }

    updateCountdown();
    setInterval(updateCountdown,1000);

});
