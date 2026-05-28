 // Automatikusan eltünteti az alert üzeneteket 3 másodperc után
    document.addEventListener('DOMContentLoaded', () => {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            setTimeout(() => {
                alert.classList.remove('show'); // Animáció kezdete
                alert.classList.add('fade');  // Opció: csak fade
                setTimeout(() => alert.remove(), 150); // Eltávolítja az elemet 150ms után
            }, 3000); // 3 másodperc
        });
    });