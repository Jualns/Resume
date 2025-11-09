document.addEventListener('DOMContentLoaded', () => {
    // Smooth scrolling for navigation links (somente para links internos)
    document.querySelectorAll('nav a').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');

            // Só intercepta links internos (#)
            if (href && href.startsWith('#')) {
                e.preventDefault();

                const targetElement = document.querySelector(href);

                if (targetElement) {
                    const navbarHeight = document.querySelector('.navbar').offsetHeight;
                    const offsetTop = targetElement.offsetTop - navbarHeight - 20;

                    window.scrollTo({
                        top: offsetTop,
                        behavior: 'smooth'
                    });
                }
            }
            // Caso contrário (links externos), o comportamento padrão é mantido
        });
    });

    // Fade-in para seções ao rolar a página
    const sectionCards = document.querySelectorAll('.section-card');

    const observerOptions = {
        root: null, // viewport
        rootMargin: '0px',
        threshold: 0.1 // Trigger quando 10% estiver visível
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = 1;
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target); // Para de observar após animar
            }
        });
    }, observerOptions);

    sectionCards.forEach(card => {
        card.style.opacity = 0;
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
        observer.observe(card);
    });

    // Garante que todos os elementos fiquem visíveis antes da impressão
    window.addEventListener('beforeprint', () => {
        sectionCards.forEach(card => {
            card.style.opacity = 1;
            card.style.transform = 'translateY(0)';
            card.style.transition = 'none'; // Remove transições para evitar atrasos
        });
    });

    // Restaura estado após impressão (opcional)
    window.addEventListener('afterprint', () => {
        sectionCards.forEach(card => {
            card.style.opacity = 0; // Restaura o estado inicial
            card.style.transform = 'translateY(20px)';
            card.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
            observer.observe(card); // Reativa o observer
        });
    });

    // =============================================================
    // Atualiza o ano dinamicamente no rodapé
    // -------------------------------------------------------------
    const elementoAno = document.getElementById('anoAtual');
    
    if (elementoAno) {
        const dataAtual = new Date();
        const ano = dataAtual.getFullYear();
        elementoAno.textContent = ano;
    }
    // =============================================================
});
