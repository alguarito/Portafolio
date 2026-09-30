#!/usr/bin/env python3
"""Emite constancias de participación verificables con código QR.

Uso:
  python3 _herramientas/constancias.py _constancias/<curso>.csv

El CSV (UTF-8) lleva estas columnas; «codigo» se llena solo la primera vez:
  nombre,curso,horas,fecha_inicio,fecha_fin,institucion,modalidad,aval,codigo

Produce:
  constancias/<codigo>.json               registro público que lee verificar.html
  _constancias/salida/<curso>/<nombre>.pdf la constancia para entregar (no se publica)

Solo se registra el nombre, el curso y las fechas: nunca el documento de identidad.
Incluya únicamente a quienes aceptaron que su constancia sea verificable en línea.
"""
import csv, html, json, os, re, secrets, subprocess, sys, tempfile
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 'https://alvarocardenasorozco.com'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
ALFABETO = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'  # sin 0/O ni 1/I
MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
         'septiembre', 'octubre', 'noviembre', 'diciembre']
COLS = ['nombre', 'curso', 'horas', 'fecha_inicio', 'fecha_fin', 'institucion', 'modalidad', 'aval', 'codigo']


def fecha_larga(s):
    d = datetime.strptime(s, '%Y-%m-%d').date()
    return f'{d.day} de {MESES[d.month - 1]} de {d.year}'


def nuevo_codigo(usados):
    while True:
        c = 'AC-' + ''.join(secrets.choice(ALFABETO) for _ in range(8))
        if c not in usados and not os.path.exists(os.path.join(ROOT, 'constancias', c + '.json')):
            return c


def slug(t):
    t = t.lower()
    for a, b in zip('áéíóúüñ', 'aeiouun'):
        t = t.replace(a, b)
    return re.sub(r'[^a-z0-9]+', '-', t).strip('-')


PLANTILLA = '''<!DOCTYPE html>
<html lang="es-CO"><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Instrument+Serif:ital@0;1&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/qrcode-generator@1.4.4/qrcode.js"></script>
<style>
@page {{ size: A4 landscape; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; }}
body {{ width: 297mm; height: 210mm; font-family: 'Instrument Sans', sans-serif; color: #111312; background: #f1f0ec; }}
.hoja {{ position: absolute; inset: 12mm; background: #fff; border-radius: 10mm; padding: 16mm 20mm; display: flex; flex-direction: column; }}
.franja {{ position: absolute; left: 0; top: 0; bottom: 0; width: 5mm; background: #c6f432; border-radius: 10mm 0 0 10mm; }}
.mono {{ font-family: 'JetBrains Mono', monospace; font-size: 9.5pt; color: #555b58; letter-spacing: .02em; }}
.tipo {{ align-self: flex-start; display: inline-block; margin-top: 8mm; padding: 1.8mm 4mm; border-radius: 99px; background: #c6f432; font-family: 'JetBrains Mono', monospace; font-size: 10pt; }}
.consta {{ margin-top: 8mm; font-size: 13pt; color: #3d4240; }}
h1 {{ margin-top: 3mm; font-size: 42pt; line-height: 1.02; letter-spacing: -0.03em; font-weight: 600; }}
.texto {{ margin-top: 6mm; font-size: 13pt; line-height: 1.5; color: #3d4240; max-width: 200mm; }}
.texto strong {{ color: #111312; }}
.curso {{ font-family: 'Instrument Serif', serif; font-style: italic; font-size: 17pt; color: #111312; }}
.pie {{ margin-top: auto; display: flex; align-items: flex-end; justify-content: space-between; gap: 10mm; }}
.firma {{ border-top: .4mm solid #111312; padding-top: 2.5mm; width: 90mm; }}
.firma strong {{ display: block; font-size: 12pt; }}
.firma span {{ display: block; font-size: 9.5pt; color: #555b58; line-height: 1.4; }}
.qr {{ display: flex; align-items: flex-end; gap: 4mm; text-align: right; }}
.qr .mono {{ font-size: 8.5pt; line-height: 1.5; }}
.qr .cod {{ font-size: 11pt; color: #111312; font-weight: 500; }}
#qr svg, #qr img {{ width: 30mm; height: 30mm; display: block; }}
.aviso {{ margin-top: 5mm; font-size: 8pt; color: #555b58; }}
</style></head><body>
<div class="hoja"><div class="franja"></div>
  <div class="mono">Dr. Álvaro Cárdenas Orozco · Formación docente · Cartago, Valle del Cauca, Colombia</div>
  <span class="tipo">Constancia de participación</span>
  <p class="consta">Se deja constancia de que</p>
  <h1>{nombre}</h1>
  <p class="texto">participó en <span class="curso">{curso}</span>, con una intensidad de <strong>{horas} horas</strong>, realizado {periodo} en modalidad {modalidad}{institucion}.{aval}</p>
  <div class="pie">
    <div class="firma"><strong>Dr. Álvaro Cárdenas Orozco</strong><span>Doctor en Ciencias de la Educación · Ingeniero de Sistemas y Computación<br>ORCID 0000-0003-1820-301X · alvarocardenasorozco.com</span></div>
    <div class="qr"><div class="mono">Verifique esta constancia en<br>alvarocardenasorozco.com/verificar<br><span class="cod">{codigo}</span><br>Emitida el {emitida}</div><div id="qr"></div></div>
  </div>
  <p class="aviso">Esta constancia acredita la participación en una actividad de formación continua. No constituye título ni crédito académico.</p>
</div>
<script>
var q = qrcode(0, 'M'); q.addData('{url}'); q.make();
document.getElementById('qr').innerHTML = q.createSvgTag({{cellSize: 4, margin: 0, scalable: true}});
</script>
</body></html>'''


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    ruta = sys.argv[1]
    with open(ruta, encoding='utf-8-sig', newline='') as f:
        filas = list(csv.DictReader(f))
    if not filas:
        sys.exit('El CSV está vacío.')
    faltan = [c for c in COLS[:6] if c not in filas[0]]
    if faltan:
        sys.exit('Faltan columnas: ' + ', '.join(faltan))
    usados = {r.get('codigo', '') for r in filas}
    os.makedirs(os.path.join(ROOT, 'constancias'), exist_ok=True)
    hoy = date.today().isoformat()
    emitidas = 0
    for r in filas:
        r = {c: (r.get(c) or '').strip() for c in COLS}
        if not r['nombre']:
            continue
        if not r['codigo']:
            r['codigo'] = nuevo_codigo(usados)
            usados.add(r['codigo'])
        periodo = (f'el {fecha_larga(r["fecha_inicio"])}' if not r['fecha_fin'] or r['fecha_fin'] == r['fecha_inicio']
                   else f'del {fecha_larga(r["fecha_inicio"])} al {fecha_larga(r["fecha_fin"])}')
        reg = {
            'codigo': r['codigo'], 'tipo': 'Constancia de participación',
            'nombre': r['nombre'], 'curso': r['curso'], 'horas': r['horas'],
            'periodo': periodo, 'modalidad': r['modalidad'] or 'presencial',
            'institucion': r['institucion'], 'aval': r['aval'],
            'emitida': fecha_larga(hoy), 'emisor': 'Dr. Álvaro Cárdenas Orozco',
        }
        with open(os.path.join(ROOT, 'constancias', r['codigo'] + '.json'), 'w', encoding='utf-8') as f:
            json.dump(reg, f, ensure_ascii=False, indent=1)
        pagina = PLANTILLA.format(
            nombre=html.escape(r['nombre']), curso=html.escape(r['curso']), horas=html.escape(r['horas']),
            periodo=periodo, modalidad=html.escape(reg['modalidad']),
            institucion=f', dirigido a {html.escape(r["institucion"])}' if r['institucion'] else '',
            aval=f' Con el aval de {html.escape(r["aval"])}.' if r['aval'] else '',
            codigo=r['codigo'], emitida=reg['emitida'],
            url=f'{BASE}/verificar.html?c={r["codigo"]}')
        carpeta = os.path.join(ROOT, '_constancias', 'salida', slug(r['curso']))
        os.makedirs(carpeta, exist_ok=True)
        with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as t:
            t.write(pagina)
        pdf = os.path.join(carpeta, slug(r['nombre']) + '.pdf')
        subprocess.run([CHROME, '--headless', '--disable-gpu', '--no-pdf-header-footer',
                        '--virtual-time-budget=8000', f'--print-to-pdf={pdf}', 'file://' + t.name],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove(t.name)
        emitidas += 1
        print(f'  {r["codigo"]}  {r["nombre"]}')
        # guardar el código en la fila
        for fila in filas:
            if fila['nombre'].strip() == r['nombre'] and not (fila.get('codigo') or '').strip():
                fila['codigo'] = r['codigo']
                break
    with open(ruta, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction='ignore')
        w.writeheader()
        w.writerows(filas)
    print(f'{emitidas} constancia(s). Publique con git add constancias/ y push; los PDF quedan en _constancias/salida/.')


if __name__ == '__main__':
    main()
