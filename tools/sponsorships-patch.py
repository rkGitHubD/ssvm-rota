"""Sponsorships redesigned: one table of all records, a New sponsorship form (item from
the items, the services, or a new item), an item-wise report, and the item list.
The stored data and its use on the Rota Sheet / Dashboard are unchanged.

Usage: python3 tools/sponsorships-patch.py Index.html
"""
import os
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()
new = open(os.path.join(os.path.dirname(__file__), "sponsorships.jsx"), encoding="utf-8").read()

start = s.index("function MDSponsorships(")
end = s.index("\n}\n", start) + 3
assert s.count("function MDSponsorships(") == 1
s = s[:start] + new + s[end:]
old = '''<MDSponsorships sponsorships={sponsorships} upSponsorships={upSponsorships} showToast={showToast}/>'''
assert s.count(old) == 1
s = s.replace(old, '''<MDSponsorships sponsorships={sponsorships} upSponsorships={upSponsorships} showToast={showToast} sevas={sevas}/>''')
open(p, "w", encoding="utf-8").write(s)
print("patched", p)
