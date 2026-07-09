#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
مولّد مدونة ماجد — موقع ثابت بدون أي اعتماديات خارجية.

  python3 build.py        → يولّد الموقع كاملاً في مجلد docs/

المحتوى في content/posts/*.md (ترويسة بين --- ثم نص المقالة HTML)
وإعدادات الموقع في content/site.json.
"""
import json, re, shutil
from pathlib import Path
from string import Template

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
OUT = ROOT / "docs"


# ————— قراءة المحتوى —————

def parse_post(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"ترويسة مفقودة في {path.name}")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    meta["slug"] = path.stem
    meta["body"] = m.group(2).strip()
    meta["featured"] = meta.get("featured", "no") == "yes"
    rt = meta.get("reading_time", "")
    if rt:
        meta["reading_time"] = str(int(float(rt)))
    return meta


def load():
    site = json.loads((CONTENT / "site.json").read_text(encoding="utf-8"))
    posts = [parse_post(p) for p in sorted((CONTENT / "posts").glob("*.md"))]
    posts.sort(key=lambda p: p["date"], reverse=True)
    return site, posts


def fmt_date(iso: str) -> str:          # 2026-07-09T15:55:03 → 2026/07/09
    return iso[:10].replace("-", "/")


def fmt_short(iso: str) -> str:         # 2026-07-09T15:55:03 → 07/09
    y, m, d = iso[:10].split("-")
    return f"{m}/{d}"


# ————— الأجزاء المشتركة —————

ICON_MENU = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="4" y1="7" x2="20" y2="7"/><line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="17" x2="20" y2="17"/></svg>'
ICON_X = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="6" y1="6" x2="18" y2="18"/><line x1="18" y1="6" x2="6" y2="18"/></svg>'

PAGE = Template("""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>$title</title>
<meta name="description" content="$description">
<meta property="og:title" content="$title">
<meta property="og:description" content="$description">
<meta property="og:type" content="$og_type">
$og_image
<link rel="icon" href="${rel}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="${rel}assets/css/style.css">
</head>
<body>
<nav class="navbar" id="navbar">
  <div class="container nav-inner">
    <button class="menu-btn" id="menuOpen" aria-label="فتح القائمة">$icon_menu</button>
    <a href="${rel}index.html" class="nav-brand">$brand</a>
  </div>
</nav>

<div class="menu-overlay" id="menuOverlay">
  <div class="menu-head">
    <button class="menu-close" id="menuClose" aria-label="إغلاق القائمة">$icon_x</button>
    <span class="brand">$brand</span>
  </div>
  <div class="menu-links">
$menu_links
  </div>
  <div class="menu-foot"><p>$tagline</p></div>
</div>

$main

<footer class="footer">
  <div class="container inner">
    <div class="footer-grid">
      <div>
        <h3>$brand</h3>
        <p class="desc">$description</p>
      </div>
      <div>
        <h4>تصفّح</h4>
        <nav>
$footer_links
        </nav>
      </div>
    </div>
    <hr class="mistarah">
    <div class="footer-bottom">
      <p>جميع الحقوق محفوظة © $year</p>
      <p>$footer_note</p>
    </div>
  </div>
</footer>

<script>
(function () {
  var nav = document.getElementById('navbar');
  var onScroll = function () { nav.classList.toggle('scrolled', window.scrollY > 20); };
  window.addEventListener('scroll', onScroll); onScroll();

  var overlay = document.getElementById('menuOverlay');
  document.getElementById('menuOpen').addEventListener('click', function () {
    overlay.classList.add('open'); document.body.style.overflow = 'hidden';
  });
  document.getElementById('menuClose').addEventListener('click', function () {
    overlay.classList.remove('open'); document.body.style.overflow = '';
  });

  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); } });
    }, { rootMargin: '-50px' });
    document.querySelectorAll('.fade-in').forEach(function (el) { io.observe(el); });
  } else {
    document.querySelectorAll('.fade-in').forEach(function (el) { el.classList.add('visible'); });
  }
})();
</script>
$extra_js
</body>
</html>
""")


def render_page(site, *, rel, title, description, main, og_type="website", og_image="", extra_js=""):
    import datetime
    menu_links = "\n".join(
        f'    <a href="{rel}{item["url"]}">{item["label"]}</a>' for item in site["nav"]
    )
    footer_links = "\n".join(
        f'          <a href="{rel}{item["url"]}">{item["label"]}</a>' for item in site["nav"]
    )
    return PAGE.substitute(
        rel=rel, title=title, description=description,
        og_type=og_type,
        og_image=f'<meta property="og:image" content="{og_image}">' if og_image else "",
        brand=site["brand"], tagline=site["tagline"],
        menu_links=menu_links, footer_links=footer_links,
        footer_note=site["footer_note"],
        year=datetime.date.today().year,
        icon_menu=ICON_MENU, icon_x=ICON_X,
        main=main, extra_js=extra_js,
    )


def card_meta(p, sep='<span>·</span>'):
    parts = [f'<span>{p["category"]}</span>']
    if p.get("subcategory"):
        parts.append(f'<span>{p["subcategory"]}</span>')
    parts.append(f'<span>{fmt_date(p["date"])}</span>')
    if p.get("reading_time"):
        parts.append(f'<span>{p["reading_time"]} دقائق</span>')
    return f"\n          {sep}\n          ".join(parts)


# ————— الصفحة الرئيسية —————

def build_home(site, posts):
    featured = next((p for p in posts if p["featured"]), posts[0])
    rest = [p for p in posts if p is not featured]
    rel = ""

    cards = "\n".join(f"""
      <a href="post/{p['slug']}/index.html" class="post-card fade-in">
        <div class="img-wrap"><img src="{p['image']}" alt="{p['title']}" loading="lazy"></div>
        <div class="meta">
          {card_meta(p)}
        </div>
        <h3>{p['title']}</h3>
        <p class="excerpt">{p['excerpt']}</p>
        <span class="read">اقرأ المقالة ←</span>
      </a>""" for p in rest)

    pull = ""
    if featured.get("pull_quote"):
        pull = f"""
  <section class="pull-quote-section">
    <div class="inner">
      <span class="marker top">■</span>
      <blockquote>{featured['pull_quote']}</blockquote>
      <span class="marker bottom">■</span>
    </div>
  </section>"""

    main = f"""
<main>
  <section class="hero">
    <div class="hero-bg">
      <img src="{featured['image']}" alt="">
      <div class="hero-fade"></div>
    </div>
    <div class="hero-ghost" aria-hidden="true">{featured['title'][:20]}</div>
    <div class="hero-content">
      <div class="container"><div class="inner">
        <div class="meta">
          <span class="chip">{featured['category']}</span>
          <span>{featured.get('subcategory', '')}</span>
          <span>{fmt_date(featured['date'])}</span>
          <span>{featured.get('reading_time', '')} دقائق قراءة</span>
        </div>
        <h1>{featured['title']}</h1>
        <p class="excerpt">{featured['excerpt']}</p>
        <a class="btn-read" href="post/{featured['slug']}/index.html">اقرأ المقالة</a>
      </div></div>
    </div>
    <div class="hero-rule"></div>
  </section>

  <section class="articles">
    <div class="container">
      <div class="section-head">
        <h2>{site['articles_heading']}</h2>
        <div class="rule"></div>
      </div>
      <div class="post-grid">{cards}
      </div>
    </div>
  </section>
{pull}
</main>"""

    return render_page(
        site, rel=rel,
        title=f"{site['brand']} | {site['tagline']}",
        description=site["description"],
        main=main,
    )


# ————— الأرشيف —————

def build_archive(site, posts):
    rel = "../"
    years = {}
    for p in posts:
        years.setdefault(p["date"][:4], []).append(p)

    cat_buttons = '<button class="filter-btn active" data-filter-cat="">الكل</button>\n' + "\n".join(
        f'          <button class="filter-btn" data-filter-cat="{c}">{c}</button>' for c in site["categories"]
    )
    sense_buttons = "\n".join(
        f'          <button class="filter-btn sense" data-filter-sub="{s}">{s}</button>' for s in site["senses"]
    )

    groups = []
    for year, yposts in sorted(years.items(), reverse=True):
        rows = "\n".join(f"""
        <a href="{rel}post/{p['slug']}/index.html" class="archive-row"
           data-cat="{p['category']}" data-sub="{p.get('subcategory','')}" data-img="{rel}{p['image']}">
          <span class="date">{fmt_short(p['date'])}</span>
          <span class="cat">{p['category']}{' · ' + p['subcategory'] if p.get('subcategory') else ''}</span>
          <h3>{p['title']}</h3>
          {f'<span class="rt">{p["reading_time"]} د</span>' if p.get('reading_time') else ''}
        </a>""" for p in yposts)
        groups.append(f"""
      <div class="year-group" data-year="{year}">
        <div class="year-head">
          <span class="year">{year}</span>
          <div class="rule-wrap"><hr class="mistarah"></div>
        </div>
        <div class="rows">{rows}
        </div>
      </div>""")

    main = f"""
<main class="page archive">
  <div class="container">
    <h1>الأرشيف</h1>
    <p class="sub">كل ما كُتب، مرتّباً بحسب الزمن.</p>

    <div class="filter-row">
          {cat_buttons}
    </div>
    <div class="filter-row senses">
      <span class="senses-label">الحواس:</span>
{sense_buttons}
    </div>

    <div class="ghost-img" id="ghostImg"><img src="" alt=""></div>
    <div id="archiveList">{''.join(groups)}
    </div>
    <p class="archive-empty" id="archiveEmpty" hidden>لا توجد مقالات بعد.</p>
  </div>
</main>"""

    extra_js = """<script>
(function () {
  var cat = '', sub = '';
  function apply() {
    var any = false;
    document.querySelectorAll('.archive-row').forEach(function (row) {
      var show = (!cat || row.dataset.cat === cat) && (!sub || row.dataset.sub === sub);
      row.style.display = show ? '' : 'none';
      if (show) any = true;
    });
    document.querySelectorAll('.year-group').forEach(function (g) {
      var visible = [].some.call(g.querySelectorAll('.archive-row'), function (r) { return r.style.display !== 'none'; });
      g.style.display = visible ? '' : 'none';
    });
    document.getElementById('archiveEmpty').hidden = any;
  }
  document.querySelectorAll('[data-filter-cat]').forEach(function (b) {
    b.addEventListener('click', function () {
      cat = b.dataset.filterCat;
      document.querySelectorAll('[data-filter-cat]').forEach(function (x) { x.classList.toggle('active', x === b); });
      apply();
    });
  });
  document.querySelectorAll('[data-filter-sub]').forEach(function (b) {
    b.addEventListener('click', function () {
      sub = (sub === b.dataset.filterSub) ? '' : b.dataset.filterSub;
      document.querySelectorAll('[data-filter-sub]').forEach(function (x) { x.classList.toggle('active', x.dataset.filterSub === sub); });
      apply();
    });
  });
  var ghost = document.getElementById('ghostImg'), ghostImg = ghost.querySelector('img');
  document.querySelectorAll('.archive-row').forEach(function (row) {
    row.addEventListener('mouseenter', function () {
      if (row.dataset.img) { ghostImg.src = row.dataset.img; ghost.classList.add('visible'); }
    });
    row.addEventListener('mouseleave', function () { ghost.classList.remove('visible'); });
  });
})();
</script>"""

    return render_page(
        site, rel=rel,
        title=f"الأرشيف | {site['brand']}",
        description="كل ما كُتب، مرتّباً بحسب الزمن.",
        main=main, extra_js=extra_js,
    )


# ————— عني —————

def build_about(site):
    rel = "../"
    a = site["about"]
    paragraphs = "\n".join(f"        <p>{p}</p>" for p in a["paragraphs"])
    stats = "\n".join(f"""
        <div>
          <span class="value">{s['value']}</span>
          <span class="label">{s['label']}</span>
        </div>""" for s in a["stats"])

    main = f"""
<main class="page">
  <div class="container">
    <div class="about-grid">
      <div class="about-image">
        <img src="{rel}{a['image']}" alt="صورة الكاتب">
        <div class="fade"></div>
      </div>
      <div class="about-content">
        <span class="label">{a['label']}</span>
        <h1>{a['title']}</h1>
        <hr class="mistarah">
        <div class="about-text">
{paragraphs}
        </div>
        <hr class="mistarah">
        <div class="stats">{stats}
        </div>
        <hr class="mistarah">
        <blockquote class="about-quote">{a['quote']}</blockquote>
      </div>
    </div>
  </div>
</main>"""

    return render_page(
        site, rel=rel,
        title=f"عني | {site['brand']}",
        description=a["paragraphs"][0][:150],
        main=main,
    )


# ————— صفحة المقالة —————

def build_post(site, p):
    rel = "../../"
    pull = ""
    if p.get("pull_quote"):
        pull = f"""
  <div class="post-pull"><blockquote>{p['pull_quote']}</blockquote></div>"""

    main = f"""
<div class="progress-track" aria-hidden="true"><div class="bar" id="progressBar"></div></div>
<main>
  <header class="post-header">
    <div class="inner">
      <a href="{rel}index.html" class="back-link">← العودة</a>
      <div class="meta">
        <span class="chip">{p['category']}</span>
        {f'<span>{p["subcategory"]}</span>' if p.get('subcategory') else ''}
        <span>{fmt_date(p['date'])}</span>
        {f'<span>{p["reading_time"]} دقائق قراءة</span>' if p.get('reading_time') else ''}
      </div>
      <h1>{p['title']}</h1>
      <hr class="mistarah">
    </div>
  </header>

  <figure class="post-figure">
    <img src="{rel}{p['image']}" alt="{p['title']}">
  </figure>
{pull}
  <article class="post-body">
    <div class="prose-arabic">
{p['body']}
    </div>
  </article>

  <div class="end-marker">■</div>
  <hr class="mistarah post-rule">
</main>"""

    extra_js = """<script>
(function () {
  var bar = document.getElementById('progressBar');
  function update() {
    var h = document.documentElement.scrollHeight - window.innerHeight;
    bar.style.height = (h > 0 ? (window.scrollY / h) * 100 : 0) + '%';
  }
  window.addEventListener('scroll', update); update();
})();
</script>"""

    return render_page(
        site, rel=rel,
        title=f"{p['title']} | {site['brand']}",
        description=p["excerpt"],
        og_type="article",
        main=main, extra_js=extra_js,
    )


# ————— RSS —————

def build_feed(site, posts):
    url = site.get("site_url", "").rstrip("/")
    if not url:
        return None
    items = "\n".join(f"""  <item>
    <title>{p['title']}</title>
    <link>{url}/post/{p['slug']}/</link>
    <guid>{url}/post/{p['slug']}/</guid>
    <pubDate>{p['date']}</pubDate>
    <description>{p['excerpt']}</description>
  </item>""" for p in posts)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>{site['brand']}</title>
  <link>{url}</link>
  <description>{site['description']}</description>
  <language>ar</language>
{items}
</channel></rss>
"""


# ————— التنفيذ —————

def main():
    site, posts = load()

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets")
    (OUT / ".nojekyll").write_text("")

    (OUT / "index.html").write_text(build_home(site, posts), encoding="utf-8")

    (OUT / "archive").mkdir()
    (OUT / "archive" / "index.html").write_text(build_archive(site, posts), encoding="utf-8")

    (OUT / "about").mkdir()
    (OUT / "about" / "index.html").write_text(build_about(site), encoding="utf-8")

    for p in posts:
        d = OUT / "post" / p["slug"]
        d.mkdir(parents=True)
        (d / "index.html").write_text(build_post(site, p), encoding="utf-8")

    feed = build_feed(site, posts)
    if feed:
        (OUT / "feed.xml").write_text(feed, encoding="utf-8")

    # دومين GitHub Pages الخاص
    url = site.get("site_url", "")
    if url:
        host = url.split("//")[-1].strip("/")
        if not host.endswith("github.io"):
            (OUT / "CNAME").write_text(host + "\n")

    n = 3 + len(posts)
    print(f"تم البناء ✓  {n} صفحات في docs/  ({len(posts)} مقالة)")


if __name__ == "__main__":
    main()
