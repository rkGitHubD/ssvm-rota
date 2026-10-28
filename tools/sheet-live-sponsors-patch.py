"""Rota Sheet: sponsorships added after a sheet was opened now show on it (the phone
sheet only had the list from when it was opened). Closed sheets keep what they had.

Usage: python3 tools/sheet-live-sponsors-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()
old = '''  const currentSheet = sheetFound && !sheetFound.prasadhamProvider && sheetFound.status !== "closed" && plannedPrasadham(sheetFound)
    ? { ...sheetFound, prasadhamProvider: plannedPrasadham(sheetFound) } : sheetFound;'''
new = '''  // Sponsorships for the sheet's day, as they are now
  const liveSponsors = sh => (sponsorships||[]).flatMap(a => (a.donations||[]).filter(d => (d.rotaDates||[]).includes(sh.date)).map(d => d.donor ? d.donor + " (" + a.name + ")" : a.name))
    .concat(servicePaidOn(rotaSheets, sh.date).map(d => d.donor + " (" + d.area + ")")).join(", ");
  // An open sheet follows the plan: prasadham and sponsorships added after it was opened still show
  const currentSheet = sheetFound && sheetFound.status !== "closed"
    ? { ...sheetFound, prasadhamProvider: sheetFound.prasadhamProvider || plannedPrasadham(sheetFound), sponsors: liveSponsors(sheetFound) || sheetFound.sponsors || "" } : sheetFound;'''
assert s.count(old) == 1
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("patched", p)
