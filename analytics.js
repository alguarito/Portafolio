// ============================================
// Google Analytics 4 con modo de consentimiento
// Nada se guarda en cookies hasta que el visitante acepte
// ============================================

(function () {
    var GA_ID = 'G-4YRT62L3FT';
    var KEY = 'consentimiento-analitica';

    window.dataLayer = window.dataLayer || [];
    function gtag() { dataLayer.push(arguments); }
    window.gtag = gtag;

    var saved = null;
    try { saved = localStorage.getItem(KEY); } catch (e) {}

    // Por defecto, sin cookies de analítica ni publicidad
    gtag('consent', 'default', {
        analytics_storage: saved === 'si' ? 'granted' : 'denied',
        ad_storage: 'denied',
        ad_user_data: 'denied',
        ad_personalization: 'denied',
        wait_for_update: 500
    });
    gtag('js', new Date());
    gtag('config', GA_ID);

    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);

    function decide(value) {
        try { localStorage.setItem(KEY, value); } catch (e) {}
        gtag('consent', 'update', { analytics_storage: value === 'si' ? 'granted' : 'denied' });
        var bar = document.getElementById('cookieBar');
        if (bar) bar.remove();
    }

    function banner() {
        if (saved) return;
        var bar = document.createElement('div');
        bar.id = 'cookieBar';
        bar.className = 'cookie-bar';
        bar.setAttribute('role', 'region');
        bar.setAttribute('aria-label', 'Aviso de cookies');
        bar.innerHTML =
            '<p>Uso Google Analytics para saber qué partes del sitio le sirven a la gente. ¿Me permite medir su visita con cookies?</p>' +
            '<div class="cookie-actions">' +
            '<button type="button" class="btn btn-ink" data-c="si">Aceptar</button>' +
            '<button type="button" class="btn btn-line" data-c="no">Rechazar</button>' +
            '</div>';
        bar.addEventListener('click', function (e) {
            var v = e.target.closest('[data-c]');
            if (v) decide(v.dataset.c);
        });
        document.body.appendChild(bar);
    }

    // Eventos de conversión: clics que importan
    function track(e) {
        var a = e.target.closest('a, button');
        if (!a) return;
        var href = a.getAttribute('href') || '';
        var label = (a.getAttribute('aria-label') || a.textContent || '').trim().slice(0, 100);
        if (a.dataset && a.dataset.share) gtag('event', 'compartir_articulo', { red: a.dataset.share, pagina: location.pathname });
        else if (a.hasAttribute('data-libro')) gtag('event', 'abrir_libro', { libro: a.getAttribute('href'), ubicacion: 'articulo' });
        else if (a.hasAttribute('data-fb-post')) gtag('event', 'opinar_facebook', { pagina: location.pathname });
        else if (href.indexOf('calendly.com') > -1) gtag('event', 'agendar_conversacion', { ubicacion: label });
        else if (href.indexOf('wa.me') > -1) gtag('event', 'contacto_whatsapp', { ubicacion: label });
        else if (href.indexOf('mailto:') === 0) gtag('event', 'contacto_correo');
        else if (href.indexOf('.pdf') > -1) gtag('event', 'descargar_hoja_de_vida', { version: href.indexOf('edtech') > -1 ? 'edtech' : 'academica' });
        else if (href.indexOf('doi.org') > -1 || href.indexOf('zenodo.org') > -1) gtag('event', 'abrir_libro', { libro: label });
        else if (a.dataset && a.dataset.group) gtag('event', 'ver_certificado', { certificado: label });
        else if (/linkedin|facebook|orcid/.test(href)) gtag('event', 'abrir_perfil', { perfil: href.split('/')[2] });
    }

    document.addEventListener('click', track);
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', banner);
    else banner();
})();
