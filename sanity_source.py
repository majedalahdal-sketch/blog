# -*- coding: utf-8 -*-
"""
جلب المحتوى من Sanity — يُستخدم تلقائياً عندما يوجد content/sanity.json:

  { "projectId": "xxxx", "dataset": "production" }

يجلب المقالات عبر GROQ، يحوّل نص Portable Text إلى HTML،
وينزّل الصور محلياً إلى assets/images/sanity/ ليبقى الموقع مستقلاً.
"""
import json, ssl, subprocess, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).parent

GROQ = """*[_type == "post" && !(_id in path("drafts.**"))] | order(date desc) {
  title, "slug": slug.current, date, category, subcategory,
  "reading_time": readingTime, excerpt, "pull_quote": pullQuote,
  "is_featured": featured, body,
  "image_url": mainImage.asset->url, "image_id": mainImage.asset->_id,
  "image_ext": mainImage.asset->extension
}"""


def _http_get(url: str) -> bytes:
    # curl أولاً (شهادات بايثون المحلية ناقصة على هذا الجهاز)
    try:
        return subprocess.run(["curl", "-sf", url], capture_output=True, check=True).stdout
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return urllib.request.urlopen(url, context=ctx).read()


# ————— تحويل Portable Text إلى HTML —————

def _render_marks(span, mark_defs):
    text = (span.get("text") or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    for mark in span.get("marks", []):
        link = next((d for d in mark_defs if d.get("_key") == mark and d.get("_type") == "link"), None)
        if link:
            text = f'<a href="{link.get("href", "#")}">{text}</a>'
        elif mark == "strong":
            text = f"<strong>{text}</strong>"
        elif mark == "em":
            text = f"<em>{text}</em>"
    return text


def portable_text_to_html(blocks) -> str:
    html, list_open = [], False
    for b in blocks or []:
        if b.get("_type") == "image":
            ref = (b.get("asset") or {}).get("_ref", "")
            html.append(f'<img src="{_asset_ref_to_url(ref)}" alt="">')
            continue
        if b.get("_type") != "block":
            continue
        style = b.get("style", "normal")
        content = "".join(_render_marks(s, b.get("markDefs", [])) for s in b.get("children", []))
        if b.get("listItem"):
            if not list_open:
                html.append("<ul>")
                list_open = True
            html.append(f"<li>{content}</li>")
            continue
        if list_open:
            html.append("</ul>")
            list_open = False
        if not content.strip():
            continue
        tag = {"h2": "h2", "h3": "h3", "blockquote": "blockquote"}.get(style, "p")
        html.append(f"<{tag}>{content}</{tag}>")
    if list_open:
        html.append("</ul>")
    return "\n\n".join(html)


_CFG = {}

def _asset_ref_to_url(ref: str) -> str:
    # image-<id>-<dims>-<ext> → cdn url
    parts = ref.split("-")
    if len(parts) < 4:
        return ""
    return f"https://cdn.sanity.io/images/{_CFG['projectId']}/{_CFG['dataset']}/{parts[1]}-{parts[2]}.{parts[3]}"


# ————— الصور: تنزيل محلي مع تخزين مؤقت —————

def _localize_image(url: str, asset_id: str, ext: str) -> str:
    imgdir = ROOT / "assets" / "images" / "sanity"
    imgdir.mkdir(parents=True, exist_ok=True)
    name = f"{asset_id.replace('image-', '')}.{ext}"
    dest = imgdir / name
    if not dest.exists():
        dest.write_bytes(_http_get(url + "?w=1600&fit=max&auto=format"))
    return f"assets/images/sanity/{name}"


# ————— الواجهة الرئيسية للمولّد —————

def fetch_posts() -> list | None:
    """يعيد قائمة مقالات بنفس شكل ملفات .md، أو None إذا لم يُفعَّل سانيتي."""
    cfg_path = ROOT / "content" / "sanity.json"
    if not cfg_path.exists():
        return None
    _CFG.update(json.loads(cfg_path.read_text()))
    q = urllib.parse.quote(GROQ)
    url = f"https://{_CFG['projectId']}.apicdn.sanity.io/v2024-01-01/data/query/{_CFG['dataset']}?query={q}"
    rows = json.loads(_http_get(url))["result"]

    posts = []
    for r in rows:
        if not r.get("slug"):
            continue
        image = ""
        if r.get("image_url"):
            image = _localize_image(r["image_url"], r["image_id"], r.get("image_ext", "jpg"))
        posts.append({
            "slug": r["slug"],
            "title": r.get("title", ""),
            "date": r.get("date", ""),
            "category": r.get("category", ""),
            "subcategory": r.get("subcategory") or "",
            "reading_time": str(int(r["reading_time"])) if r.get("reading_time") else "",
            "excerpt": r.get("excerpt", ""),
            "pull_quote": r.get("pull_quote") or "",
            "featured": bool(r.get("is_featured")),
            "image": image,
            "body": portable_text_to_html(r.get("body")),
        })
    return posts
