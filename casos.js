// ============================================
// Filtro de casos por área. Lee el ancla
// (#desarrollo, #diseno, #ia, #educacion)
// para llegar filtrado desde la portada.
// ============================================

(function () {
    const chips = document.querySelectorAll('.cs-chip');
    const items = document.querySelectorAll('#casos-lista .cs, .cs-index li');
    if (!chips.length) return;
    const AREAS = ['educacion', 'desarrollo', 'diseno', 'ia'];

    const apply = (f) => {
        chips.forEach((c) => c.setAttribute('aria-pressed', String(c.dataset.f === f)));
        items.forEach((el) => {
            el.hidden = f !== 'todos' && el.dataset.a.split(' ').indexOf(f) === -1;
        });
    };

    chips.forEach((c) => c.addEventListener('click', () => {
        apply(c.dataset.f);
        const url = c.dataset.f === 'todos' ? location.pathname : '#' + c.dataset.f;
        history.replaceState(null, '', url);
    }));

    const fromHash = () => {
        const h = location.hash.slice(1);
        if (AREAS.indexOf(h) > -1) {
            apply(h);
            document.querySelector('.cs-filter').scrollIntoView({ block: 'start' });
        }
    };
    fromHash();
    window.addEventListener('hashchange', fromHash);
})();
