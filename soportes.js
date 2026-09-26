// ============================================
// Visor de soportes: cada botón abre el grupo
// de certificados que respalda ese ítem
// ============================================

(function () {
    const dialog = document.getElementById('viewer');
    const dataEl = document.getElementById('soportes-data');
    if (!dialog || !dataEl || typeof dialog.showModal !== 'function') return;

    const GROUPS = JSON.parse(dataEl.textContent);
    const img = document.getElementById('viewerImg');
    const title = document.getElementById('viewerTitle');
    const entity = document.getElementById('viewerEntity');
    const count = document.getElementById('viewerCount');
    const prev = document.getElementById('viewerPrev');
    const next = document.getElementById('viewerNext');
    const close = document.getElementById('viewerClose');

    let group = null;
    let index = 0;
    let opener = null;

    const show = (i) => {
        const n = group.s.length;
        index = (i + n) % n;
        img.src = 'assets/soportes/' + group.s[index] + '.jpg';
        img.alt = 'Certificado: ' + group.t;
        title.textContent = group.t;
        entity.textContent = group.m;
        count.textContent = n > 1 ? (index + 1) + ' de ' + n : '';
        prev.hidden = n < 2;
        next.hidden = n < 2;
    };

    document.querySelectorAll('[data-group]').forEach((btn) => {
        btn.addEventListener('click', () => {
            group = GROUPS[btn.dataset.group];
            if (!group) return;
            opener = btn;
            show(0);
            dialog.showModal();
        });
    });

    prev.addEventListener('click', () => show(index - 1));
    next.addEventListener('click', () => show(index + 1));
    close.addEventListener('click', () => dialog.close());

    // Flechas del teclado solo mientras el visor está abierto
    dialog.addEventListener('keydown', (e) => {
        if (!group || group.s.length < 2) return;
        if (e.key === 'ArrowLeft') { e.preventDefault(); show(index - 1); }
        if (e.key === 'ArrowRight') { e.preventDefault(); show(index + 1); }
    });

    // Cerrar al tocar el fondo oscuro
    dialog.addEventListener('click', (e) => {
        if (e.target === dialog) dialog.close();
    });

    // Deslizar con el dedo en el móvil
    let startX = null;
    dialog.addEventListener('touchstart', (e) => { startX = e.touches[0].clientX; }, { passive: true });
    dialog.addEventListener('touchend', (e) => {
        if (startX === null || !group || group.s.length < 2) return;
        const dx = e.changedTouches[0].clientX - startX;
        if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1));
        startX = null;
    });

    dialog.addEventListener('close', () => {
        img.src = '';
        if (opener) opener.focus();
    });
})();
