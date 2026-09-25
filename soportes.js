// ============================================
// Visor de soportes: abre un certificado y
// permite recorrer los de su misma categoría
// ============================================

(function () {
    const dialog = document.getElementById('viewer');
    if (!dialog || typeof dialog.showModal !== 'function') return;

    const img = document.getElementById('viewerImg');
    const title = document.getElementById('viewerTitle');
    const entity = document.getElementById('viewerEntity');
    const count = document.getElementById('viewerCount');
    const prev = document.getElementById('viewerPrev');
    const next = document.getElementById('viewerNext');
    const close = document.getElementById('viewerClose');

    let group = [];
    let index = 0;
    let opener = null;

    const show = (i) => {
        index = (i + group.length) % group.length;
        const doc = group[index];
        const t = doc.dataset.title;
        img.src = doc.dataset.full;
        img.alt = 'Certificado: ' + t;
        title.textContent = t;
        entity.textContent = doc.dataset.meta;
        count.textContent = (index + 1) + ' de ' + group.length;
        const single = group.length < 2;
        prev.hidden = single;
        next.hidden = single;
    };

    document.querySelectorAll('.doc').forEach((doc) => {
        doc.addEventListener('click', () => {
            group = [...document.querySelectorAll('.doc[data-cat="' + doc.dataset.cat + '"]')];
            opener = doc;
            show(group.indexOf(doc));
            dialog.showModal();
        });
    });

    prev.addEventListener('click', () => show(index - 1));
    next.addEventListener('click', () => show(index + 1));
    close.addEventListener('click', () => dialog.close());

    // Flechas del teclado solo mientras el visor está abierto
    dialog.addEventListener('keydown', (e) => {
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
        if (startX === null) return;
        const dx = e.changedTouches[0].clientX - startX;
        if (Math.abs(dx) > 50) show(index + (dx < 0 ? 1 : -1));
        startX = null;
    });

    dialog.addEventListener('close', () => {
        img.src = '';
        if (opener) opener.focus();
    });
})();
