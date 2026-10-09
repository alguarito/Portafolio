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

    // ===== COPIAR ENLACE DE UN ARTÍCULO =====
    document.querySelectorAll('[data-share="copiar"]').forEach(btn => {
        btn.addEventListener('click', () => {
            const label = btn.textContent;
            const done = () => { btn.textContent = 'Enlace copiado'; setTimeout(() => { btn.textContent = label; }, 2000); };
            if (navigator.clipboard) navigator.clipboard.writeText(btn.dataset.url).then(done, () => {});
        });
    });

    // ===== LECTURAS DE ARTÍCULOS =====
    // Contador en Abacus (sin cookies). Suma una vez por navegador y solo se muestra desde 50.
    const VIEWS_API = 'https://abacus.jasoncameron.dev';
    const VIEWS_NS = 'alvarocardenasorozco-com';
    const VIEWS_MIN = 50;
    document.querySelectorAll('[data-views]').forEach(el => {
        const slug = el.dataset.slug;
        let mode = 'get';
        if (el.dataset.views === 'hit' && !navigator.webdriver) {
            try {
                if (!localStorage.getItem('leido:' + slug)) { mode = 'hit'; localStorage.setItem('leido:' + slug, '1'); }
            } catch (e) { mode = 'hit'; }
        }
        fetch(`${VIEWS_API}/${mode}/${VIEWS_NS}/${slug}`)
            .then(r => (r.ok ? r.json() : null))
            .then(d => {
                const n = d && d.value;
                if (n >= VIEWS_MIN) { el.querySelector('span').textContent = n.toLocaleString('es-CO'); el.hidden = false; }
            })
            .catch(() => {});
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
