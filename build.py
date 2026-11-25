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
    posts = None
    try:
        import sanity_source
        posts = sanity_source.fetch_posts()   # None إذا لم يوجد content/sanity.json
        if posts is not None:
            print(f"المصدر: Sanity ({len(posts)} مقالة)")
    except Exception as e:
        print(f"تعذّر الجلب من Sanity ({e}) — سأستخدم الملفات المحلية")
        posts = None
    if posts is None:
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
ICON_MOON = '<svg class="icon-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>'
ICON_SUN = '<svg class="icon-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><line x1="12" y1="2" x2="12" y2="4"/><line x1="12" y1="20" x2="12" y2="22"/><line x1="4.2" y1="4.2" x2="5.6" y2="5.6"/><line x1="18.4" y1="18.4" x2="19.8" y2="19.8"/><line x1="2" y1="12" x2="4" y2="12"/><line x1="20" y1="12" x2="22" y2="12"/><line x1="4.2" y1="19.8" x2="5.6" y2="18.4"/><line x1="18.4" y1="5.6" x2="19.8" y2="4.2"/></svg>'

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
$head_extra
<link rel="icon" href="${rel}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="${rel}assets/css/style.css">
<script>
(function () {
  var t = localStorage.getItem('theme');
  if (t === 'dark' || (!t && matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.dataset.theme = 'dark';
  } else if (t === 'light') {
    document.documentElement.dataset.theme = 'light';
  }
})();
</script>
$ga
</head>
<body class="$body_class">
<nav class="navbar" id="navbar">
  <div class="container nav-inner">
    <div class="nav-actions">
      <button class="menu-btn" id="menuOpen" aria-label="فتح القائمة">$icon_menu</button>
      <button class="theme-btn" id="themeToggle" aria-label="تبديل الوضع الليلي">$icon_moon$icon_sun</button>
      <a href="${rel}subscribe/" class="nav-subscribe"><span class="full">اشترك في النشرة</span><span class="short">اشترك</span></a>
    </div>
    <div class="nav-search">
      <svg class="s-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><line x1="21" y1="21" x2="16.5" y2="16.5"/></svg>
      <input id="searchInput" type="search" placeholder="$search_placeholder" autocomplete="off" aria-label="بحث">
      <div class="search-results" id="searchResults" hidden></div>
    </div>
    <a href="$home" class="nav-brand">
      <span class="brand-name">$brand</span>
      <span class="brand-sub">$brand_sub</span>
    </a>
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
        <p class="footer-title">$brand</p>
        <p class="desc">$description</p>
      </div>
      <div>
        <p class="footer-sub">تصفّح</p>
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

  document.getElementById('themeToggle').addEventListener('click', function () {
    var root = document.documentElement;
    var dark = root.dataset.theme === 'dark' ||
      (!root.dataset.theme && matchMedia('(prefers-color-scheme: dark)').matches);
    var next = dark ? 'light' : 'dark';
    root.dataset.theme = next;
    localStorage.setItem('theme', next);
  });

  var nl = document.getElementById('newsletterForm');
  if (nl && nl.dataset.subscribeAction) {
    // الإرسال إلى مزوّد النشرة (Kit)
    nl.addEventListener('submit', function (e) {
      e.preventDefault();
      var email = nl.querySelector('input[type=email]').value.trim();
      if (!email) return;
      var fd = new FormData();
      fd.append(nl.dataset.subscribeField, email);
      fetch(nl.dataset.subscribeAction, { method: 'POST', mode: 'no-cors', body: fd })
        .finally(function () {
          nl.outerHTML = '<p style="font-weight:500">' + nl.dataset.success + '</p>';
        });
    });
  } else if (nl && !nl.getAttribute('action')) {
    nl.addEventListener('submit', function (e) {
      e.preventDefault();
      var email = nl.querySelector('input[type=email]').value;
      location.href = 'mailto:' + nl.dataset.fallback +
        '?subject=' + encodeURIComponent('اشتراك في النشرة البريدية') +
        '&body=' + encodeURIComponent('أرغب بالاشتراك: ' + email);
    });
  }

  // البحث
  var POSTS = $search_index;
  var sInput = document.getElementById('searchInput');
  var sResults = document.getElementById('searchResults');
  function norm(s) { return (s || '').replace(/[\\u064B-\\u0652]/g, '').replace(/[أإآ]/g, 'ا').replace(/ة/g, 'ه').toLowerCase(); }
  function renderResults(q) {
    if (!q) { sResults.hidden = true; sResults.innerHTML = ''; return; }
    var nq = norm(q);
    var hits = POSTS.filter(function (p) {
      return norm(p.t).indexOf(nq) !== -1 || norm(p.e).indexOf(nq) !== -1 ||
             norm(p.c).indexOf(nq) !== -1 || norm(p.b).indexOf(nq) !== -1;
    }).slice(0, 6);
    sResults.innerHTML = hits.length
      ? hits.map(function (p) {
          return '<a href="' + p.u + '"><span class="r-title">' + p.t + '</span><span class="r-meta">' + p.c + ' · ' + p.d + '</span></a>';
        }).join('')
      : '<span class="r-none">لا نتائج</span>';
    sResults.hidden = false;
  }
  if (sInput) {
    sInput.addEventListener('input', function () { renderResults(sInput.value.trim()); });
    sInput.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        var first = sResults.querySelector('a');
        if (first) location.href = first.getAttribute('href');
      }
      if (e.key === 'Escape') { sResults.hidden = true; sInput.blur(); }
    });
    document.addEventListener('click', function (e) {
      if (!e.target.closest('.nav-search')) sResults.hidden = true;
    });
  }
})();
</script>
$extra_js
</body>
</html>
""")


_ALL_POSTS = []   # يملؤها main() لفهرس البحث


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html or "")
    text = (text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&#39;", "'").replace("&nbsp;", " "))
    return re.sub(r"\s+", " ", text).strip()


# ————— أدوات مساعدة: الروابط المطلقة وأبعاد الصور —————

def site_url(site):
    return (site.get("site_url") or "").rstrip("/")


def html_attr(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def _read_image_size(path: Path):
    """عرض وارتفاع صورة PNG أو JPEG أو WebP بمكتبة بايثون القياسية فقط."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    import struct
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return struct.unpack(">II", data[16:24])
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        kind = data[12:16]
        if kind == b"VP8 ":
            w, h = struct.unpack("<HH", data[26:30])
            return w & 0x3FFF, h & 0x3FFF
        if kind == b"VP8L":
            b = data[21:25]
            w = 1 + (((b[1] & 0x3F) << 8) | b[0])
            h = 1 + (((b[3] & 0xF) << 10) | (b[2] << 2) | ((b[1] & 0xC0) >> 6))
            return w, h
        if kind == b"VP8X":
            w = 1 + int.from_bytes(data[24:27], "little")
            h = 1 + int.from_bytes(data[27:30], "little")
            return w, h
    if data[:2] == b"\xff\xd8":
        i = 2
        while i < len(data) - 9:
            if data[i] != 0xFF:
                i += 1
                continue
            marker = data[i + 1]
            if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", data[i + 5:i + 9])
                return w, h
            i += 2 + struct.unpack(">H", data[i + 2:i + 4])[0]
    return None


def img_dims(src: str) -> str:
    """width/height للصورة (يمنع قفز الصفحة أثناء التحميل). src نسبي إلى جذر الموقع."""
    src = re.sub(r"^(\.\./)+", "", src or "")
    m = re.search(r"-(\d+)x(\d+)", Path(src).name)
    if m:
        w, h = int(m.group(1)), int(m.group(2))
        if w > 1600:                       # سانيتي يصغّرها إلى عرض 1600
            w, h = 1600, round(h * 1600 / w)
    else:
        size = _read_image_size(ROOT / src)
        if not size:
            return ""
        w, h = size
    return f' width="{w}" height="{h}"'


def add_body_img_dims(html: str) -> str:
    """أبعاد لصور متن التدوينة، وأول صورتين تُحمَّلان فوراً بلا تأجيل."""
    first = [0]

    def fix(m):
        tag = m.group(0)
        if "width=" not in tag:
            src = re.search(r'src="([^"]+)"', tag)
            if src:
                tag = tag.replace("<img ", "<img" + img_dims(src.group(1)) + " ", 1)
        if first[0] < 2:                  # أول صورتين في المتن تظهران مبكراً
            tag = tag.replace(' loading="lazy"', "")
            first[0] += 1
        return tag

    return re.sub(r"<img\b[^>]*>", fix, html)


def person_ld(site, full=False):
    url = site_url(site)
    a = site.get("about", {})
    p = {"@type": "Person", "@id": f"{url}/#person", "name": site["brand"], "url": f"{url}/about/"}
    if a.get("image"):
        p["image"] = f"{url}/{a['image']}"
    if full:
        p["description"] = _strip_html(a.get("paragraphs", [""])[0])
        books = a.get("books") or []
        if books:
            p["workExample"] = [{
                "@type": "Book", "name": b["title"], "inLanguage": "ar",
                "publisher": {"@type": "Organization", "name": b["publisher"]},
                "datePublished": b["year"], "url": b["link"],
                **({"image": f"{url}/{b['image']}"} if b.get("image") else {}),
            } for b in books]
    return p


def search_index_json(rel):
    idx = [{
        "t": p["title"], "e": p.get("excerpt", ""), "c": p.get("category", ""),
        "b": _strip_html(p.get("body", "")),
        "d": fmt_date(p["date"]), "u": f"{rel}post/{p['slug']}/",
    } for p in _ALL_POSTS]
    return json.dumps(idx, ensure_ascii=False).replace("</", "<\\/")


def ga_snippet(site):
    gid = (site.get("ga_id") or "").strip()
    if not gid:
        return ""
    return (
        f'<!-- Google Analytics (GA4) -->\n'
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={gid}"></script>\n'
        f'<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}'
        f"gtag('js',new Date());gtag('config','{gid}');</script>"
    )


def head_extra(site, *, rel, path, title, og_image="", preload="", jsonld=None):
    """canonical وog:url وصورة المشاركة وتحميل صورة LCP مسبقاً والبيانات المنظّمة."""
    out = []
    url = site_url(site)
    if url:
        canon = f"{url}/{path}"
        out.append(f'<link rel="canonical" href="{canon}">')
        out.append(f'<meta property="og:url" content="{canon}">')
        out.append(f'<meta property="og:site_name" content="{site["brand"]}">')
        out.append('<meta property="og:locale" content="ar_AR">')
    if og_image and url:
        out.append(f'<meta property="og:image" content="{url}/{og_image}">')
        out.append(f'<meta property="og:image:alt" content="{html_attr(title)}">')
        large = og_image.endswith("-og.jpg")
        out.append(f'<meta name="twitter:card" content="{"summary_large_image" if large else "summary"}">')
        out.append(f'<meta name="twitter:image" content="{url}/{og_image}">')
    if preload:
        out.append(f'<link rel="preload" as="image" href="{rel}{preload}" fetchpriority="high">')
    if jsonld:
        data = json.dumps(jsonld, ensure_ascii=False, indent=1).replace("</", "<\\/")
        out.append(f'<script type="application/ld+json">\n{data}\n</script>')
    return "\n".join(out)


def render_page(site, *, rel, title, description, main, path="", og_type="website", og_image="",
                preload="", jsonld=None, extra_js="", body_class=""):
    import datetime
    menu_links = "\n".join(
        f'    <a href="{(rel + item["url"]) or "./"}">{item["label"]}</a>' for item in site["nav"]
    )
    footer_links = "\n".join(
        f'          <a href="{(rel + item["url"]) or "./"}">{item["label"]}</a>' for item in site["nav"]
    )
    return PAGE.substitute(
        rel=rel, title=title, description=description,
        og_type=og_type,
        head_extra=head_extra(site, rel=rel, path=path, title=title, og_image=og_image,
                              preload=preload, jsonld=jsonld),
        brand=site["brand"], tagline=site["tagline"],
        menu_links=menu_links, footer_links=footer_links,
        footer_note=site["footer_note"],
        year=datetime.date.today().year,
        icon_menu=ICON_MENU, icon_x=ICON_X, icon_moon=ICON_MOON, icon_sun=ICON_SUN,
        main=main, extra_js=extra_js, body_class=body_class,
        home=rel or "./",
        search_placeholder=site.get("search_placeholder", "ابحث…"),
        brand_sub=site.get("brand_sub", ""),
        search_index=search_index_json(rel),
        ga=ga_snippet(site),
    )


def newsletter_section(site, heading_tag="h2"):
    n = site.get("newsletter")
    if not n:
        return ""
    action = n.get("action", "")
    return f"""
  <section class="newsletter">
    <div class="container"><div class="inner">
      <span class="label">{n['label']}</span>
      <{heading_tag}>{n['heading']}</{heading_tag}>
      <p>{n['text']}</p>
      <form id="newsletterForm" action="{action}" method="post"
            data-fallback="{n.get('fallback_email','')}"
            data-subscribe-action="{n.get('subscribe_action','')}"
            data-subscribe-field="{n.get('subscribe_field','')}"
            data-success="{n.get('success','تم الاشتراك ✓')}">
        <input type="email" name="email" autocomplete="email" required placeholder="{n['placeholder']}" aria-label="{n['placeholder']}">
        <button type="submit">{n['button']}</button>
      </form>
      <p class="note">{n.get('note','')}</p>
    </div></div>
  </section>"""


def img_pos(p):
    """نمط object-position من نقطة تركيز سانيتي، إن وُجدت."""
    pos = p.get("image_pos")
    return f' style="object-position:{pos}"' if pos else ""


def card_meta(p, sep='<span>·</span>'):
    parts = [f'<span>{fmt_date(p["date"])}</span>', f'<span>{p["category"]}</span>']
    if p.get("subcategory"):
        parts.append(f'<span>{p["subcategory"]}</span>')
    if p.get("reading_time"):
        parts.append(f'<span>{p["reading_time"]} دقائق</span>')
    return f"\n          {sep}\n          ".join(parts)


# ————— الصفحة الرئيسية —————

def build_home(site, posts):
    featured = next((p for p in posts if p["featured"]), posts[0])
    rest = [p for p in posts if p is not featured]
    rel = ""

    # البطاقتان الأوليان تظهران دون تمرير، فلا تأجيل لتحميل صورتيهما
    cards = "\n".join(f"""
      <a href="post/{p['slug']}/" class="post-card fade-in">
        <div class="thumb"><img src="{p['image']}" alt="{p['title']}"{img_dims(p['image'])}{' loading="lazy"' if i >= 2 else ''}{img_pos(p)}></div>
        <div class="card-body">
          <h3>{p['title']}</h3>
          <div class="meta">
            {card_meta(p)}
          </div>
        </div>
      </a>""" for i, p in enumerate(rest))

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
      <img src="{featured['image']}" alt=""{img_dims(featured['image'])} fetchpriority="high"{img_pos(featured)}>
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
        <a class="btn-read" href="post/{featured['slug']}/">{site.get('read_button', 'اقرأ التدوينة')}</a>
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
{newsletter_section(site)}
{pull}
</main>"""

    return render_page(
        site, rel=rel,
        title=f"{site['brand']} | {site['tagline']}",
        description=site["description"],
        path="", og_image=og_image_for(featured, site), preload=featured["image"],
        jsonld={
            "@context": "https://schema.org", "@type": "WebSite",
            "@id": f"{site_url(site)}/#website", "url": f"{site_url(site)}/",
            "name": site["brand"], "description": site["description"], "inLanguage": "ar",
            "author": person_ld(site), "publisher": {"@id": f"{site_url(site)}/#person"},
        },
        main=main, body_class="has-hero",
    )


def og_image_for(p, site):
    """صورة المشاركة: نسخة -og.jpg إن وُجدت، وإلا الغلاف إن كان JPEG/PNG، وإلا صورة الكاتب."""
    if p and p.get("og_image"):
        return p["og_image"]
    if p and p.get("image", "").lower().endswith((".jpg", ".jpeg", ".png")):
        return p["image"]
    return site.get("about", {}).get("og_image", "")


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
        <a href="{rel}post/{p['slug']}/" class="archive-row"
           data-cat="{p['category']}" data-sub="{p.get('subcategory','')}">
          <span class="date">{fmt_short(p['date'])}</span>
          <span class="cat">{p['category']}{' · ' + p['subcategory'] if p.get('subcategory') else ''}</span>
          <h3>{p['title']}</h3>
          {f'<span class="rt">{p["reading_time"]} د</span>' if p.get('reading_time') else ''}
        </a>""" for p in yposts)
        groups.append(f"""
      <div class="year-group" data-year="{year}">
        <div class="year-head">
          <h2 class="year">{year}</h2>
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
})();
</script>"""

    return render_page(
        site, rel=rel,
        title=f"الأرشيف | {site['brand']}",
        description="كل ما كُتب، مرتّباً بحسب الزمن.",
        path="archive/", og_image=og_image_for(None, site),
        main=main, extra_js=extra_js,
    )


# ————— عني —————

def books_section(a):
    books = a.get("books")
    if not books:
        return ""
    cards = "\n".join(f"""
      <div class="book-card fade-in">
        <a class="book-cover" href="{bk['link']}" target="_blank" rel="noopener">
          <img src="../{bk['image']}" alt="غلاف {bk['title']}"{img_dims(bk['image'])}>
        </a>
        <div class="book-body">
          <h3><a href="{bk['link']}" target="_blank" rel="noopener">{bk['title']}</a></h3>
          <p class="book-subtitle">{bk['subtitle']}</p>
          <div class="book-meta">
            <span>{bk['role']}</span>
            <span>·</span>
            <span>{bk['publisher']}</span>
            <span>·</span>
            <span>{bk['year']}</span>
            <span>·</span>
            <span>{bk['pages']}</span>
          </div>
          <p class="book-desc">{bk['description']}</p>
          <a class="book-link" href="{bk['link']}" target="_blank" rel="noopener">اقتنِ الكتاب ←<span class="sr-only"> «{bk['title']}»</span></a>
        </div>
      </div>""" for bk in books)
    return f"""
    <section class="books">
      <div class="section-head">
        <h2>{a.get('books_heading', 'كُتبي')}</h2>
        <div class="rule"></div>
      </div>
      <div class="books-grid">{cards}
      </div>
    </section>"""


def build_about(site):
    rel = "../"
    a = site["about"]
    paragraphs = "\n".join(f"        <p>{p}</p>" for p in a["paragraphs"])
    main = f"""
<main class="page">
  <div class="container">
    <div class="about-grid">
      <div class="about-image">
        <img src="{rel}{a['image']}" alt="صورة الكاتب"{img_dims(a['image'])} fetchpriority="high">
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
        <blockquote class="about-quote">{a['quote']}</blockquote>
      </div>
    </div>
{books_section(a)}
  </div>
</main>"""

    return render_page(
        site, rel=rel,
        title=f"عني | {site['brand']}",
        description=a["paragraphs"][0][:150],
        path="about/", og_image=og_image_for(None, site), preload=a["image"],
        jsonld={
            "@context": "https://schema.org", "@type": "ProfilePage",
            "name": f"عني | {site['brand']}", "url": f"{site_url(site)}/about/", "inLanguage": "ar",
            "mainEntity": person_ld(site, full=True),
        },
        main=main,
    )


# ————— صفحة النشرة —————

def build_subscribe(site):
    rel = "../"
    n = site.get("newsletter", {})
    main = f"""
<main class="page subscribe-page">
{newsletter_section(site, heading_tag="h1")}
</main>"""
    return render_page(
        site, rel=rel,
        title=f"{n.get('label', 'النشرة البريدية')} | {site['brand']}",
        description=n.get("text", site.get("description", "")),
        path="subscribe/", og_image=og_image_for(None, site),
        main=main,
    )


# ————— صفحة المقالة —————

def build_post(site, p):
    rel = "../../"
    body = add_body_img_dims(p["body"]).replace('src="assets/', f'src="{rel}assets/')
    pull = ""
    if p.get("pull_quote"):
        pull = f"""
  <div class="post-pull"><blockquote>{p['pull_quote']}</blockquote></div>"""

    main = f"""
<div class="progress-track" aria-hidden="true"><div class="bar" id="progressBar"></div></div>
<main>
  <header class="post-header">
    <div class="inner">
      <a href="{rel or './'}" class="back-link">← العودة</a>
      <div class="meta">
        <span class="chip">{p['category']}</span>
        {f'<span>{p["subcategory"]}</span>' if p.get('subcategory') else ''}
        <time datetime="{p['date'][:10]}">{fmt_date(p['date'])}</time>
        {f'<span>{p["reading_time"]} دقائق قراءة</span>' if p.get('reading_time') else ''}
      </div>
      <h1>{p['title']}</h1>
      <hr class="mistarah">
    </div>
  </header>

  <figure class="post-figure">
    <div class="cover"><img src="{rel}{p['image']}" alt="{p['title']}"{img_dims(p['image'])} fetchpriority="high"{img_pos(p)}></div>
  </figure>
{pull}
  <article class="post-body">
    <div class="prose-arabic">
{body}
    </div>
  </article>

  <div class="end-marker">■</div>
  <hr class="mistarah post-rule">
{newsletter_section(site)}
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
        path=f"post/{p['slug']}/", og_image=og_image_for(p, site), preload=p["image"],
        jsonld=post_ld(site, p),
        main=main, extra_js=extra_js,
    )


def post_ld(site, p):
    url = site_url(site)
    ld = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": p["title"], "description": p.get("excerpt", ""),
        "url": f"{url}/post/{p['slug']}/",
        "mainEntityOfPage": f"{url}/post/{p['slug']}/",
        "datePublished": p["date"], "inLanguage": "ar",
        "articleSection": p.get("category", ""),
        "author": person_ld(site), "publisher": person_ld(site),
    }
    img = og_image_for(p, site) or p.get("image")
    if img:
        ld["image"] = f"{url}/{img}"
    words = len(_strip_html(p.get("body", "")).split())
    if words:
        ld["wordCount"] = words
    return ld


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


# ————— ملفات الزواحف والوكلاء —————
# ملاحظة: لا شيء هنا يعتمد على وقت البناء، كي لا يُنشئ الـ Action تعديلاً كل عشر دقائق.

def build_sitemap(site, posts):
    url = site_url(site)
    if not url:
        return None
    latest = max((p["date"][:10] for p in posts), default="")
    pages = [("", latest), ("archive/", latest), ("about/", ""), ("subscribe/", "")]
    pages += [(f"post/{p['slug']}/", p["date"][:10]) for p in posts]
    rows = "\n".join(
        f"  <url><loc>{url}/{path}</loc>" + (f"<lastmod>{mod}</lastmod>" if mod else "") + "</url>"
        for path, mod in pages
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{rows}
</urlset>
"""


def build_robots(site):
    url = site_url(site)
    lines = ["User-agent: *", "Allow: /", ""]
    if url:
        lines.append(f"Sitemap: {url}/sitemap.xml")
    return "\n".join(lines) + "\n"


def build_llms(site, posts):
    url = site_url(site)
    if not url:
        return None
    items = "\n".join(
        f"- [{p['title']}]({url}/post/{p['slug']}/): {_strip_html(p.get('excerpt', ''))}" for p in posts
    )
    return f"""# {site['brand']}

> {site['description']}

مدونة شخصية بالعربية لماجد الأهدل.

## الصفحات

- [عني]({url}/about/): من هو الكاتب، وكتبه المنشورة
- [الأرشيف]({url}/archive/): كل التدوينات مرتّبة زمنياً
- [خلاصة RSS]({url}/feed.xml)

## التدوينات

{items}
"""


def build_security_txt(site):
    url = site_url(site)
    email = (site.get("newsletter") or {}).get("fallback_email", "")
    if not (url and email):
        return None
    import datetime
    expires = f"{datetime.date.today().year + 1}-12-31T23:59:59Z"   # يتغيّر مرة في السنة فقط
    return (f"Contact: mailto:{email}\n"
            f"Expires: {expires}\n"
            "Preferred-Languages: ar, en\n"
            f"Canonical: {url}/.well-known/security.txt\n")


# ————— التنفيذ —————

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

def latinize(html: str) -> str:
    """كل الأرقام في الموقع لاتينية."""
    return html.translate(ARABIC_DIGITS)


def main():
    site, posts = load()
    _ALL_POSTS.clear()
    _ALL_POSTS.extend(posts)

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copytree(ROOT / "assets", OUT / "assets")
    (OUT / ".nojekyll").write_text("")

    (OUT / "index.html").write_text(latinize(build_home(site, posts)), encoding="utf-8")

    (OUT / "archive").mkdir()
    (OUT / "archive" / "index.html").write_text(latinize(build_archive(site, posts)), encoding="utf-8")

    (OUT / "about").mkdir()
    (OUT / "about" / "index.html").write_text(latinize(build_about(site)), encoding="utf-8")

    (OUT / "subscribe").mkdir()
    (OUT / "subscribe" / "index.html").write_text(latinize(build_subscribe(site)), encoding="utf-8")

    for p in posts:
        d = OUT / "post" / p["slug"]
        d.mkdir(parents=True)
        (d / "index.html").write_text(latinize(build_post(site, p)), encoding="utf-8")

    feed = build_feed(site, posts)
    if feed:
        (OUT / "feed.xml").write_text(latinize(feed), encoding="utf-8")

    sitemap = build_sitemap(site, posts)
    if sitemap:
        (OUT / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (OUT / "robots.txt").write_text(build_robots(site), encoding="utf-8")
    llms = build_llms(site, posts)
    if llms:
        (OUT / "llms.txt").write_text(latinize(llms), encoding="utf-8")
    sec = build_security_txt(site)
    if sec:
        (OUT / ".well-known").mkdir()
        (OUT / ".well-known" / "security.txt").write_text(sec, encoding="utf-8")

    # دومين GitHub Pages الخاص
    url = site.get("site_url", "")
    if url:
        host = url.split("//")[-1].strip("/")
        if not host.endswith("github.io"):
            (OUT / "CNAME").write_text(host + "\n")

    n = 4 + len(posts)
    print(f"تم البناء ✓  {n} صفحات في docs/  ({len(posts)} مقالة)")


if __name__ == "__main__":
    main()
