"""Assignments: generate next year's rota from configurable rules; weeks can be marked
Confirmed, and the schedule shows TBC until they are.

Usage: python3 tools/generator-patch.py Index.html
"""
import os
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()
component = open(os.path.join(os.path.dirname(__file__), "rota-generator.jsx"), encoding="utf-8").read()


def swap(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


swap("function MDAssignments(", component + "function MDAssignments(")
swap('''generalOffers=[], upGeneralOffers, config={} }) {''', '''generalOffers=[], upGeneralOffers, config={}, upConfig }) {''')
swap('''    <SwapPlanner members={members} rotas={rotas} upRotas={upRotas} allSlots={allSlots} generalOffers={generalOffers} upGeneralOffers={upGeneralOffers} showToast={showToast}/>''',
     '''    <SwapPlanner members={members} rotas={rotas} upRotas={upRotas} allSlots={allSlots} generalOffers={generalOffers} upGeneralOffers={upGeneralOffers} showToast={showToast}/>
    <RotaGenerator members={members} rotas={rotas} upRotas={upRotas} specials={specials} config={config} upConfig={upConfig} showToast={showToast}/>''')
swap('''upGeneralOffers={upGeneralOffers} config={config}/>}''', '''upGeneralOffers={upGeneralOffers} config={config} upConfig={upConfig}/>}''')
swap('''function MasterData({ config={}, generalOffers=[],''', '''function MasterData({ config={}, upConfig, generalOffers=[],''')
swap('''<MasterData config={config} generalOffers''', '''<MasterData config={config} upConfig={upConfig} generalOffers''')

# ── Week editor: Confirmed ticks for Rota Lead and Secondary ──────────────────
swap('''                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">🎯 Rota Lead</h4>''',
     '''                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">🎯 Rota Lead</h4>
                  {local.lead && <label className="flex items-center gap-1 text-xs font-semibold text-emerald-700">
                    <input type="checkbox" checked={local.leadConfirmed !== false} onChange={e=>setLocal({...local,leadConfirmed:e.target.checked})}/> Confirmed</label>}
                </div>''')
swap('''                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-3">🟣 Secondary <span className="font-normal">({(local.secondary||[]).length})</span></h4>''',
     '''                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">🟣 Secondary <span className="font-normal">({(local.secondary||[]).length})</span></h4>
                  {(local.secondary||[]).length > 0 && <label className="flex items-center gap-1 text-xs font-semibold text-emerald-700">
                    <input type="checkbox" checked={local.secondaryConfirmed !== false} onChange={e=>setLocal({...local,secondaryConfirmed:e.target.checked})}/> Confirmed</label>}
                </div>''')

# ── Schedule PDF: assigned but not confirmed shows TBC ────────────────────────
swap('''    if (done) counts.done++; else if (lead) counts.ok++; else counts.tbc++;''',
     '''    // Generated weeks are saved unconfirmed (leadConfirmed / secondaryConfirmed false) until confirmed
    const leadOk = !!lead && r.leadConfirmed !== false, secOk = !!sec && r.secondaryConfirmed !== false;
    if (done) counts.done++; else if (leadOk) counts.ok++; else counts.tbc++;''')
swap('''      + "</td><td>" + (esc(lead) || who0(done)) + "</td>" + status(done, lead)
      + "<td>" + (esc(sec) || who0(done)) + "</td>" + status(done, sec)''',
     '''      + "</td><td>" + (esc(lead) || who0(done)) + "</td>" + status(done, leadOk)
      + "<td>" + (esc(sec) || who0(done)) + "</td>" + status(done, secOk)''')

# ── An applied swap is an agreed change: mark that role confirmed ─────────────
swap('''      rr.swapLog = [...(rr.swapLog||[]), { at, role, from, to:r.toId }];''',
     '''      rr.swapLog = [...(rr.swapLog||[]), { at, role, from, to:r.toId }];
      if (role === "lead") rr.leadConfirmed = true; else rr.secondaryConfirmed = true;''')

# Keep false confirmation flags when a Sunday's rota is merged with a special occasion's
swap('''...Object.fromEntries(Object.entries(rotas[sl.key] || {}).filter(([k, v]) => Array.isArray(v) ? v.length : v)) };''',
     '''...Object.fromEntries(Object.entries(rotas[sl.key] || {}).filter(([k, v]) => typeof v === "boolean" || (Array.isArray(v) ? v.length : v))) };''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
