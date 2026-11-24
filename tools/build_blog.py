#!/usr/bin/env python3
"""Gera o blog estático da Prime Precision.

Uso (na raiz do projeto, onde está o index.html):
    python3 tools/build_blog.py

Lê os posts de content/blog/*.md e escreve blog/index.html, blog/<slug>.html,
feed.xml e sitemap.xml. O cabeçalho, o rodapé e o estilo vêm do index.html.

Formato de um post (content/blog/AAAA-MM-DD-slug.md):
    ---
    title: Título do post
    description: Resumo de 1 a 2 frases (aparece no Google)
    date: AAAA-MM-DD
    ---
    Parágrafos separados por linha em branco.
    ## Subtítulo      ### Subtítulo menor      - item de lista      1. item numerado
    **negrito**   [texto](/#orcamento)
O slug é o nome do arquivo sem a data.
"""
import re, sys, glob, os, html, json, datetime

SITE = 'https://primeprecision.com.br'
MESES = ['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro']
CSS = '''<style>
.lang{display:none}
.blog-wrap{max-width:760px;margin:0 auto;padding:48px 0 72px}
.blog-wrap h1{font-size:clamp(2rem,4.6vw,3.2rem);margin:10px 0 14px}
.post-meta{color:var(--muted);font-size:.95rem}
.post-body{margin-top:28px;font-size:1.08rem;line-height:1.75}
.post-body h2{font-size:1.7rem;margin:38px 0 10px}
.post-body h3{font-size:1.3rem;margin:28px 0 8px}
.post-body p{margin:0 0 16px}
.post-body ul,.post-body ol{margin:0 0 18px;padding-left:1.3em}
.post-body li{margin:6px 0}
.post-body a{color:var(--red-ink);text-decoration:underline;text-underline-offset:3px}
.post-cta{margin-top:40px;padding:24px;border:1px solid var(--line);border-radius:12px;background:var(--surface);display:flex;flex-wrap:wrap;align-items:center;gap:14px 24px}
.post-cta p{margin:0;font-weight:600;flex:1 1 260px}
.more{margin-top:48px;border-top:1px solid var(--line)}
.more h2{font-size:1.4rem;margin:24px 0 4px}
.plist{border-top:1px solid var(--line);margin-top:28px}
.pitem{display:block;padding:26px 0;border-bottom:1px solid var(--line);text-decoration:none;color:inherit}
.pitem h2,.pitem h3{font-size:1.6rem;margin:4px 0 6px}
.pitem p{margin:0;color:var(--muted)}
.pitem:hover h2,.pitem:hover h3{color:var(--red-ink)}
.crumb{font-size:.95rem}.crumb a{color:var(--muted)}
</style>
'''

def esc(s): return html.escape(s, quote=True)

def inline(s):
    s = esc(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: '<a href="%s">%s</a>' % (m.group(2), m.group(1)), s)
    return s

def md(body):
    out, blocks = [], re.split(r'\n\s*\n', body.strip())
    for b in blocks:
        lines = b.strip().split('\n')
        if b.startswith('## '): out.append('<h2>%s</h2>' % inline(b[3:].strip()))
        elif b.startswith('### '): out.append('<h3>%s</h3>' % inline(b[4:].strip()))
        elif all(l.startswith('- ') for l in lines): out.append('<ul>%s</ul>' % ''.join('<li>%s</li>' % inline(l[2:]) for l in lines))
        elif all(re.match(r'\d+\. ', l) for l in lines): out.append('<ol>%s</ol>' % ''.join('<li>%s</li>' % inline(re.sub(r'^\d+\. ', '', l)) for l in lines))
        else: out.append('<p>%s</p>' % inline(' '.join(lines)))
    return '\n'.join(out)

def load_posts(root):
    posts = []
    for f in sorted(glob.glob(os.path.join(root, 'content', 'blog', '*.md'))):
        t = open(f, encoding='utf8').read()
        m = re.match(r'---\n(.*?)\n---\n(.*)', t, re.S)
        if not m: raise SystemExit('Post sem cabeçalho: ' + f)
        meta = dict(re.match(r'(\w+):\s*(.*)', l).groups() for l in m.group(1).split('\n') if l.strip())
        for k in ('title', 'description', 'date'):
            if k not in meta: raise SystemExit('Falta "%s" em %s' % (k, f))
        slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', os.path.basename(f)[:-3])
        d = datetime.date.fromisoformat(meta['date'])
        words = len(re.findall(r'\w+', m.group(2)))
        posts.append(dict(slug=slug, title=meta['title'], desc=meta['description'], date=d, body=m.group(2),
                          words=words, mins=max(1, round(words / 200))))
    posts = [p for p in posts if p['date'] <= datetime.date.today()]  # posts com data futura ficam agendados
    return sorted(posts, key=lambda p: p['date'], reverse=True)

def fdate(d): return '%d de %s de %d' % (d.day, MESES[d.month - 1], d.year)

def build(home, posts, mode, root):
    """home = html da página inicial (já pronto). mode: 'site' ou 'art'. Escreve em root/blog."""
    if mode == 'site': HOME, SUB, BLOG, POST = '/', '/quem-somos', '/blog', lambda s: '/blog/' + s
    else: HOME, SUB, BLOG, POST = '../index.html', '../quem-somos.html', 'index.html', lambda s: s + '.html'
    pre = home[:home.index('<main id="topo">')]
    mid = home[home.index('</main>'):home.index('<script>', home.index('</main>'))]
    def chrome(cur_blog):
        p = pre
        p = p.replace('href="#topo"', 'href="%s"' % HOME)
        for x in ('endoscopio', 'servicos', 'faq', 'orcamento'):
            p = p.replace('href="#%s"' % x, 'href="%s#%s"' % (HOME, x))
        p = re.sub(r'href="(#quem-somos|/quem-somos|quem-somos\.html|\.\./quem-somos\.html)"', 'href="%s"' % SUB, p)
        p = re.sub(r'href="(#blog|/blog|blog/index\.html|\.\./blog/index\.html|index\.html)"(?=[^>]*>Blog<)',
                   'href="%s"%s' % (BLOG, ' aria-current="page"' if cur_blog else ''), p)
        if mode == 'site':
            p = p.replace('src="assets/', 'src="/assets/').replace('href="favicon.svg"', 'href="/favicon.svg"')
        return p
    def head(p, title, desc, url, typ='website', extra=''):
        p = re.sub(r'<title>.*?</title>', lambda m: '<title>%s</title>' % esc(title), p, count=1, flags=re.S)
        if mode == 'site':
            p = re.sub(r'<meta name="description" content="[^"]*">', lambda m: '<meta name="description" content="%s">' % esc(desc), p, count=1)
            p = re.sub(r'<link rel="canonical" href="[^"]*">', lambda m: '<link rel="canonical" href="%s">' % url, p, count=1)
            p = re.sub(r'<meta property="og:url" content="[^"]*">', lambda m: '<meta property="og:url" content="%s">' % url, p, count=1)
            p = re.sub(r'<meta property="og:title" content="[^"]*">', lambda m: '<meta property="og:title" content="%s">' % esc(title), p, count=1)
            p = re.sub(r'<meta property="og:description" content="[^"]*">', lambda m: '<meta property="og:description" content="%s">' % esc(desc), p, count=1)
            p = p.replace('<meta property="og:type" content="website">', '<meta property="og:type" content="%s">' % typ)
        if '</head>' in p: return p.replace('</head>', CSS + extra + '</head>', 1)
        return p.replace('</style>', '</style>\n' + CSS + extra, 1)
    script = '''<script>
(function(){
  var root=document.documentElement;
  function toggleTheme(){var dark=root.dataset.theme?root.dataset.theme==="dark":window.matchMedia("(prefers-color-scheme: dark)").matches;root.dataset.theme=dark?"light":"dark"}
  Array.prototype.forEach.call(document.querySelectorAll(".theme,.tbtn"),function(b){b.addEventListener("click",toggleTheme)});
  var burger=document.getElementById("burger"),menu=document.getElementById("menu");
  function setMenu(o){menu.hidden=!o;burger.setAttribute("aria-expanded",o?"true":"false")}
  burger.addEventListener("click",function(){setMenu(menu.hidden)});
  Array.prototype.forEach.call(menu.querySelectorAll("a"),function(a){a.addEventListener("click",function(){setMenu(false)})});
  document.addEventListener("keydown",function(e){if(e.key==="Escape"&&!menu.hidden){setMenu(false);burger.focus()}});
  var wide=window.matchMedia("(min-width:861px)");
  function onWide(){if(wide.matches)setMenu(false)}
  if(wide.addEventListener)wide.addEventListener("change",onWide);else if(wide.addListener)wide.addListener(onWide);
})();
</script>
</body>
</html>
'''
    cta = ('<div class="post-cta"><p>Quer conversar sobre a manutenção do seu endoscópio?</p>'
           '<a class="btn" href="%s#orcamento">Pedir orçamento</a></div>') % HOME
    os.makedirs(os.path.join(root, 'blog'), exist_ok=True)
    # índice
    if posts:
        items = ''.join('<a class="pitem" href="%s"><div class="post-meta">%s · %d min de leitura</div><h2>%s</h2><p>%s</p></a>\n' %
                        (POST(p['slug']) if mode != 'art' else p['slug'] + '.html', fdate(p['date']), p['mins'], esc(p['title']), esc(p['desc'])) for p in posts)
    else:
        items = '<p>Em breve, novos artigos.</p>'
    idx = (head(chrome(True), 'Blog | Manutenção de endoscópios | Prime Precision',
                'Artigos sobre manutenção preventiva de endoscópios e instrumentos de precisão: cuidados, sinais de desgaste e boas práticas, pela Prime Precision.',
                SITE + '/blog') +
           '<main id="topo"><div class="band"><div class="inner"><div class="blog-wrap">'
           '<div class="kicker">Blog</div><h1>Manutenção de endoscópios e instrumentos de precisão</h1>'
           '<p class="sec-lead">Cuidados, sinais de desgaste e boas práticas, escritos pela equipe da Prime Precision.</p>'
           '<div class="plist">' + items + '</div>' + cta.replace('post-cta', 'post-cta" style="margin-top:40px') + '</div></div></div>\n' + mid + script)
    open(os.path.join(root, 'blog', 'index.html'), 'w', encoding='utf8').write(idx)
    # posts
    for i, p in enumerate(posts):
        url = '%s/blog/%s' % (SITE, p['slug'])
        ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p['title'], "description": p['desc'],
              "datePublished": p['date'].isoformat(), "dateModified": p['date'].isoformat(), "inLanguage": "pt-BR",
              "mainEntityOfPage": url, "image": SITE + "/assets/hero.jpg",
              "author": {"@type": "Organization", "name": "Prime Precision", "url": SITE + "/"},
              "publisher": {"@type": "Organization", "name": "Prime Precision", "url": SITE + "/", "logo": {"@type": "ImageObject", "url": SITE + "/assets/logo-light.png"}}}
        extra = '<script type="application/ld+json">%s</script>\n' % json.dumps(ld, ensure_ascii=False)
        others = [q for q in posts if q is not p][:3]
        more = ''
        if others:
            more = '<div class="more"><h2>Leia também</h2><div class="plist" style="margin-top:12px">' + ''.join(
                '<a class="pitem" href="%s"><h3>%s</h3><p>%s</p></a>' % (q['slug'] + '.html' if mode == 'art' else POST(q['slug']), esc(q['title']), esc(q['desc'])) for q in others) + '</div></div>'
        body = md(p['body'])
        body = body.replace('href="/#', 'href="%s#' % HOME)
        page = (head(chrome(True), p['title'] + ' | Prime Precision', p['desc'], url, 'article', extra) +
                '<main id="topo"><div class="band"><div class="inner"><article class="blog-wrap">'
                '<div class="crumb"><a href="%s">Blog</a></div><h1>%s</h1>'
                '<div class="post-meta">%s · %d min de leitura · Prime Precision</div>'
                '<div class="post-body">%s</div>%s%s</article></div></div>\n' % (BLOG, esc(p['title']), fdate(p['date']), p['mins'], body, cta, more) + mid + script)
        open(os.path.join(root, 'blog', p['slug'] + '.html'), 'w', encoding='utf8').write(page)

def write_seo(root, posts):
    urls = [(SITE + '/', 'monthly', '1.0', None), (SITE + '/quem-somos', 'yearly', '0.6', None), (SITE + '/blog', 'weekly', '0.7', posts[0]['date'] if posts else None)]
    urls += [(SITE + '/blog/' + p['slug'], 'yearly', '0.6', p['date']) for p in posts]
    x = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u, c, pr, d in urls:
        x += '  <url><loc>%s</loc>%s<changefreq>%s</changefreq><priority>%s</priority></url>\n' % (u, '<lastmod>%s</lastmod>' % d.isoformat() if d else '', c, pr)
    open(os.path.join(root, 'sitemap.xml'), 'w', encoding='utf8').write(x + '</urlset>\n')
    f = '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Prime Precision | Blog</title><link>%s/blog</link><description>Manutenção de endoscópios e instrumentos de precisão</description><language>pt-BR</language>\n' % SITE
    for p in posts:
        f += '<item><title>%s</title><link>%s/blog/%s</link><guid>%s/blog/%s</guid><pubDate>%s 12:00:00 +0000</pubDate><description>%s</description></item>\n' % (
            esc(p['title']), SITE, p['slug'], SITE, p['slug'], p['date'].strftime('%a, %d %b %Y'), esc(p['desc']))
    open(os.path.join(root, 'feed.xml'), 'w', encoding='utf8').write(f + '</channel></rss>\n')

if __name__ == '__main__':
    root = os.getcwd()
    home = open(os.path.join(root, 'index.html'), encoding='utf8').read()
    posts = load_posts(root)
    build(home, posts, 'site', root)
    write_seo(root, posts)
    print('Blog gerado: %d posts' % len(posts))
