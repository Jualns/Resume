document.addEventListener('DOMContentLoaded', () => {
    // Smooth scrolling for navigation links
    document.querySelectorAll('nav a').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();

            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);

            if (targetElement) {
                const navbarHeight = document.querySelector('.navbar').offsetHeight;
                const offsetTop = targetElement.offsetTop - navbarHeight - 20;

                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });

    // Optional: Add a subtle fade-in effect for sections on scroll
    const sectionCards = document.querySelectorAll('.section-card');

    const observerOptions = {
        root: null, // viewport
        rootMargin: '0px',
        threshold: 0.1 // Trigger when 10% of the item is visible
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = 1;
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target); // Stop observing once animated
            }
        });
    }, observerOptions);

    sectionCards.forEach(card => {
        card.style.opacity = 0;
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
        observer.observe(card);
    });

    // Garantir que todos os elementos sejam visíveis antes da impressão
    window.addEventListener('beforeprint', () => {
        sectionCards.forEach(card => {
            card.style.opacity = 1;
            card.style.transform = 'translateY(0)';
            card.style.transition = 'none'; // Remove transições para evitar atrasos
        });
    });

    // Opcional: Restaurar estado após impressão (se necessário)
    window.addEventListener('afterprint', () => {
        sectionCards.forEach(card => {
            card.style.opacity = 0; // Restaura o estado inicial
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
            observer.observe(card); // Reativa o observer
        });
    });

    // =============================================================
    // Código para Ano Dinâmico
    // -------------------------------------------------------------
    const elementoAno = document.getElementById('anoAtual');
    
    if (elementoAno) {
        const dataAtual = new Date();
        const ano = dataAtual.getFullYear();
        elementoAno.textContent = ano;
    }
    // =============================================================
});