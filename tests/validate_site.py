#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
files=['index.html','assets/nabz.js','assets/home.css','assets/pro4.css','tools/market-prices.html','tools/gold-calculator.html','tools/salary-calculator.html','tools/deposit-interest.html','tools/rent-converter.html','tools/iran-validator.html']
for f in files:
 p=ROOT/f
 if not p.exists(): print('missing',f);sys.exit(1)
 if f.endswith('.js'):
  r=subprocess.run(['node','--check',str(p)],capture_output=True,text=True)
  if r.returncode: print(r.stderr);sys.exit(1)
print('NABZ Tools validation PASSED')
