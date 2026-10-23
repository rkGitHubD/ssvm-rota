"""Generated rota: special occasions on other days get Rota Lead "Committee" and Secondary TBC.
A rota day can be led by the Committee (rota.committee = true) instead of a member.

Usage: python3 tools/committee-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def swap(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


# ── Generator: specials on other days are Committee-led and left out of the shares ─
swap('''    const L = planRole(d.length, leads.map(m => m.id).filter(keep), rules);   // Rota Leads first
    const S = planRole(d.length, secs.map(m => m.id).filter(keep), rules);
    setPlan(d.map((x, i) => ({ ...x, lead: L[i], sec: S[i] })));''',
     '''    // Special occasions on other days: Rota Lead is the Committee, Secondary TBC; the rest are shared out
    const n = d.filter(x => !x.special).length;
    const L = planRole(n, leads.map(m => m.id).filter(keep), rules);   // Rota Leads first
    const S = planRole(n, secs.map(m => m.id).filter(keep), rules);
    let k = 0;
    setPlan(d.map(x => x.special ? { ...x, lead: COMMITTEE, sec: "" } : { ...x, lead: L[k], sec: S[k++] }));''')
swap('''      const id = p[f]; if (!id) { issues[i+f] = "Nobody"; return; }''',
     '''      const id = p[f]; if (id === COMMITTEE) return; if (!id) { issues[i+f] = p.special && f === "sec" ? "" : "Nobody"; return; }''')
swap('''        lead: p.lead || "", secondary: p.sec ? [p.sec] : [], leadConfirmed: false, secondaryConfirmed: false, generated: year };''',
     '''        lead: p.lead === COMMITTEE ? "" : (p.lead || ""), committee: p.lead === COMMITTEE, secondary: p.sec ? [p.sec] : [],
        leadConfirmed: p.lead === COMMITTEE, secondaryConfirmed: false, generated: year };''')
swap('''                              {(f === "lead" ? leads : secs).map(m => <option key={m.id} value={m.id}>{m.name}</option>)}''',
     '''                              {f === "lead" && <option value={COMMITTEE}>🏛 Committee</option>}
                              {(f === "lead" ? leads : secs).map(m => <option key={m.id} value={m.id}>{m.name}</option>)}''')
swap('''                Give special occasions on other days their own Rota Lead and Secondary</label>''',
     '''                Include special occasions on other days (Rota Lead: Committee, Secondary: TBC)</label>''')
swap('''const DEFAULT_ROTA_RULES = { minGap: 2, includeSpecials: true, maxPer: {}, exclude: [] };''',
     '''const DEFAULT_ROTA_RULES = { minGap: 2, includeSpecials: true, maxPer: {}, exclude: [] };
// Stand-in for "the Committee" as Rota Lead in the generator's lists (saved as rota.committee)
const COMMITTEE = "__committee__";''')

# ── Schedule PDF ──────────────────────────────────────────────────────────────
swap('''    const lead = name(r.lead), sec = (r.secondary || []).map(name).filter(Boolean).join(", ");''',
     '''    const lead = r.committee ? "Committee" : name(r.lead), sec = (r.secondary || []).map(name).filter(Boolean).join(", ");''')

# ── Day summary and week editor ───────────────────────────────────────────────
swap('''            <InfoPill label="Rota Lead" value={selRota.lead ? getName(selRota.lead) : "Not assigned"} filled={!!selRota.lead} icon="🎯"/>''',
     '''            <InfoPill label="Rota Lead" value={selRota.committee ? "Committee" : selRota.lead ? getName(selRota.lead) : "Not assigned"} filled={!!selRota.lead || !!selRota.committee} icon="🎯"/>''')
swap('''                  <button onClick={()=>setLocal({...local,lead:""})}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm border transition-colors ${!local.lead?"bg-slate-100 border-slate-300 font-semibold":"border-transparent hover:bg-slate-50 text-slate-500"}`}>— None</button>''',
     '''                  <button onClick={()=>setLocal({...local,lead:"",committee:false})}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm border transition-colors ${!local.lead&&!local.committee?"bg-slate-100 border-slate-300 font-semibold":"border-transparent hover:bg-slate-50 text-slate-500"}`}>— None</button>
                  <button onClick={()=>setLocal({...local,lead:"",committee:true})}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm border transition-colors ${local.committee?"bg-indigo-50 border-indigo-300 text-indigo-700 font-semibold":"border-transparent hover:bg-slate-50"}`}>🏛 Committee</button>''')
swap('''                    <button key={m.id} onClick={()=>setLocal({...local,lead:m.id})}''',
     '''                    <button key={m.id} onClick={()=>setLocal({...local,lead:m.id,committee:false})}''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
