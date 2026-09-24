// ============================================
// Álvaro Cárdenas Orozco — sitio personal
// Menú móvil y aparición al desplazarse
// ============================================

document.addEventListener('DOMContentLoaded', () => {

    // ===== MENÚ MÓVIL =====
    const toggle = document.getElementById('navToggle');
    const links = document.getElementById('navLinks');

    const setMenu = (open) => {
        links.classList.toggle('open', open);
        toggle.setAttribute('aria-expanded', String(open));
        toggle.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú');
    };

    toggle.addEventListener('click', () => setMenu(!links.classList.contains('open')));
    links.querySelectorAll('a').forEach(a => a.addEventListener('click', () => setMenu(false)));
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && links.classList.contains('open')) {
            setMenu(false);
            toggle.focus();
        }
    });

    // ===== APARICIÓN AL DESPLAZARSE =====
    const items = document.querySelectorAll('.reveal');
    if (!('IntersectionObserver' in window)) {
        items.forEach(el => el.classList.add('visible'));
        return;
    }
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });

    // Escalonar las tarjetas dentro de cada rejilla
    document.querySelectorAll('.hero, .services, .quotes').forEach(grid => {
        grid.querySelectorAll('.reveal').forEach((el, i) => {
            el.style.transitionDelay = `${i * 0.08}s`;
        });
    });

    items.forEach(el => observer.observe(el));
});
