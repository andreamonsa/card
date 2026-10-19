#!/usr/bin/env python3
"""Build the NFC card site.

Reads site.json and every people/<slug>.json, then writes the static site to
docs/ (the folder GitHub Pages serves):

    docs/<slug>/index.html   the card page
    docs/<slug>/<slug>.vcf   the "Save contact" file

Run:  python3 build.py
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "docs"
REQUIRED = ["firstName", "lastName", "email", "phone", "linkedin"]

ARROW = ('<svg class="arrow" viewBox="0 0 16 16" fill="none" stroke="currentColor" '
         'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
         '<path d="M5 11 11 5M6 5h5v5"/></svg>')

NOINDEX_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow, noarchive">
<meta name="color-scheme" content="light only">
<title>{company}</title>
<style>html,body{{height:100%;margin:0;background:#FAFAF8}}body{{display:flex;align-items:center;justify-content:center}}img{{width:160px;height:auto}}</style>
</head><body><img src="{logo}" alt="{company}"></body></html>
"""


def fail(msg):
    sys.exit(f"build.py: {msg}")


def render(template, values):
    def sub(m):
        key = m.group(1)
        if key not in values:
            fail(f"template uses {{{{{key}}}}} but no value was provided")
        return values[key]
    return re.sub(r"\{\{(\w+)\}\}", sub, template)


def vcard_escape(value):
    return (value.replace("\\", "\\\\").replace("\n", "\\n")
            .replace(",", "\\,").replace(";", "\\;"))


def build_vcard(p, company):
    e = vcard_escape
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{e(p['lastName'])};{e(p['firstName'])};;;",
        f"FN:{e(p['fullName'])}",
        f"ORG:{e(company)}",
    ]
    if p.get("title"):
        lines.append(f"TITLE:{e(p['title'])}")
    lines += [
        f"TEL;TYPE=CELL,VOICE:{p['phoneDial']}",
        f"EMAIL;TYPE=INTERNET,WORK:{p['email']}",
        # iOS shows this as a LinkedIn profile; Android falls back to the URL below.
        f"X-SOCIALPROFILE;TYPE=linkedin:{p['linkedin']}",
        f"item1.URL:{p['linkedin']}",
        "item1.X-ABLabel:LinkedIn",
        "END:VCARD",
    ]
    # Lines are deliberately not folded at 75 chars: some Android importers
    # don't unfold them, which breaks long URLs. iOS and Android accept long lines.
    return "\r\n".join(lines) + "\r\n"


def load_person(path, site):
    p = json.loads(path.read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED if not str(p.get(k, "")).strip()]
    if missing:
        fail(f"{path.name} is missing: {', '.join(missing)}")
    slug = path.stem
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        fail(f"{path.name}: file name must be lowercase letters, digits and dashes (it becomes the URL)")

    p["slug"] = slug
    p["company"] = p.get("company") or site["company"]
    p["fullName"] = f"{p['firstName']} {p['lastName']}".strip()
    p["phoneDisplay"] = p.get("phoneDisplay") or p["phone"]
    p["phoneDial"] = re.sub(r"[^\d+]", "", p["phone"])
    handle = re.search(r"linkedin\.com/(in/[^/?#]+)", p["linkedin"])
    p["linkedinHandle"] = "/" + handle.group(1) if handle else p["linkedin"]
    return p


def main():
    site = json.loads((ROOT / "site.json").read_text(encoding="utf-8"))
    template = (ROOT / "templates" / "card.html").read_text(encoding="utf-8")
    people = [load_person(f, site) for f in sorted((ROOT / "people").glob("*.json"))]
    if not people:
        fail("no people/*.json files found")

    # docs/ is fully generated: wipe it so removed people disappear too.
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "assets").mkdir(parents=True)
    logo = Path(site["logo"])
    shutil.copy2(ROOT / logo, OUT / "assets" / logo.name)
    logo_rel = f"assets/{logo.name}"

    base = site.get("baseUrl", "").rstrip("/")
    esc = lambda s: html.escape(str(s), quote=True)

    for p in people:
        vcf_name = f"{p['slug']}.vcf"
        og_image = f'<meta property="og:image" content="{esc(base + "/" + logo_rel)}">' if base else ""
        values = {
            "fullName": esc(p["fullName"]),
            "title": esc(p.get("title", "")),
            "company": esc(p["company"]),
            "companyUpper": esc(p["company"].upper()),
            "email": esc(p["email"]),
            "phoneDisplay": esc(p["phoneDisplay"]),
            "phoneDial": esc(p["phoneDial"]),
            "linkedin": esc(p["linkedin"]),
            "linkedinHandle": esc(p["linkedinHandle"]),
            "logo": esc(logo_rel),
            "accent": esc(site.get("accent", "#BE4B43")),
            "vcfFile": esc(vcf_name),
            "ogImage": og_image,
            "arrow": ARROW,
        }
        page_dir = OUT / p["slug"]
        page_dir.mkdir()
        (page_dir / "index.html").write_text(render(template, values), encoding="utf-8")
        (page_dir / vcf_name).write_bytes(build_vcard(p, p["company"]).encode("utf-8"))
        print(f"  built /{p['slug']}/")

    landing = NOINDEX_PAGE.format(company=esc(site["company"]), logo=esc(logo_rel))
    (OUT / "index.html").write_text(landing, encoding="utf-8")
    (OUT / "404.html").write_text(landing, encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print(f"Done: {len(people)} card(s) in docs/")


if __name__ == "__main__":
    main()
