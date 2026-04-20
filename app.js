// ============================================
// PORTAFOLIO DE SERVICIOS — Dr. Álvaro Cárdenas
// Interactive Logic (Vanilla JS)
// ============================================

document.addEventListener('DOMContentLoaded', () => {

    // ===== NAVIGATION SCROLL =====
    const nav = document.getElementById('mainNav');
    window.addEventListener('scroll', () => {
        nav.classList.toggle('scrolled', window.scrollY > 60);
    });

    // ===== MOBILE MENU =====
    const navToggle = document.getElementById('navToggle');
    const navLinks = document.getElementById('navLinks');

    navToggle.addEventListener('click', () => {
        navLinks.classList.toggle('active');
        navToggle.classList.toggle('open');
    });

    navLinks.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', () => {
            navLinks.classList.remove('active');
            navToggle.classList.remove('open');
        });
    });

    // ===== SCROLL REVEAL =====
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });

    document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

    // ===== STAGGERED REVEAL =====
    document.querySelectorAll('.services-grid, .testimonials-grid, .packages-grid, .why-grid').forEach(container => {
        container.querySelectorAll('.reveal').forEach((card, i) => {
            card.style.transitionDelay = `${i * 0.12}s`;
        });
    });

    // ===== METRIC COUNTERS =====
    const metricNumbers = document.querySelectorAll('.metric-number[data-target]');

    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const target = parseInt(el.getAttribute('data-target'));
                animateCount(el, target);
                counterObserver.unobserve(el);
            }
        });
    }, { threshold: 0.5 });

    metricNumbers.forEach(el => counterObserver.observe(el));

    function animateCount(el, target) {
        let current = 0;
        const increment = Math.max(1, Math.ceil(target / 50));
        const duration = 1500;
        const stepTime = duration / (target / increment);

        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                current = target;
                clearInterval(timer);
            }
            el.textContent = current + (target >= 10 ? '+' : '');
        }, stepTime);
    }

    // ===== HERO STAT COUNTERS =====
    const heroStats = document.querySelectorAll('.stat-number');

    const heroStatObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const text = el.textContent.trim();
                const hasPlus = text.includes('+');
                const target = parseInt(text.replace('+', ''));

                let current = 0;
                const increment = Math.max(1, Math.ceil(target / 40));
                const stepTime = 1200 / (target / increment);

                const timer = setInterval(() => {
                    current += increment;
                    if (current >= target) {
                        current = target;
                        clearInterval(timer);
                    }
                    el.textContent = current + (hasPlus ? '+' : '');
                }, stepTime);

                heroStatObserver.unobserve(el);
            }
        });
    }, { threshold: 0.5 });

    heroStats.forEach(stat => heroStatObserver.observe(stat));

    // ===== HERO PARALLAX =====
    const heroImage = document.querySelector('.hero-image');
    const heroAccent = document.querySelector('.hero-image-accent');

    window.addEventListener('scroll', () => {
        const scrolled = window.scrollY;
        if (heroImage && scrolled < window.innerHeight) {
            heroImage.style.transform = `translateY(${scrolled * 0.06}px)`;
            heroAccent.style.transform = `translateY(${scrolled * 0.1}px)`;
        }
    });

    // ===== ACTIVE NAV LINK =====
    const sections = document.querySelectorAll('[id]');
    const allNavLinks = document.querySelectorAll('.nav-links a');

    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            const top = section.offsetTop - 200;
            if (window.scrollY >= top) {
                current = section.getAttribute('id');
            }
        });
        allNavLinks.forEach(link => {
            link.style.color = '';
            if (link.getAttribute('href') === '#' + current) {
                link.style.color = '#c9a96e';
            }
        });
    });

});

// ===== SERVICE CARD TOGGLE (Global) =====
function toggleService(cardId) {
    const card = document.getElementById(cardId);
    card.classList.toggle('expanded');
}
