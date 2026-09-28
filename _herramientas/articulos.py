#!/usr/bin/env python3
"""Construye la sección de artículos del sitio.

Fuente: _articulos/<slug>.md con encabezado (entre líneas ---) y cuerpo en
Markdown sencillo. Las carpetas que empiezan por «_» no se publican.

Genera:
  articulos/index.html          listado
  articulos/<slug>.html         cada artículo
  assets/articulos/<slug>.jpg   imagen (1600 px) y <slug>-og.jpg (1200×630)
  feed.xml                      RSS
y actualiza, entre marcadores, sitemap.xml, llms.txt, la portada y el menú.

Uso: python3 _herramientas/articulos.py
"""
import html, json, os, re, subprocess, sys
from datetime import date, datetime
from email.utils import format_datetime
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://alvarocardenasorozco.com'
CAL = 'https://calendly.com/alvaro-cardenas-orozco/30min'
FB_PAGE = 'https://www.facebook.com/Profe.AlvaroCardenas2021/'
CSS_V = None  # se lee de index.html para usar la misma versión
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
         'septiembre', 'octubre', 'noviembre', 'diciembre']
SERVICIOS = {
    'formacion-docente-ia': 'Formación docente en IA',
    'educacion-stem-steam': 'Educación STEM y STEAM',
    'desarrollo-a-medida': 'Desarrollo a medida',
    'diseno-editorial': 'Diseño editorial',
    'asesoria-de-tesis': 'Asesoría de tesis',
    'conferencias': 'Conferencias',
}
ARROW = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'


def p(*parts):
    return os.path.join(ROOT, *parts)


def esc(t):
    return html.escape(str(t), quote=True)


def fecha_larga(d):
    return f'{d.day} de {MESES[d.month - 1]} de {d.year}'


# ---------- Markdown mínimo ----------

def inline(t):
    t = esc(t)
    t = re.sub(r'!\[([^\]]*)\]\(([^)\s]+)\)', r'<img src="\2" alt="\1" loading="lazy">', t)
    t = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', lambda m: link(m.group(1), m.group(2)), t)
    t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
    t = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', t)
    t = re.sub(r'(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])', r'<em>\1</em>', t)
    return t


def strip(t):
    return re.sub(r'[*_]', '', t)


def link(text, href):
    ext = href.startswith('http') and not href.startswith(BASE)
    extra = ' target="_blank" rel="noopener"' if ext else ''
    return f'<a href="{href}"{extra}>{text}</a>'


def slugify(t):
    t = t.lower()
    for a, b in zip('áéíóúüñ', 'aeiouun'):
        t = t.replace(a, b)
    t = re.sub(r'[^a-z0-9]+', '-', t).strip('-')
    return t[:60].strip('-')


def markdown(src):
    """Devuelve (html, encabezados [(id, texto)], palabras)."""
    out, heads, para, lst, lst_tag, quote_buf = [], [], [], [], None, []
    words = len(re.findall(r'\w+', src))

    def flush():
        nonlocal para, lst, lst_tag, quote_buf
        if para:
            out.append('<p>' + inline(' '.join(para)) + '</p>')
            para = []
        if lst:
            out.append(f'<{lst_tag}>' + ''.join(f'<li>{inline(i)}</li>' for i in lst) + f'</{lst_tag}>')
            lst, lst_tag = [], None
        if quote_buf:
            out.append('<blockquote><p>' + inline(' '.join(quote_buf)) + '</p></blockquote>')
            quote_buf = []

    for raw in src.splitlines():
        line = raw.rstrip()
        s = line.strip()
        if not s:
            flush(); continue
        m = re.match(r'^(#{2,3})\s+(.*)', s)
        if m:
            flush()
            level, text = len(m.group(1)), m.group(2).strip()
            hid = slugify(text)
            if level == 2:
                heads.append((hid, text))
            out.append(f'<h{level} id="{hid}">{inline(text)}</h{level}>')
            continue
        if re.match(r'^(-{3,}|\*{3,})$', s):
            flush(); out.append('<hr>'); continue
        if s.startswith('>'):
            if para or lst: flush()
            quote_buf.append(s.lstrip('> ').strip()); continue
        m = re.match(r'^([-*•])\s+(.*)', s)
        n = re.match(r'^\d+[.)]\s+(.*)', s)
        if m or n:
            tag = 'ul' if m else 'ol'
            if para or quote_buf or (lst and lst_tag != tag): flush()
            lst_tag = tag
            lst.append((m or n).group(2 if m else 1)); continue
        if lst or quote_buf: flush()
        para.append(s)
    flush()
    return '\n'.join(out), heads, words


# ---------- Fuente ----------

def leer(ruta):
    with open(ruta, encoding='utf-8') as f:
        txt = f.read()
    m = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', txt, re.S)
    if not m:
        sys.exit(f'{ruta}: falta el encabezado entre líneas ---')
    meta = {}
    for line in m.group(1).splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            meta[k.strip()] = v.strip()
    a = dict(meta)
    a['slug'] = os.path.splitext(os.path.basename(ruta))[0]
    a['cuerpo_md'] = m.group(2).strip()
    for req in ('titulo', 'fecha', 'descripcion'):
        if not a.get(req):
            sys.exit(f'{ruta}: falta «{req}»')
    if len(a['descripcion']) > 160:
        print(f'  aviso: la descripción de {a["slug"]} tiene {len(a["descripcion"])} caracteres; Google corta cerca de 155')
    a['fecha_d'] = datetime.strptime(a['fecha'], '%Y-%m-%d').date()
    a['actualizado_d'] = datetime.strptime(a.get('actualizado', a['fecha']), '%Y-%m-%d').date()
    a['claves'] = [k.strip() for k in a.get('palabras_clave', '').split(',') if k.strip()]
    if a.get('servicio') and a['servicio'] not in SERVICIOS:
        sys.exit(f'{ruta}: servicio «{a["servicio"]}» no existe ({", ".join(SERVICIOS)})')
    a['cuerpo'], a['heads'], a['palabras'] = markdown(a['cuerpo_md'])
    a['lectura'] = max(1, round(a['palabras'] / 200))
    a['url'] = f'{BASE}/articulos/{a["slug"]}.html'
    a['titulo_seo'] = a.get('titulo_seo') or a['titulo']
    if len(a['titulo_seo']) > 65:
        print(f'  aviso: el título para buscadores de {a["slug"]} tiene {len(a["titulo_seo"])} caracteres; conviene «titulo_seo» de hasta 65')
    return a


def imagen(a):
    """Prepara la imagen del artículo con sips (macOS)."""
    src = a.get('imagen')
    if not src:
        a['img'] = a['og'] = None
        return
    src = src if os.path.isabs(src) else p(src)
    if not os.path.exists(src):
        sys.exit(f'{a["slug"]}: no encuentro la imagen {src}')
    os.makedirs(p('assets', 'articulos'), exist_ok=True)
    dst = p('assets', 'articulos', a['slug'] + '.jpg')
    og = p('assets', 'articulos', a['slug'] + '-og.jpg')
    if not os.path.exists(dst) or os.path.getmtime(src) > os.path.getmtime(dst):
        sw, sh = dims(src)
        cmd = ['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', '72']
        if max(sw, sh) > 1600:
            cmd += ['-Z', '1600']  # solo reduce, nunca agranda
        run(cmd + [src, '--out', dst])
        w, h = dims(dst)
        tmp = og + '.tmp.jpg'
        if w / h > 1200 / 630:
            run(['sips', '--resampleHeight', '630', dst, '--out', tmp])
        else:
            run(['sips', '--resampleWidth', '1200', dst, '--out', tmp])
        run(['sips', '-c', '630', '1200', '-s', 'formatOptions', '72', tmp, '--out', og])
        os.remove(tmp)
    a['img'] = f'/assets/articulos/{a["slug"]}.jpg'
    a['og'] = f'/assets/articulos/{a["slug"]}-og.jpg'
    a['img_w'], a['img_h'] = dims(dst)


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def dims(f):
    out = subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', f], capture_output=True, text=True).stdout
    return int(re.search(r'pixelWidth: (\d+)', out).group(1)), int(re.search(r'pixelHeight: (\d+)', out).group(1))


# ---------- Plantilla ----------

def shell_parts():
    with open(p('casos.html'), encoding='utf-8') as f:
        s = f.read()
    global CSS_V
    CSS_V = re.search(r'style\.css\?v=(\d+)', s).group(1)
    nav = s[s.index('<nav class="nav"'):s.index('</nav>', s.index('<div class="nav-links"')) + 6]
    nav = nav.replace(' aria-current="page"', '')
    tail = s[s.index('<footer class="footer">'):].replace('<script src="casos.js"></script>\n', '')
    for a in ['href="./"', 'href="./#', 'href="casos.html', 'src="app.js"']:
        nav = nav.replace(a, a.replace('"./', '"/').replace('"casos', '"/casos').replace('"app', '"/app'))
        tail = tail.replace(a, a.replace('"./', '"/').replace('"casos', '"/casos').replace('"app', '"/app'))
    nav = re.sub(r'href="(?!https?:|/|#)([a-z-]+\.html)', r'href="/\1', nav)
    tail = re.sub(r'href="(?!https?:|/|#|mailto)([a-z-]+\.html)', r'href="/\1', tail)
    return nav, tail


def head(title, desc, url, og_img, og_type, ld, extra=''):
    return f'''<!DOCTYPE html>
<html lang="es-CO">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="author" content="Álvaro Cárdenas Orozco">
<link rel="canonical" href="{url}">
<link rel="alternate" type="application/rss+xml" title="Artículos de Álvaro Cárdenas Orozco" href="{BASE}/feed.xml">
<meta name="theme-color" content="#f1f0ec">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<meta property="og:type" content="{og_type}">
<meta property="og:locale" content="es_CO">
<meta property="og:site_name" content="Álvaro Cárdenas Orozco">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:image" content="{BASE}{og_img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
{extra}<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/style.css?v={CSS_V}">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, indent=1)}</script>
<script src="/analytics.js" defer></script>
</head>
<body>
<div class="wrap">
'''


def compartir(a):
    u = quote(a['url'], safe='')
    t = quote(a['titulo'], safe='')
    return (f'<div class="ar-share" aria-label="Compartir">'
            f'<span class="mono muted">Compartir</span>'
            f'<a data-share="facebook" href="https://www.facebook.com/sharer/sharer.php?u={u}" target="_blank" rel="noopener">Facebook</a>'
            f'<a data-share="whatsapp" href="https://wa.me/?text={t}%20{u}" target="_blank" rel="noopener">WhatsApp</a>'
            f'<a data-share="linkedin" href="https://www.linkedin.com/sharing/share-offsite/?url={u}" target="_blank" rel="noopener">LinkedIn</a>'
            f'<button type="button" data-share="copiar" data-url="{a["url"]}">Copiar enlace</button>'
            f'</div>')


def pagina_articulo(a, nav, tail, otros):
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'BlogPosting', '@id': a['url'] + '#articulo', 'headline': a['titulo_seo'], 'name': a['titulo'],
         'description': a['descripcion'], 'url': a['url'], 'mainEntityOfPage': a['url'],
         'datePublished': a['fecha_d'].isoformat(), 'dateModified': a['actualizado_d'].isoformat(),
         'inLanguage': 'es-CO', 'wordCount': a['palabras'],
         'author': {'@id': BASE + '/#persona'}, 'publisher': {'@id': BASE + '/#persona'},
         **({'image': {'@type': 'ImageObject', 'url': BASE + a['img'], 'width': a['img_w'], 'height': a['img_h']}} if a['img'] else {}),
         **({'keywords': a['claves']} if a['claves'] else {}),
         **({'articleSection': SERVICIOS[a['servicio']]} if a.get('servicio') else {}),
         **({'discussionUrl': a['facebook']} if a.get('facebook') else {}),
         **({'isBasedOn': {'@type': 'Book', 'name': strip(a['libro_titulo']), 'url': a['libro_url'],
                           'author': {'@id': BASE + '/#persona'}}} if a.get('libro_url') else {}),
         'isPartOf': {'@id': BASE + '/articulos/#blog'}},
        {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Inicio', 'item': BASE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Artículos', 'item': BASE + '/articulos/'},
            {'@type': 'ListItem', 'position': 3, 'name': a['titulo'], 'item': a['url']}]},
        {'@type': 'Person', '@id': BASE + '/#persona', 'name': 'Álvaro Cárdenas Orozco', 'url': BASE + '/'},
    ]}
    extra = (f'<meta property="article:published_time" content="{a["fecha_d"].isoformat()}">\n'
             f'<meta property="article:modified_time" content="{a["actualizado_d"].isoformat()}">\n'
             f'<meta property="article:author" content="{FB_PAGE}">\n'
             + ''.join(f'<meta property="article:tag" content="{esc(k)}">\n' for k in a['claves']))
    og_img = a['og'] or '/assets/og.jpg'
    out = head(f'{a["titulo_seo"]} | Álvaro Cárdenas Orozco', a['descripcion'], a['url'], og_img, 'article', ld, extra)
    out += nav + '\n<main>\n<article class="ar">\n<header class="ar-head">\n'
    out += f'  <nav class="mono muted sv-crumbs" aria-label="Ruta"><a href="/">Inicio</a> / <a href="/articulos/">Artículos</a></nav>\n'
    if a.get('servicio'):
        out += f'  <a class="chip mono ar-tag" href="/{a["servicio"]}.html">{esc(SERVICIOS[a["servicio"]])}</a>\n'
    out += f'  <h1>{inline(a["titulo"])}</h1>\n  <p class="ar-lead">{inline(a.get("bajada") or a["descripcion"])}</p>\n'
    out += (f'  <p class="mono muted ar-meta">Por <a href="/#sobre-mi">Dr. Álvaro Cárdenas Orozco</a> · '
            f'<time datetime="{a["fecha_d"].isoformat()}">{fecha_larga(a["fecha_d"])}</time> · {a["lectura"]} min de lectura</p>\n')
    if a.get('libro_url'):
        out += (f'  <a class="ar-basis" data-libro href="{a["libro_url"]}" target="_blank" rel="noopener">'
                f'<span class="mono">Basado en el libro</span><strong>{inline(a["libro_titulo"])}</strong>'
                f'<span>{esc(a.get("libro_serie", ""))}{" · " if a.get("libro_serie") else ""}Leer gratis en Zenodo →</span></a>\n')
    out += '</header>\n'
    if a['img']:
        out += (f'<figure class="ar-fig"><img src="{a["img"]}" alt="{esc(a.get("imagen_alt") or a["titulo"])}" '
                f'width="{a["img_w"]}" height="{a["img_h"]}" fetchpriority="high"></figure>\n')
    out += '<div class="ar-layout">\n'
    if len(a['heads']) >= 3:
        out += ('<nav class="ar-toc" aria-label="En este artículo"><span class="mono muted">En este artículo</span><ol>'
                + ''.join(f'<li><a href="#{i}">{inline(t)}</a></li>' for i, t in a['heads']) + '</ol></nav>\n')
    out += f'<div class="ar-body">\n{a["cuerpo"]}\n</div>\n</div>\n'
    if a.get('libro_url'):
        port = (f'<img src="{a["libro_portada"]}" alt="Portada del libro {esc(a["libro_titulo"])}" width="637" height="900" loading="lazy">'
                if a.get('libro_portada') else '')
        out += (f'<aside class="ar-book">{port}<div><span class="mono">El libro</span>'
                f'<h2>{inline(a["libro_titulo"])}</h2>'
                + (f'<p class="ar-book-sub">{inline(a["libro_subtitulo"])}</p>' if a.get('libro_subtitulo') else '')
                + (f'<p>{esc(a["libro_serie"])}. Acceso abierto, con licencia CC BY-SA 4.0.</p>' if a.get('libro_serie') else '')
                + f'<div class="sv-cta"><a class="btn btn-ink" data-libro href="{a["libro_url"]}" target="_blank" rel="noopener">Descargar el libro gratis</a>'
                f'<a class="btn btn-line" href="https://zenodo.org/communities/coleccion-milc/records" target="_blank" rel="noopener">Ver la colección</a></div></div></aside>\n')
    out += compartir(a) + '\n'
    # Conversación en Facebook
    if a.get('facebook'):
        out += (f'<section class="ar-talk" id="opiniones"><h2>¿Qué opina <span class="it">usted?</span></h2>'
                f'<p>La conversación sobre este artículo está en mi página de Facebook. Deje allí su opinión, su pregunta o su experiencia.</p>'
                f'<a class="btn btn-ink" data-fb-post href="{a["facebook"]}" target="_blank" rel="noopener">Opinar en Facebook</a></section>\n')
    else:
        out += (f'<section class="ar-talk" id="opiniones"><h2>¿Qué opina <span class="it">usted?</span></h2>'
                f'<p>Comparta este artículo en Facebook con su opinión, o escríbame directamente: leo cada mensaje.</p>'
                f'<div class="sv-cta"><a class="btn btn-ink" data-share="facebook" href="https://www.facebook.com/sharer/sharer.php?u={quote(a["url"], safe="")}" target="_blank" rel="noopener">Opinar en Facebook</a>'
                f'<a class="btn btn-line" href="{FB_PAGE}" target="_blank" rel="noopener">Seguir la página</a></div></section>\n')
    # Autor y servicio
    serv = a.get('servicio')
    out += ('<aside class="ar-author"><img src="/assets/alvaro-cardenas-orozco.jpg" alt="Álvaro Cárdenas Orozco" width="96" height="96" loading="lazy">'
            '<div><strong>Dr. Álvaro Cárdenas Orozco</strong><p>Ingeniero de sistemas, doctor en Ciencias de la Educación y autor de la Colección MILC. '
            'Docente de posgrado en la Universidad Tecnológica de Pereira.</p>'
            + (f'<a class="link-strong" href="/{serv}.html">{esc(SERVICIOS[serv])}: ver el servicio →</a>' if serv else
               '<a class="link-strong" href="/#servicios">Ver los servicios →</a>')
            + '</div></aside>\n')
    out += '</article>\n'
    if otros:
        out += '<section class="section"><div class="section-head"><h2>Otros <span class="it">artículos.</span></h2></div><div class="ar-grid">'
        out += ''.join(tarjeta(o) for o in otros[:3]) + '</div></section>\n'
    out += '</main>\n\n\n' + tail
    return out


def tarjeta(a, cls='ar-card'):
    img = (f'<span class="ar-card-img"><img src="{a["img"]}" alt="" loading="lazy"></span>' if a['img'] else '')
    tag = f'<span class="mono muted">{esc(SERVICIOS[a["servicio"]])}</span>' if a.get('servicio') else ''
    return (f'<a class="{cls} reveal" href="/articulos/{a["slug"]}.html">{img}<span class="ar-card-body">{tag}'
            f'<span class="ar-card-t">{inline(a["titulo"])}</span><span class="ar-card-d">{esc(a["descripcion"])}</span>'
            f'<span class="mono muted">{fecha_larga(a["fecha_d"])} · {a["lectura"]} min</span></span></a>')


def pagina_listado(arts, nav, tail):
    url = BASE + '/articulos/'
    desc = 'Artículos del Dr. Álvaro Cárdenas Orozco sobre inteligencia artificial en la educación, educación STEM y STEAM, desarrollo de software y diseño editorial.'
    ld = {'@context': 'https://schema.org', '@graph': [
        {'@type': 'Blog', '@id': url + '#blog', 'name': 'Artículos de Álvaro Cárdenas Orozco', 'url': url,
         'description': desc, 'inLanguage': 'es-CO', 'author': {'@id': BASE + '/#persona'},
         'blogPost': [{'@id': a['url'] + '#articulo'} for a in arts]},
        {'@type': 'Person', '@id': BASE + '/#persona', 'name': 'Álvaro Cárdenas Orozco', 'url': BASE + '/'}]}
    out = head('Artículos | Álvaro Cárdenas Orozco: IA, educación y tecnología', desc, url, '/assets/og.jpg', 'website', ld,
               '' if arts else '<meta name="robots" content="noindex">\n')
    out += nav + '\n<main>\n<header class="s-hero">\n'
    out += '  <nav class="mono muted sv-crumbs" aria-label="Ruta"><a href="/">Inicio</a> / <span>Artículos</span></nav>\n'
    out += '  <h1>Artículos sobre IA, <span class="it">educación y tecnología.</span></h1>\n'
    out += '  <p>Ideas, métodos y casos del aula y del taller: inteligencia artificial en la educación, educación STEM y STEAM, desarrollo a medida y diseño editorial.</p>\n'
    out += f'  <div class="sv-cta"><a class="btn btn-line" href="/feed.xml">Suscribirse por RSS</a><a class="btn btn-line" href="{FB_PAGE}" target="_blank" rel="noopener">Seguir en Facebook</a></div>\n</header>\n'
    if arts:
        out += '<section class="ar-list">' + tarjeta(arts[0], 'ar-card ar-card-first') + '<div class="ar-grid">' + ''.join(tarjeta(a) for a in arts[1:]) + '</div></section>\n'
    else:
        out += '<section class="ar-empty"><p>El primer artículo está en preparación.</p></section>\n'
    out += '</main>\n\n\n' + tail
    return out


def feed(arts):
    items = ''
    for a in arts[:20]:
        dt = datetime.combine(a['fecha_d'], datetime.min.time()).astimezone()
        items += (f'<item><title>{esc(a["titulo"])}</title><link>{a["url"]}</link><guid>{a["url"]}</guid>'
                  f'<pubDate>{format_datetime(dt)}</pubDate><description>{esc(a["descripcion"])}</description></item>\n')
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel>\n'
            f'<title>Artículos de Álvaro Cárdenas Orozco</title><link>{BASE}/articulos/</link>'
            f'<atom:link href="{BASE}/feed.xml" rel="self" type="application/rss+xml"/>'
            f'<description>IA, educación y tecnología</description><language>es-co</language>\n{items}</channel></rss>\n')


def reemplazar_entre(ruta, ini, fin, contenido):
    with open(ruta, encoding='utf-8') as f:
        s = f.read()
    if ini not in s:
        sys.exit(f'{ruta}: falta el marcador {ini}')
    a, b = s.index(ini) + len(ini), s.index(fin)
    s = s[:a] + contenido + s[b:]
    with open(ruta, 'w', encoding='utf-8') as f:
        f.write(s)


def menu(hay):
    """Agrega o quita «Artículos» del menú de todas las páginas."""
    link = '<a href="/articulos/" data-nav="articulos">Artículos</a>'
    for dirpath, _, files in os.walk(ROOT):
        if any(part.startswith(('.', '_')) for part in os.path.relpath(dirpath, ROOT).split(os.sep) if part != '.'):
            continue
        for fn in files:
            if not fn.endswith('.html') or fn == 'hoja-de-vida.html':
                continue
            f = os.path.join(dirpath, fn)
            with open(f, encoding='utf-8') as fh:
                s = fh.read()
            if '<div class="nav-links" id="navLinks">' not in s:
                continue
            s2 = re.sub(r'\n    <a href="/articulos/" data-nav="articulos"[^>]*>Artículos</a>', '', s)
            if hay:
                cur = ' aria-current="page"' if '/articulos/' in f.replace(ROOT, '') else ''
                i = s2.index('<div class="nav-links" id="navLinks">')
                j = s2.index('</div>', i)
                # antes de «Contacto»
                k = s2.rfind('\n    <a', i, j)
                s2 = s2[:k] + f'\n    <a href="/articulos/" data-nav="articulos"{cur}>Artículos</a>' + s2[k:]
            if s2 != s:
                with open(f, 'w', encoding='utf-8') as fh:
                    fh.write(s2)


def main():
    src_dir = p('_articulos')
    fuentes = sorted(f for f in os.listdir(src_dir) if f.endswith('.md')) if os.path.isdir(src_dir) else []
    arts = [leer(os.path.join(src_dir, f)) for f in fuentes]
    arts = [a for a in arts if a.get('borrador', '').lower() not in ('si', 'sí', 'true')]
    arts.sort(key=lambda a: a['fecha_d'], reverse=True)
    for a in arts:
        imagen(a)
    nav, tail = shell_parts()
    os.makedirs(p('articulos'), exist_ok=True)
    vivos = {a['slug'] + '.html' for a in arts} | {'index.html'}
    for f in os.listdir(p('articulos')):
        if f not in vivos:
            os.remove(p('articulos', f))
    for a in arts:
        otros = [o for o in arts if o is not a]
        otros.sort(key=lambda o: (o.get('servicio') != a.get('servicio'),))
        with open(p('articulos', a['slug'] + '.html'), 'w', encoding='utf-8') as f:
            f.write(pagina_articulo(a, nav, tail, otros))
    with open(p('articulos', 'index.html'), 'w', encoding='utf-8') as f:
        f.write(pagina_listado(arts, nav, tail))
    with open(p('feed.xml'), 'w', encoding='utf-8') as f:
        f.write(feed(arts))

    # sitemap
    sm = ''
    if arts:
        sm = f'\n  <url>\n    <loc>{BASE}/articulos/</loc>\n    <lastmod>{arts[0]["actualizado_d"].isoformat()}</lastmod>\n    <priority>0.8</priority>\n  </url>'
        for a in arts:
            img = f'\n    <image:image>\n      <image:loc>{BASE}{a["img"]}</image:loc>\n    </image:image>' if a['img'] else ''
            sm += f'\n  <url>\n    <loc>{a["url"]}</loc>\n    <lastmod>{a["actualizado_d"].isoformat()}</lastmod>{img}\n    <priority>0.7</priority>\n  </url>'
        sm += '\n  '
    reemplazar_entre(p('sitemap.xml'), '<!-- articulos:inicio -->', '<!-- articulos:fin -->', sm or '\n  ')

    # llms.txt
    ll = ''
    if arts:
        ll = '\n## Artículos\n\n' + ''.join(f'- [{a["titulo_seo"]}]({a["url"]}): {a["descripcion"]}\n' for a in arts[:15]) + '\n'
    reemplazar_entre(p('llms.txt'), '<!-- articulos:inicio -->', '<!-- articulos:fin -->', ll or '\n')

    # portada
    home = ''
    if arts:
        home = ('\n<section id="articulos" class="section">\n  <div class="section-head">\n    <h2>Artículos <span class="it">recientes.</span></h2>\n'
                '    <div class="section-side"><p>Ideas y métodos del aula y del taller.</p><a href="/articulos/" class="link-strong">Ver todos los artículos</a></div>\n  </div>\n'
                '  <div class="ar-grid">' + ''.join(tarjeta(a) for a in arts[:3]) + '</div>\n</section>\n')
    reemplazar_entre(p('index.html'), '<!-- articulos:inicio -->', '<!-- articulos:fin -->', home or '\n')

    menu(bool(arts))
    print(f'{len(arts)} artículo(s) publicados' + (': ' + ', '.join(a['slug'] for a in arts) if arts else ''))


if __name__ == '__main__':
    main()
