#!/usr/bin/env python3
"""Static validation for NABZ Tools before GitHub Pages deployment (Persian site + English /en/ section)."""
from __future__ import annotations
import json, re, subprocess, sys, tempfile
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
SITE="https://nabzkhabarofficial.github.io/nabz-tools/"
TOOLS=["word-counter","percentage","unit-converter","qr-generator","image-compressor","image-resizer","image-converter","pdf-tools","json-formatter","base64","url-encoder","password-generator","text-case","color-converter","timestamp","age-calculator","date-difference","bmi","jalali-converter","number-to-words","digits-converter","loan-calculator","discount-vat","hash-generator","currency-converter","market-prices","gold-calculator","salary-calculator","deposit-interest","rent-converter","iran-validator","coloring-page","karaoke-maker","link-shortener"]
GUIDES=["word-counter-guide","qr-code-guide","image-compression-guide","image-to-pdf-guide","percentage-guide","unit-converter-guide","image-resize-guide","image-converter-guide","json-format-guide","base64-guide","url-encoding-guide","password-generator-guide","timestamp-guide","age-calculator-guide"]
# English section (Oct 2026): en/index.html, en/about.html, en/privacy.html, en/tools/<slug>.html
EN_TOOLS=list(TOOLS)  # every tool has an English page (Oct 15 2026)
errors=[]
def fail(msg): errors.append(msg)
def read(rel):
 p=ROOT/rel
 if not p.exists(): fail(f"missing file: {rel}"); return ""
 return p.read_text(encoding="utf-8")
def count(pattern,text,flags=re.I): return len(re.findall(pattern,text,flags))
pages=["index.html","about.html","privacy.html"]+[f"tools/{x}.html" for x in TOOLS]+["guides/index.html"]+[f"guides/{x}.html" for x in GUIDES]
en_pages=["en/index.html","en/about.html","en/privacy.html"]+[f"en/tools/{x}.html" for x in EN_TOOLS]
for rel in ["index.html","style.css","robots.txt","sitemap.xml","about.html","privacy.html","404.html",".github/workflows/pages.yml","assets/qrcode.min.js","assets/nabz.js","assets/home.css","assets/pro4.css","data/rates.json","assets/nabz-en.js","assets/en.css"]:
 if not (ROOT/rel).exists(): fail(f"missing required file: {rel}")
try:
 _r=json.loads((ROOT/"data/rates.json").read_text(encoding="utf-8"))
 if not _r.get("usd",{}).get("eur"): fail("data/rates.json: global rates missing")
except Exception as exc: fail(f"data/rates.json: invalid JSON: {exc}")
_js=(ROOT/"assets/nabz.js").read_text(encoding="utf-8") if (ROOT/"assets/nabz.js").exists() else ""
for x in TOOLS:
 if f'["{x}",' not in _js: fail(f"assets/nabz.js: tool switcher is missing {x}")
_jsen=(ROOT/"assets/nabz-en.js").read_text(encoding="utf-8") if (ROOT/"assets/nabz-en.js").exists() else ""
for x in EN_TOOLS:
 if f'["{x}",' not in _jsen: fail(f"assets/nabz-en.js: tool switcher is missing {x}")
 if f'"{x}"' not in _js.split("var EN=",1)[-1][:2000]: fail(f"assets/nabz.js: English link list is missing {x}")
_home=(ROOT/"index.html").read_text(encoding="utf-8") if (ROOT/"index.html").exists() else ""
for x in TOOLS:
 if f'href="tools/{x}.html"' not in _home: fail(f"index.html: no card for {x}")
_enhome=(ROOT/"en/index.html").read_text(encoding="utf-8") if (ROOT/"en/index.html").exists() else ""
for x in EN_TOOLS:
 if f'href="tools/{x}.html"' not in _enhome: fail(f"en/index.html: no card for {x}")
 if not (ROOT/f"tools/{x}.html").exists(): fail(f"en/tools/{x}.html: no Persian page to link to")
def canonical_for(rel):
 if rel=="index.html": return SITE
 if rel=="guides/index.html": return SITE+"guides/"
 if rel=="en/index.html": return SITE+"en/"
 return SITE+rel
for rel in pages+en_pages:
 html=read(rel)
 if not html: continue
 english=rel.startswith("en/")
 if english:
  if not re.search(r'<html\b[^>]*\blang="en"[^>]*\bdir="ltr"',html,re.I): fail(f"{rel}: missing en/ltr html attributes")
  if 'hreflang="fa"' not in html: fail(f"{rel}: missing link to the Persian version")
  if 'href="'+("../" if rel.count("/")==1 else "../../")+'assets/en.css"' not in html: fail(f"{rel}: missing assets/en.css")
 elif not re.search(r'<html\b[^>]*\blang="fa"[^>]*\bdir="rtl"',html,re.I): fail(f"{rel}: missing fa/rtl html attributes")
 if count(r"<title>[^<]+</title>",html)!=1: fail(f"{rel}: expected exactly one title")
 if not re.search(r'<meta\s+name="description"\s+content="[^"]+"',html,re.I): fail(f"{rel}: missing meta description")
 if not re.search(r'<meta\s+name="robots"\s+content="index,follow"',html,re.I): fail(f"{rel}: missing index,follow robots")
 canon=re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"',html,re.I)
 if not canon or canon.group(1)!=canonical_for(rel): fail(f"{rel}: canonical mismatch")
 if count(r"<h1\b",html)!=1: fail(f"{rel}: expected exactly one h1")
 if rel in ("index.html","en/index.html"):
  if '"@type":"WebSite"' not in html.replace('": "','":"'): fail(f"{rel}: missing WebSite JSON-LD")
  if 'id="faq"' not in html or '<details>' not in html: fail(f"{rel}: visible FAQ section missing")
 elif rel.startswith(("tools/","en/tools/")):
  for token in ['property="og:title"','property="og:description"','property="og:url"','name="twitter:card"','class="related-tools"','"@type":"BreadcrumbList"']:
   if token not in html.replace('": "','":"'): fail(f"{rel}: missing {token}")
  if 'href="'+("../../" if english else "../")+'style.css"' not in html: fail(f"{rel}: missing stylesheet")
 elif rel.startswith("guides/"):
  if rel=="guides/index.html" and '"@type":"CollectionPage"' not in html: fail("guides/index.html: missing CollectionPage JSON-LD")
  for token in ['property="og:title"','property="og:description"','property="og:url"','name="twitter:card"','"@type":"BreadcrumbList"']:
   if token not in html: fail(f"{rel}: missing {token}")
  if 'href="../style.css"' not in html: fail(f"{rel}: missing stylesheet")
 else:
  if 'href="'+("../" if english else "")+'style.css"' not in html: fail(f"{rel}: missing stylesheet")
 ids=re.findall(r'\bid="([^"]+)"',html,re.I); seen=set(); dup=set()
 for ident in ids:
  if ident in seen: dup.add(ident)
  seen.add(ident)
 if dup: fail(f"{rel}: duplicate ids: {', '.join(sorted(dup))}")
 for block in re.findall(r'<script\b[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',html,re.I|re.S):
  try: json.loads(block.strip())
  except Exception as exc: fail(f"{rel}: invalid JSON-LD: {exc}")
 attrs=re.findall(r'\b(?:href|src)="([^"]+)"',html,re.I)
 for target in attrs:
  if target.startswith(("#","mailto:","tel:","data:","javascript:")): continue
  parsed=urlparse(target)
  if parsed.scheme or target.startswith("//"): continue
  clean=target.split("#",1)[0].split("?",1)[0]
  if not clean: continue
  dest=((ROOT/rel).parent/clean).resolve()
  try: dest.relative_to(ROOT.resolve())
  except ValueError: fail(f"{rel}: link escapes repository: {target}"); continue
  if not dest.exists(): fail(f"{rel}: broken local target: {target}")
for rel in pages+en_pages:
 html=read(rel); blocks=re.findall(r'<script\b(?![^>]*type="application/ld\+json")[^>]*>(.*?)</script>',html,re.I|re.S)
 for i,js in enumerate(blocks,1):
  if not js.strip(): continue
  with tempfile.NamedTemporaryFile("w",suffix=".js",encoding="utf-8",delete=False) as f: f.write(js); tmp=f.name
  try:
   proc=subprocess.run(["node","--check",tmp],capture_output=True,text=True)
   if proc.returncode: fail(f"{rel}: JavaScript syntax error in inline script {i}: {proc.stderr.strip()}")
  finally: Path(tmp).unlink(missing_ok=True)
for rel in ["assets/nabz.js","assets/nabz-en.js"]:
 proc=subprocess.run(["node","--check",str(ROOT/rel)],capture_output=True,text=True)
 if proc.returncode: fail(f"{rel}: JavaScript syntax error: {proc.stderr.strip()}")
sitemap=read("sitemap.xml"); robots=read("robots.txt"); locs=re.findall(r"<loc>(.*?)</loc>",sitemap,re.I|re.S)
expected_urls=[SITE]+[SITE+f"tools/{x}.html" for x in TOOLS]+[SITE+"about.html",SITE+"privacy.html",SITE+"guides/"]+[SITE+f"guides/{x}.html" for x in GUIDES]
expected_urls+=[SITE+"en/"]+[SITE+f"en/tools/{x}.html" for x in EN_TOOLS]+[SITE+"en/about.html",SITE+"en/privacy.html"]
if len(locs)!=len(expected_urls) or set(locs)!=set(expected_urls): fail(f"sitemap.xml: expected {len(expected_urls)} exact URLs, found {len(locs)}")
if f"Sitemap: {SITE}sitemap.xml" not in robots: fail("robots.txt: sitemap declaration missing")
if not re.search(r"User-agent:\s*\*\s*\nAllow:\s*/",robots): fail("robots.txt: expected global Allow: /")
actual_tools=sorted(p.name for p in (ROOT/"tools").glob("*.html")); expected_tools=sorted(f"{x}.html" for x in TOOLS)
if actual_tools!=expected_tools: fail("tools/: unexpected or missing tool pages")
actual_en=sorted(p.name for p in (ROOT/"en/tools").glob("*.html")) if (ROOT/"en/tools").exists() else []
if actual_en!=sorted(f"{x}.html" for x in EN_TOOLS): fail("en/tools/: unexpected or missing English tool pages")
if errors:
 print("NABZ Tools validation FAILED")
 for e in errors: print(f"- {e}")
 sys.exit(1)
print(f"NABZ Tools validation PASSED: {len(pages)} Persian pages + {len(en_pages)} English pages, {len(TOOLS)} tools ({len(EN_TOOLS)} in English), {len(GUIDES)} guides, sitemap/robots, JSON-LD, links, duplicate IDs, and inline JS syntax checked.")
