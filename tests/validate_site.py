#!/usr/bin/env python3
"""Static validation for NABZ Tools before GitHub Pages deployment."""
from __future__ import annotations
import json, re, subprocess, sys, tempfile
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
SITE="https://nabzkhabarofficial.github.io/nabz-tools/"
TOOLS=["word-counter","percentage","unit-converter","qr-generator","image-compressor","image-resizer","image-converter","pdf-tools","json-formatter","base64","url-encoder","password-generator","text-case","color-converter","timestamp","age-calculator","date-difference","bmi"]
GUIDES=["word-counter-guide","qr-code-guide","image-compression-guide","image-to-pdf-guide"]
errors=[]
def fail(msg): errors.append(msg)
def read(rel):
 p=ROOT/rel
 if not p.exists(): fail(f"missing file: {rel}"); return ""
 return p.read_text(encoding="utf-8")
def count(pattern,text,flags=re.I): return len(re.findall(pattern,text,flags))
pages=["index.html","about.html","privacy.html"]+[f"tools/{x}.html" for x in TOOLS]+[f"guides/{x}.html" for x in GUIDES]
for rel in ["index.html","style.css","robots.txt","sitemap.xml","about.html","privacy.html","404.html",".github/workflows/pages.yml","assets/qrcode.min.js"]:
 if not (ROOT/rel).exists(): fail(f"missing required file: {rel}")
for rel in pages:
 html=read(rel)
 if not html: continue
 if not re.search(r'<html\b[^>]*\blang="fa"[^>]*\bdir="rtl"',html,re.I): fail(f"{rel}: missing fa/rtl html attributes")
 if count(r"<title>[^<]+</title>",html)!=1: fail(f"{rel}: expected exactly one title")
 if not re.search(r'<meta\s+name="description"\s+content="[^"]+"',html,re.I): fail(f"{rel}: missing meta description")
 if not re.search(r'<meta\s+name="robots"\s+content="index,follow"',html,re.I): fail(f"{rel}: missing index,follow robots")
 canon=re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"',html,re.I); expected=SITE+(rel if rel!="index.html" else "")
 if not canon or canon.group(1)!=expected: fail(f"{rel}: canonical mismatch")
 if count(r"<h1\b",html)!=1: fail(f"{rel}: expected exactly one h1")
 if rel=="index.html":
  if '"@type":"WebSite"' not in html: fail("index.html: missing WebSite JSON-LD")
  if '"@type":"FAQPage"' not in html: fail("index.html: missing FAQPage JSON-LD")
  if 'id="faq"' not in html or '<details>' not in html: fail("index.html: visible FAQ section missing")
 elif rel.startswith("tools/"):
  for token in ['property="og:title"','property="og:description"','property="og:url"','name="twitter:card"','class="related-tools"','"@type":"BreadcrumbList"']:
   if token not in html: fail(f"{rel}: missing {token}")
  if 'href="../style.css"' not in html: fail(f"{rel}: missing stylesheet")
 elif rel.startswith("guides/"):
  for token in ['property="og:title"','property="og:description"','property="og:url"','name="twitter:card"','"@type":"BreadcrumbList"']:
   if token not in html: fail(f"{rel}: missing {token}")
  if 'href="../style.css"' not in html: fail(f"{rel}: missing stylesheet")
 else:
  if 'href="style.css"' not in html: fail(f"{rel}: missing stylesheet")
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
for rel in pages:
 html=read(rel); blocks=re.findall(r'<script\b(?![^>]*type="application/ld\+json")[^>]*>(.*?)</script>',html,re.I|re.S)
 for i,js in enumerate(blocks,1):
  if not js.strip(): continue
  with tempfile.NamedTemporaryFile("w",suffix=".js",encoding="utf-8",delete=False) as f: f.write(js); tmp=f.name
  try:
   proc=subprocess.run(["node","--check",tmp],capture_output=True,text=True)
   if proc.returncode: fail(f"{rel}: JavaScript syntax error in inline script {i}: {proc.stderr.strip()}")
  finally: Path(tmp).unlink(missing_ok=True)
sitemap=read("sitemap.xml"); robots=read("robots.txt"); locs=re.findall(r"<loc>(.*?)</loc>",sitemap,re.I|re.S)
expected_urls=[SITE]+[SITE+f"tools/{x}.html" for x in TOOLS]+[SITE+"about.html",SITE+"privacy.html"]+[SITE+f"guides/{x}.html" for x in GUIDES]
if len(locs)!=len(expected_urls) or set(locs)!=set(expected_urls): fail(f"sitemap.xml: expected {len(expected_urls)} exact URLs, found {len(locs)}")
if f"Sitemap: {SITE}sitemap.xml" not in robots: fail("robots.txt: sitemap declaration missing")
if not re.search(r"User-agent:\s*\*\s*\nAllow:\s*/",robots): fail("robots.txt: expected global Allow: /")
actual_tools=sorted(p.name for p in (ROOT/"tools").glob("*.html")); expected_tools=sorted(f"{x}.html" for x in TOOLS)
if actual_tools!=expected_tools: fail("tools/: unexpected or missing tool pages")
if errors:
 print("NABZ Tools validation FAILED")
 for e in errors: print(f"- {e}")
 sys.exit(1)
print(f"NABZ Tools validation PASSED: {len(pages)} pages, {len(TOOLS)} tools, {len(GUIDES)} guides, sitemap/robots, JSON-LD, FAQ, links, duplicate IDs, and inline JS syntax checked.")
