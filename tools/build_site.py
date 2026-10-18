"""Builds the static website from src/free-tape-label.html into dist/.

One pre-translated page per language (English at /, the others at /xx/), with hreflang,
sitemap.xml, robots.txt and Cloudflare Pages _headers. Requires Python 3.8+ only.

Usage:  python3 tools/build_site.py [--base https://your-domain.example/]
"""
import re, json, html, os, datetime, shutil, sys
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(REPO, 'src', 'free-tape-label.html')
PUBLIC = os.path.join(REPO, 'public')
OUT = os.path.join(REPO, 'dist')
BASE = 'https://www.freetapelabels.com/'
if '--base' in sys.argv:
    BASE = sys.argv[sys.argv.index('--base') + 1].rstrip('/') + '/'
LANGS = ['de', 'en', 'fr', 'es', 'it', 'pt', 'nl', 'pl']
HREFLANG = {'pt': 'pt-BR'}
LOCALE = {'de': 'de_DE', 'en': 'en_US', 'fr': 'fr_FR', 'es': 'es_ES', 'it': 'it_IT', 'pt': 'pt_BR', 'nl': 'nl_NL', 'pl': 'pl_PL'}
META = {
 'de': ('Free Tape Labels – kostenloser LTO Label Generator für Barcode-Etiketten',
        'Kostenloser LTO Label Generator: LTO-Barcode-Etiketten für LTO-1 bis LTO-10, WORM, Reinigungskassetten und IBM 3592 erstellen. Ohne Installation, ohne Konto, ohne Abo – dauerhaft kostenlos. Vorlagen für Avery 6577, Herma 4459 und Etikettendrucker.'),
 'en': ('Free Tape Labels – free LTO label generator for barcode labels',
        'Free LTO label generator: create LTO barcode labels for LTO-1 to LTO-10, WORM, cleaning cartridges and IBM 3592. No installation, no account, no subscription – free for good. Templates for Avery 6577, Herma 4459 and label printers.'),
 'fr': ('Free Tape Labels – générateur d’étiquettes LTO gratuit pour codes-barres',
        'Générateur d’étiquettes LTO gratuit : créez des étiquettes code-barres LTO pour LTO-1 à LTO-10, WORM, cartouches de nettoyage et IBM 3592. Sans installation, sans compte, sans abonnement – gratuit pour toujours. Modèles pour Avery 6577, Herma 4459 et imprimantes d’étiquettes.'),
 'es': ('Free Tape Labels – generador de etiquetas LTO gratuito con código de barras',
        'Generador de etiquetas LTO gratuito: crea etiquetas de código de barras LTO para LTO-1 a LTO-10, WORM, cartuchos de limpieza e IBM 3592. Sin instalación, sin cuenta, sin suscripción: gratis para siempre. Plantillas para Avery 6577, Herma 4459 e impresoras de etiquetas.'),
 'it': ('Free Tape Labels – generatore di etichette LTO gratuito con barcode',
        'Generatore di etichette LTO gratuito: crea etichette barcode LTO per LTO-1 fino a LTO-10, WORM, cartucce di pulizia e IBM 3592. Senza installazione, senza account, senza abbonamento – gratis per sempre. Modelli per Avery 6577, Herma 4459 e stampanti per etichette.'),
 'pt': ('Free Tape Labels – gerador de etiquetas LTO grátis com código de barras',
        'Gerador de etiquetas LTO grátis: crie etiquetas de código de barras LTO para LTO-1 a LTO-10, WORM, cartuchos de limpeza e IBM 3592. Sem instalação, sem conta, sem assinatura – grátis para sempre. Modelos para Avery 6577, Herma 4459 e impressoras de etiquetas.'),
 'nl': ('Free Tape Labels – gratis LTO-labelgenerator voor barcodelabels',
        'Gratis LTO-labelgenerator: maak LTO-barcodelabels voor LTO-1 tot LTO-10, WORM, reinigingscassettes en IBM 3592. Zonder installatie, zonder account, zonder abonnement – voor altijd gratis. Sjablonen voor Avery 6577, Herma 4459 en labelprinters.'),
 'pl': ('Free Tape Labels – darmowy generator etykiet LTO z kodem kreskowym',
        'Darmowy generator etykiet LTO: twórz etykiety z kodem kreskowym LTO dla LTO-1 do LTO-10, WORM, kaset czyszczących i IBM 3592. Bez instalacji, bez konta, bez abonamentu – darmowo na zawsze. Szablony dla Avery 6577, Herma 4459 i drukarek etykiet.'),
}
ROOT = 'en'
path = lambda L: '' if L == ROOT else L + '/'

src = open(SRC).read()

def dict_of(L):
    """Dictionary of one language from the app source (key = English text)."""
    if L == 'en': return {}
    a = 'const %s = ' % L.upper(); i = src.index(a) + len(a); j = src.index(';\n', i)
    return json.loads(src[i:j])

EN = dict_of('de')  # key list: every key is an English source text
DICTS = {L: dict_of(L) for L in LANGS}

RAW = ('script', 'style', 'textarea')
SKIP = ('svg',)
VOID = {'area','base','br','col','embed','hr','img','input','link','meta','source','track','wbr'}

def translate_markup(m, D):
    """Like applyStatic in the browser: text nodes and aria-label/placeholder whose trimmed text is a key."""
    out = []; pos = 0; stack = []  # (tag, skip)
    def skipping(): return any(sk for _, sk in stack)
    def tr_attr(tag):
        def f(mo):
            k = html.unescape(mo.group(2))
            if k in EN and k in D: return mo.group(1) + '="' + html.escape(D[k], quote=True) + '"'
            return mo.group(0)
        return re.sub(r'\b(aria-label|placeholder)="([^"]*)"', f, tag)
    while pos < len(m):
        lt = m.find('<', pos)
        if lt < 0: lt = len(m)
        text = m[pos:lt]
        if text:
            k = html.unescape(text.strip())
            if k and not skipping() and k in EN and k in D:
                lead = text[:len(text) - len(text.lstrip())]; trail = text[len(text.rstrip()):]
                if re.match(r'[,.;:]', D[k]): lead = ''
                text = lead + html.escape(D[k], quote=False) + trail
            out.append(text)
        if lt >= len(m): break
        gt = m.index('>', lt); tag = m[lt:gt+1]
        mo = re.match(r'<\s*(/?)\s*([a-zA-Z0-9-]+)', tag)
        if not mo:  # comment, doctype
            if tag.startswith('<!--'):
                end = m.index('-->', lt) + 3; out.append(m[lt:end]); pos = end; continue
            out.append(tag); pos = gt + 1; continue
        closing, name = mo.group(1) == '/', mo.group(2).lower()
        if closing:
            while stack:
                n, _ = stack.pop()
                if n == name: break
            out.append(tag); pos = gt + 1; continue
        if name in RAW:
            end = m.index('</' + name, gt); close = m.index('>', end) + 1
            out.append(tr_attr(tag) + m[gt+1:close]); pos = close; continue
        sk = skipping() or name in SKIP or 'data-dyn' in tag
        out.append(tag if skipping() else tr_attr(tag))
        if name not in VOID and not tag.endswith('/>'): stack.append((name, sk))
        pos = gt + 1
    return ''.join(out)

def build(L):
    pre = '' if L == ROOT else '../'
    D = DICTS[L]
    b = src.replace('<title>Free Tape Labels</title>\n', '', 1)
    b = re.sub(r'<link rel="preconnect"[^>]*>\n', '', b); b = re.sub(r'<link href="https://fonts\.googleapis\.com[^>]*>\n', '', b)
    b = b.replace('https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js', pre + 'assets/jspdf.umd.min.js')
    # ship DE (key list) and the page's own language only
    for X in ['FR', 'ES', 'IT', 'PT', 'NL', 'PL']:
        if X.lower() == L: continue
        a = 'const %s = ' % X; i = b.index(a) + len(a); j = b.index(';\n', i); b = b[:i] + '{}' + b[j:]
    # structured data in the page language
    i = b.index('<script type="application/ld+json">'); j = b.index('</script>', i)
    ld = json.loads(b[i+len('<script type="application/ld+json">'):j])
    ld['description'] = META[L][1]; ld['inLanguage'] = HREFLANG.get(L, L); ld['url'] = BASE + path(L)
    b = b[:i] + '<script type="application/ld+json">\n' + json.dumps(ld, ensure_ascii=False) + '\n' + b[j:]
    if L != 'en': b = translate_markup(b, D)
    # write the version into the footer statically (for search engines and without JavaScript)
    vt = {'de':'Version','en':'Version','fr':'Version','es':'Versión','it':'Versione','pt':'Versão','nl':'Versie','pl':'Wersja'}[L]
    vd = {'en':'2026-10-16','de':'16.10.2026','pl':'16.10.2026','nl':'16-10-2026'}.get(L,'16/10/2026')
    b = b.replace('<span id="appVer" data-dyn></span>', '<span id="appVer" data-dyn>%s 1.0 · %s</span>' % (vt, vd))
    title, desc = META[L]
    alts = ''.join('<link rel="alternate" hreflang="%s" href="%s%s">\n' % (HREFLANG.get(x, x), BASE, path(x)) for x in LANGS)
    alts += '<link rel="alternate" hreflang="x-default" href="%s">\n' % BASE
    site = {'lang': L, 'root': L == ROOT, 'urls': {x: (pre + path(x)) or './' for x in LANGS}}
    head = f'''<!doctype html>
<html lang="{HREFLANG.get(L, L)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{html.escape(title, quote=False)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{BASE}{path(L)}">
{alts}<meta property="og:type" content="website">
<meta property="og:locale" content="{LOCALE[L]}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{BASE}{path(L)}">
<meta property="og:image" content="{BASE}assets/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Free Tape Labels – LTO barcode label generator">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{pre}favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{pre}assets/fonts.css">
<script>window.FTL_SITE={json.dumps(site, separators=(',', ':'))};(function(){{var S=window.FTL_SITE,s=null;try{{s=localStorage.getItem("ftl.lang")}}catch(e){{}}if(s&&s!==S.lang&&S.urls[s]){{location.replace(S.urls[s]+location.hash);return}}if(!s&&S.root&&!/bot|crawl|spider|slurp/i.test(navigator.userAgent||"")){{var b=(navigator.language||"").slice(0,2).toLowerCase();if(b!==S.lang&&S.urls[b])location.replace(S.urls[b]+location.hash)}}}})();try{{var t=localStorage.getItem("ftl.theme");if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}</script>
<style>body{{margin:0}}[hidden]{{display:none!important}}</style>
</head>
<body>
'''
    d = os.path.join(OUT, path(L)); os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w').write(head + b + '\n</body>\n</html>\n')
    return os.path.getsize(os.path.join(d, 'index.html'))

if __name__ == '__main__':
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    shutil.copytree(PUBLIC, OUT)
    for L in LANGS: print(L, build(L))
    os.makedirs(os.path.join(OUT, 'en'), exist_ok=True)
    open(os.path.join(OUT, 'en', 'index.html'), 'w').write('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>Free Tape Labels</title><link rel="canonical" href="%s"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url=../"><script>location.replace("../"+location.hash)</script></head><body><a href="../">Free Tape Labels</a></body></html>\n' % BASE)
    today = datetime.date.today().isoformat()
    urls = ''.join('  <url>\n    <loc>%s%s</loc>\n    <lastmod>%s</lastmod>\n%s  </url>\n' % (BASE, path(L), today,
        ''.join('    <xhtml:link rel="alternate" hreflang="%s" href="%s%s"/>\n' % (HREFLANG.get(x, x), BASE, path(x)) for x in LANGS)) for L in LANGS)
    # Cloudflare Pages: long browser caching for immutable files, no indexing of pages.dev
    open(os.path.join(OUT, '_headers'), 'w').write(
        "/assets/fonts/*\n  Cache-Control: public, max-age=31536000, immutable\n\n"
        "/assets/jspdf.umd.min.js\n  Cache-Control: public, max-age=31536000, immutable\n\n"
        "/assets/fonts.css\n  Cache-Control: public, max-age=604800\n\n"
        "/favicon.svg\n  Cache-Control: public, max-age=604800\n\n"
        "/assets/og-image.jpg\n  Cache-Control: public, max-age=604800\n\n"
        "https://:project.pages.dev/*\n  X-Robots-Tag: noindex\n\n"
        "https://:version.:project.pages.dev/*\n  X-Robots-Tag: noindex\n")
    open(os.path.join(OUT, 'robots.txt'), 'w').write('User-agent: *\nAllow: /\n\nSitemap: %ssitemap.xml\n' % BASE)
    open(os.path.join(OUT, 'sitemap.xml'), 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + urls + '</urlset>\n')
    for f in ('site.pdf', 'site.png'):
        try: os.remove(os.path.join(OUT, f))
        except FileNotFoundError: pass
