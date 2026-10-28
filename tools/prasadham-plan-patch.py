"""Prasadham plan: a rolling 6-8 week list of who brings prasadham on each rota day,
with a Fill empty weeks button and WhatsApp sharing; the provider also shows in the
Rota Calendar's day panel.

Usage: python3 tools/prasadham-plan-patch.py Index.html
"""
import os
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()
new = open(os.path.join(os.path.dirname(__file__), "prasadham-plan.jsx"), encoding="utf-8").read()


def swap(old, rep, n=1):
    global s
    assert s.count(old) == n, (s.count(old), old[:80])
    s = s.replace(old, rep)


swap('''// ── MD: Prasadham Providers ──────────────────────────────────────────────────
function MDPrasadham({ prasadham, upPrasadham, showToast }) {''', new + '''// ── MD: Prasadham Providers ──────────────────────────────────────────────────
function MDPrasadham({ prasadham, upPrasadham, showToast, rotas = {}, upRotas, specials = [] }) {''')
swap('''  var edit   = function(p){ setEditId(p.id); setForm({name:p.name,phone:p.phone||"",amount:p.amount||"",collection:p.collection||""}); };
  return (
    <div className="grid md:grid-cols-5 gap-6">''', '''  var edit   = function(p){ setEditId(p.id); setForm({name:p.name,phone:p.phone||"",amount:p.amount||"",collection:p.collection||""}); };
  return (
    <div className="space-y-6">
    <PrasadhamPlan prasadham={prasadham} rotas={rotas} upRotas={upRotas} specials={specials} showToast={showToast}/>
    <div className="grid md:grid-cols-5 gap-6">''')
swap('''              <button onClick={function(){remove(p.id);}} className="text-xs bg-red-50 border border-red-200 text-red-500 px-2.5 py-1.5 rounded-lg hover:bg-red-100 font-medium">Delete</button>
            </div>
          </div>
        );})}
      </div>
    </div>
  );
}''', '''              <button onClick={function(){remove(p.id);}} className="text-xs bg-red-50 border border-red-200 text-red-500 px-2.5 py-1.5 rounded-lg hover:bg-red-100 font-medium">Delete</button>
            </div>
          </div>
        );})}
      </div>
    </div>
    </div>
  );
}''')
swap('''<MDPrasadham    prasadham={prasadham} upPrasadham={upPrasadham} showToast={showToast}/>''',
     '''<MDPrasadham    prasadham={prasadham} upPrasadham={upPrasadham} showToast={showToast} rotas={rotas} upRotas={upRotas} specials={specials}/>''')
# Rota Calendar day panel: who brings prasadham
swap('''                  <div className="text-xs text-slate-500 mb-2">👥 {(rota.primary||[]).length+(rota.secondary||[]).length} volunteer{((rota.primary||[]).length+(rota.secondary||[]).length)!==1?"s":""}</div>
                )}
                <button onClick={()=>setView("list")}''', '''                  <div className="text-xs text-slate-500 mb-2">👥 {(rota.primary||[]).length+(rota.secondary||[]).length} volunteer{((rota.primary||[]).length+(rota.secondary||[]).length)!==1?"s":""}</div>
                )}
                {rota.prasadhamId && (prasadham.find(p => p.id === rota.prasadhamId) || {}).name && (
                  <div className="text-xs text-amber-700 font-semibold mb-2">🍛 Prasadham: {prasadham.find(p => p.id === rota.prasadhamId).name}</div>
                )}
                <button onClick={()=>setView("list")}''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
