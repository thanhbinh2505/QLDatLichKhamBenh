document.addEventListener("DOMContentLoaded", function() {
//    vẽ icon
    lucide.createIcons();

});

    window.scrollDoctors = function(direction) {
        const container = document.getElementById('doctor-container');
        if (!container) {
            return;
        }
        const firstCard = container.querySelector('div');
        if (!firstCard) {
            return;
        }
        const scrollAmount = firstCard.offsetWidth + 24;
        if (direction === 'left') {
            container.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
        } else {
            container.scrollBy({ left: scrollAmount, behavior: 'smooth' });
        }
    };
