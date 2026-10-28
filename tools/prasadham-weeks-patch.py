"""Prasadham: the plan panel folds; a provider's weeks (from / to Sunday) are set from the
Add / Edit provider form; the Rota Sheet shows the planned provider even if the sheet was
opened before the plan was made.

Usage: python3 tools/prasadham-weeks-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def swap(old, rep, n=1):
    global s
    assert s.count(old) == n, (s.count(old), old[:80])
    s = s.replace(old, rep)


# ── Rota days for any range of years, shared by the plan and the provider form ──
swap('''function prasadhamSlots(specials = [], n = 8) {
  const today = new Date(); today.setHours(0,0,0,0);
  const ymd = localDay;
  const rows = [...getWeeksForYear(today.getFullYear()), ...getWeeksForYear(today.getFullYear() + 1)]
    .map(w => ({ day:ymd(w.date), date:w.date, keys:[w.key], occasions:[] }));
  specials.forEach(sp => {
    const day = ymd(sp.date), row = rows.find(r => r.day === day);
    if (row) { row.keys.push(sp.key); row.occasions.push(sp.label || sp.tag || "Special"); }
    else rows.push({ day, date:new Date(sp.date), keys:[sp.key], occasions:[sp.label || sp.tag || "Special"] });
  });
  return rows.filter(r => r.date >= today).sort((a, b) => a.day.localeCompare(b.day)).slice(0, n);
}''', '''function rotaDayRows(fromYear, toYear, specials = []) {
  let weeks = [];
  for (let y = fromYear; y <= toYear; y++) weeks = weeks.concat(getWeeksForYear(y));
  const rows = weeks.map(w => ({ day:localDay(w.date), date:w.date, keys:[w.key], occasions:[], sunday:true }));
  specials.forEach(sp => {
    const day = localDay(sp.date), row = rows.find(r => r.day === day);
    if (row) { row.keys.push(sp.key); row.occasions.push(sp.label || sp.tag || "Special"); }
    else rows.push({ day, date:new Date(sp.date), keys:[sp.key], occasions:[sp.label || sp.tag || "Special"] });
  });
  return rows.sort((a, b) => a.day.localeCompare(b.day));
}
function prasadhamSlots(specials = [], n = 8) {
  const today = localDay(new Date()), y = new Date().getFullYear();
  return rotaDayRows(y, y + 1, specials).filter(r => r.day >= today).slice(0, n);
}
// The Sundays (and any occasion on them) from one date to another
const sundaysBetween = (from, to, specials) =>
  rotaDayRows(parseInt(from), parseInt(to), specials).filter(r => r.sunday && r.day >= from && r.day <= to);
const shortSun = d => new Date(d + "T12:00:00").toLocaleDateString("en-GB",{ weekday:"short", day:"numeric", month:"short" });''')

# ── The plan folds (closed to start with) ──
swap('''function PrasadhamPlan({ prasadham = [], rotas = {}, upRotas, specials = [], showToast }) {
  const [n, setN] = useState(8);''', '''function PrasadhamPlan({ prasadham = [], rotas = {}, upRotas, specials = [], showToast }) {
  const [n, setN] = useState(8);
  const [open, setOpen] = useState(false);''')
swap('''    <div className="bg-white rounded-2xl border border-amber-200 shadow-sm p-5 space-y-3">
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex-1 min-w-[12rem]">
          <h3 className="font-bold text-slate-800">🍛 Prasadham plan — next''', '''    <div className="bg-white rounded-2xl border border-amber-200 shadow-sm p-5 space-y-3">
      <div className="flex items-center gap-2 flex-wrap">
        <button onClick={()=>setOpen(!open)} className={"text-slate-400 text-xs transition-transform " + (open ? "rotate-90" : "")} title={open ? "Fold" : "Open"}>▶</button>
        <div className="flex-1 min-w-[12rem]">
          <h3 className="font-bold text-slate-800"><span onClick={()=>setOpen(!open)} className="cursor-pointer">🍛 Prasadham plan</span> — next''')
swap('''        <button onClick={fill} className="bg-amber-500 hover:bg-amber-600 text-white px-3 py-2 rounded-xl text-xs font-bold">✨ Fill empty weeks</button>
        <button onClick={share} title="Share on WhatsApp" className="bg-[#25D366] hover:bg-[#1ebe57] text-white px-3 py-2 rounded-xl text-xs font-bold">Share list</button>
      </div>
      <div className="divide-y divide-slate-100">''', '''        {open && <button onClick={fill} className="bg-amber-500 hover:bg-amber-600 text-white px-3 py-2 rounded-xl text-xs font-bold">✨ Fill empty weeks</button>}
        {open && <button onClick={share} title="Share on WhatsApp" className="bg-[#25D366] hover:bg-[#1ebe57] text-white px-3 py-2 rounded-xl text-xs font-bold">Share list</button>}
        {!open && <button onClick={()=>setOpen(true)} className="text-xs bg-amber-50 border border-amber-200 text-amber-700 px-3 py-1.5 rounded-lg font-semibold">Show</button>}
      </div>
      {open && <div className="divide-y divide-slate-100">''')
swap('''              {prasadham.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>); })}
      </div>
    </div>
  );
}''', '''              {prasadham.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>); })}
      </div>}
    </div>
  );
}''')

# ── Provider form: the weeks they provide ──
swap('''function MDPrasadham({ prasadham, upPrasadham, showToast, rotas = {}, upRotas, specials = [] }) {
  var blank = {name:"",phone:"",amount:"",collection:""};''', '''function MDPrasadham({ prasadham, upPrasadham, showToast, rotas = {}, upRotas, specials = [] }) {
  var blank = {name:"",phone:"",amount:"",collection:"",fromWeek:"",toWeek:""};
  // A provider's upcoming rota days, from the rota itself
  var upcomingFor = function(id){ var y = new Date().getFullYear(), today = localDay(new Date());
    return rotaDayRows(y, y + 1, specials).filter(function(r){ return r.day >= today && r.keys.some(function(k){ return (rotas[k]||{}).prasadhamId === id; }); }); };
  var setWeeks = function(rows, id){ upRotas(function(prev){ var next = { ...prev };
    rows.forEach(function(r){ r.keys.forEach(function(k){ next[k] = { ...(next[k]||{}), prasadhamId:id }; }); }); return next; }); };''')
swap('''  var save = function(){
    if (!form.name.trim()) return showToast("Name is required","error");
    if (editId) {
      upPrasadham(prasadham.map(function(p){return p.id===editId?{...p,...form}:p;}));
      showToast("Provider updated"); setEditId(null);
    } else {
      upPrasadham([...prasadham,{id:uid(),...form,name:form.name.trim()}]);
      showToast("Provider added");
    }
    setForm(blank);
  };''', '''  var save = function(){
    if (!form.name.trim()) return showToast("Name is required","error");
    var from = form.fromWeek, to = form.toWeek || form.fromWeek, rows = [];
    if (from || form.toWeek) {
      if (!from) return showToast("Choose the first Sunday","error");
      if (new Date(from+"T12:00:00").getDay() !== 0 || new Date(to+"T12:00:00").getDay() !== 0) return showToast("The weeks must start and end on a Sunday","error");
      if (to < from) return showToast("The last Sunday is before the first","error");
      rows = sundaysBetween(from, to, specials);
    }
    var { fromWeek, toWeek, ...details } = form;
    var id = editId || uid();
    var taken = rows.filter(function(r){ return r.keys.some(function(k){ var o = (rotas[k]||{}).prasadhamId; return o && o !== id; }); }).length;
    if (editId) upPrasadham(prasadham.map(function(p){return p.id===editId?{...p,...details}:p;}));
    else upPrasadham([...prasadham,{id:id,...details,name:details.name.trim()}]);
    if (rows.length) setWeeks(rows, id);
    showToast((editId ? "Provider updated" : "Provider added") + (rows.length ? " · " + rows.length + " Sunday" + (rows.length>1?"s":"") + " set" + (taken ? " (" + taken + " replaced someone else)" : "") : ""));
    setEditId(null); setForm(blank);
  };''')
swap('''  var edit   = function(p){ setEditId(p.id); setForm({name:p.name,phone:p.phone||"",amount:p.amount||"",collection:p.collection||""}); };''',
     '''  var edit   = function(p){ setEditId(p.id); setForm({name:p.name,phone:p.phone||"",amount:p.amount||"",collection:p.collection||"",fromWeek:"",toWeek:""}); };''')
swap('''          <Field label="Collection Method" value={form.collection} onChange={v=>setForm({...form,collection:v})} placeholder="e.g. Cash, Bank Transfer"/>
          <button onClick={save} className="w-full bg-indigo-600 text-white rounded-lg py-2.5 text-sm font-bold hover:bg-indigo-700">{editId?"Save Changes":"Add Provider"}</button>''',
     '''          <Field label="Collection Method" value={form.collection} onChange={v=>setForm({...form,collection:v})} placeholder="e.g. Cash, Bank Transfer"/>
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 space-y-2">
            <div className="text-xs font-bold text-amber-800">🗓 Weeks they provide prasadham</div>
            <div className="grid grid-cols-2 gap-2">
              <label className="text-xs font-semibold text-slate-600">From Sunday<input type="date" value={form.fromWeek} onChange={e=>setForm({...form,fromWeek:e.target.value})} className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white"/></label>
              <label className="text-xs font-semibold text-slate-600">To Sunday<input type="date" value={form.toWeek} min={form.fromWeek} onChange={e=>setForm({...form,toWeek:e.target.value})} className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white"/></label>
            </div>
            {form.fromWeek && <p className="text-xs text-amber-700">{(function(){ var t = form.toWeek || form.fromWeek;
              if (new Date(form.fromWeek+"T12:00:00").getDay() !== 0 || new Date(t+"T12:00:00").getDay() !== 0) return "⚠ Pick Sundays";
              if (t < form.fromWeek) return "⚠ The last Sunday is before the first";
              var n = sundaysBetween(form.fromWeek, t, specials).length; return n + " Sunday" + (n>1?"s":"") + ": " + shortSun(form.fromWeek) + (t !== form.fromWeek ? " – " + shortSun(t) : ""); })()}</p>}
            {editId && (function(){ var up = upcomingFor(editId); return up.length > 0 && (
              <div className="flex flex-wrap gap-1">{up.map(function(r){ return (
                <span key={r.day} className="inline-flex items-center gap-1 bg-white border border-amber-200 text-amber-800 text-xs px-2 py-0.5 rounded-full">{shortSun(r.day)}
                  <button onClick={function(){ setWeeks([r], ""); }} title="Take them off this day" className="font-bold text-amber-400 hover:text-red-600">×</button></span>); })}</div>); })()}
            <p className="text-xs text-slate-400">Optional. Every Sunday in between is set to this provider and shows on the Rota Calendar and that day's Rota Sheet.</p>
          </div>
          <button onClick={save} className="w-full bg-indigo-600 text-white rounded-lg py-2.5 text-sm font-bold hover:bg-indigo-700">{editId?"Save Changes":"Add Provider"}</button>''')
# Provider cards: their next days
swap('''                {p.collection && <span>🏦 {p.collection}</span>}
              </div>''', '''                {p.collection && <span>🏦 {p.collection}</span>}
              </div>
              {(function(){ var up = upcomingFor(p.id); return up.length > 0 && <div className="text-xs text-amber-700 mt-1">🗓 {up.slice(0,4).map(function(r){ return shortSun(r.day); }).join(" · ")}{up.length > 4 ? " (+" + (up.length-4) + " more)" : ""}</div>; })()}''')

# ── Rota Sheet: a provider planned after the sheet was opened still shows ──
swap('''  const currentSheet = rotaSheets.find(s => s.id === editId);''',
     '''  const sheetFound = rotaSheets.find(s => s.id === editId);
  const plannedPrasadham = sh => { const id = allSlots.filter(sl => localDay(sl.date) === sh.date).map(sl => (rotas[sl.key]||{}).prasadhamId).find(Boolean);
    return ((prasadham||[]).find(p => p.id === id) || {}).name || ""; };
  const currentSheet = sheetFound && !sheetFound.prasadhamProvider && sheetFound.status !== "closed" && plannedPrasadham(sheetFound)
    ? { ...sheetFound, prasadhamProvider: plannedPrasadham(sheetFound) } : sheetFound;''')
# Phone sheet header: prasadham shows even without a priest
swap('''          {s.priest && <div className="text-indigo-200 text-xs mt-0.5">🔔 {s.priest}{s.prasadhamProvider?" · 🍛 "+s.prasadhamProvider:""}</div>}''',
     '''          {(s.priest || s.prasadhamProvider) && <div className="text-indigo-200 text-xs mt-0.5">{[s.priest && "🔔 " + s.priest, s.prasadhamProvider && "🍛 Prasadham: " + s.prasadhamProvider].filter(Boolean).join(" · ")}</div>}''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
