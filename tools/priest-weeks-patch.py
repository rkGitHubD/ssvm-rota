"""Priests: a week-by-week list. Every rota day has the default priest unless a week is
changed; any week can be given another priest, or a new priest added and assigned there.

Usage: python3 tools/priest-weeks-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def swap(old, rep, n=1):
    global s
    assert s.count(old) == n, (s.count(old), old[:80])
    s = s.replace(old, rep)


swap('''function MDPriests({ priests, upPriests, showToast }) {''', '''// Each rota day's priest: rotas[key].priestId, or the default priest when it's not set
function PriestWeeks({ priests = [], upPriests, rotas = {}, upRotas, specials = [], showToast }) {
  const [n, setN] = useState(8);
  const [open, setOpen] = useState(true);
  const [adding, setAdding] = useState(null);          // the day a new priest is being added for
  const [np, setNp] = useState({ name:"", phone:"" });
  const def = priests.find(p => p.isDefault) || priests[0];
  const y = new Date().getFullYear(), today = localDay(new Date());
  const days = rotaDayRows(y, y + 1, specials).filter(r => r.day >= today);
  const slots = days.slice(0, n);
  const chosen = r => { const id = r.keys.map(k => (rotas[k] || {}).priestId).find(Boolean); return id && priests.some(p => p.id === id) ? id : ""; };
  const isChange = r => { const id = chosen(r); return !!id && (!def || id !== def.id); };
  const assign = (r, id) => upRotas(prev => { const next = { ...prev }; r.keys.forEach(k => { next[k] = { ...(next[k] || {}), priestId: id }; }); return next; });
  const pick = (r, v) => { if (v === "+new") { setAdding(r.day); setNp({ name:"", phone:"" }); return; } assign(r, v); };
  const addAndAssign = r => {
    const name = np.name.trim();
    if (!name) return showToast("Enter the priest's name","error");
    const found = priests.find(p => p.name.toLowerCase() === name.toLowerCase());
    const id = found ? found.id : uid();
    if (!found) upPriests([...priests, { id, name, phone: np.phone.trim(), normalFee:"", specialFee:"", isDefault: !priests.length }]);
    assign(r, id); setAdding(null); showToast(name + " is the priest on " + shortSun(r.day));
  };
  const changes = days.filter(isChange);
  return (
    <div className="bg-white rounded-2xl border border-indigo-200 shadow-sm p-5 space-y-3">
      <div className="flex items-center gap-2 flex-wrap">
        <button onClick={()=>setOpen(!open)} className={"text-slate-400 text-xs transition-transform " + (open ? "rotate-90" : "")}>▶</button>
        <div className="flex-1 min-w-[12rem]">
          <h3 className="font-bold text-slate-800"><span onClick={()=>setOpen(!open)} className="cursor-pointer">🔔 Priest for each week</span> — next
            <select value={n} onChange={e=>setN(parseInt(e.target.value))} className="mx-1.5 border border-slate-200 rounded-lg px-1.5 py-0.5 text-sm bg-white">{[8,13,26,52].map(x => <option key={x} value={x}>{x}</option>)}</select>weeks</h3>
          <p className="text-xs text-slate-400 mt-0.5">{def ? def.name + " (default) takes every week unless you change it." : "Add a priest and set them as default."}
            {changes.length > 0 && <span className="text-amber-700 font-semibold"> Changed: {changes.map(r => shortSun(r.day) + " – " + (priests.find(p => p.id === chosen(r)) || {}).name).join(", ")}</span>}</p>
        </div>
      </div>
      {open && <div className="divide-y divide-slate-100">
        {slots.map(r => { const id = chosen(r), ch = isChange(r); return (
          <div key={r.day} className="py-2 space-y-2">
            <div className="flex items-center gap-2 flex-wrap text-sm">
              <span className="w-28 font-medium text-slate-700">{shortSun(r.day)}</span>
              <span className="flex-1 min-w-[6rem] text-xs text-violet-700 font-semibold truncate">{r.occasions.map(o => "★ " + o).join(" · ")}</span>
              {ch && <button onClick={()=>assign(r, "")} className="text-xs text-slate-500 underline">Back to {def ? def.name : "default"}</button>}
              <select value={adding === r.day ? "+new" : (ch ? id : "")} onChange={e=>pick(r, e.target.value)}
                className={"border rounded-lg px-2 py-1.5 text-sm w-52 " + (ch ? "border-amber-300 bg-amber-50 text-amber-800 font-semibold" : "border-slate-200 bg-white text-slate-700")}>
                <option value="">{def ? def.name + " (default)" : "— No priest —"}</option>
                {priests.filter(p => !def || p.id !== def.id).map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                <option value="+new">+ Add a new priest…</option>
              </select>
            </div>
            {adding === r.day && (
              <div className="flex gap-2 flex-wrap items-center bg-indigo-50 border border-indigo-200 rounded-xl p-2">
                <input value={np.name} onChange={e=>setNp({ ...np, name:e.target.value })} placeholder="Priest's name" className="flex-1 min-w-[8rem] border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white"/>
                <input value={np.phone} onChange={e=>setNp({ ...np, phone:e.target.value })} placeholder="Phone (optional)" className="w-36 border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white"/>
                <button onClick={()=>addAndAssign(r)} className="bg-indigo-600 text-white text-xs font-bold px-3 py-2 rounded-lg">Add for {shortSun(r.day)}</button>
                <button onClick={()=>setAdding(null)} className="text-xs text-slate-500">Cancel</button>
              </div>
            )}
          </div>); })}
      </div>}
    </div>
  );
}

function MDPriests({ priests, upPriests, showToast, rotas = {}, upRotas, specials = [] }) {''')
swap('''<MDPriests      priests={priests} upPriests={upPriests} showToast={showToast}/>''',
     '''<MDPriests      priests={priests} upPriests={upPriests} showToast={showToast} rotas={rotas} upRotas={upRotas} specials={specials}/>''')
swap('''  var setDefault = function(id){ upPriests(priests.map(function(p){return {...p,isDefault:p.id===id};})); showToast("Default priest updated"); };
  return (
    <div className="grid md:grid-cols-5 gap-6">''', '''  var setDefault = function(id){ upPriests(priests.map(function(p){return {...p,isDefault:p.id===id};})); showToast("Default priest updated"); };
  return (
    <div className="space-y-6">
    <PriestWeeks priests={priests} upPriests={upPriests} rotas={rotas} upRotas={upRotas} specials={specials} showToast={showToast}/>
    <div className="grid md:grid-cols-5 gap-6">''')
swap('''        );})}
      </div>
    </div>
  );
}

// ─── Master Data ─────────────────────────────────────────────────────────────''', '''        );})}
      </div>
    </div>
    </div>
  );
}

// ─── Master Data ─────────────────────────────────────────────────────────────''')
open(p, "w", encoding="utf-8").write(s)
print("patched", p)
