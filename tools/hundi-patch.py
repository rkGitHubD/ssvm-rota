"""Hundi moves from the Rota Sheet to Master Data → Finance as "Hundi collections":
cash counted from the collection box now and then, added to the balance sheet.

Stored as rota-hundi: [{ id, date, amount, countedBy, witness, notes, at }].
Old sheets that recorded a hundi amount still count in Finance and their printout.

Usage: python3 tools/hundi-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def swap(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


def cut(start, end):
    global s
    assert s.count(start) == 1, start
    i = s.index(start)
    j = s.index(end, i)
    s = s[:i] + s[j:]


# ── App data: rota-hundi ──────────────────────────────────────────────────────
swap('''  const [priests,       setPriests]       = useState([]);''',
     '''  const [priests,       setPriests]       = useState([]);
  const [hundi,         setHundi]         = useState([]);''')
swap('''  const upPrasadham    = v => { setPrasadham(v);    DB.set("rota-prasadham",    v); };''',
     '''  const upPrasadham    = v => { setPrasadham(v);    DB.set("rota-prasadham",    v); };
  const upHundi        = v => { setHundi(v);        DB.set("rota-hundi",        v); };''')
swap('''    setPrasadham(storedPrasadham);''', '''    setPrasadham(storedPrasadham);
    setHundi(LS.get("rota-hundi", []));''')
swap('''        setPrasadham(g("rota-prasadham", []));''', '''        setPrasadham(g("rota-prasadham", []));
        setHundi(g("rota-hundi", []));''')
swap('''prasadham={prasadham} upPrasadham={upPrasadham} priests={priests} upPriests={upPriests}/>}''',
     '''prasadham={prasadham} upPrasadham={upPrasadham} priests={priests} upPriests={upPriests} hundi={hundi} upHundi={upHundi}/>}''')
swap('''itineraries,prasadham,priests}}/>}''', '''itineraries,prasadham,priests,hundi}}/>}''')
swap('''    "rota-prasadham":    allData.prasadham,''', '''    "rota-prasadham":    allData.prasadham,
    "rota-hundi":        allData.hundi,''')
swap('''prasadham, upPrasadham, priests, upPriests }) {
  const [section, setSection] = useState("members");''',
     '''prasadham, upPrasadham, priests, upPriests, hundi=[], upHundi }) {
  const [section, setSection] = useState("members");''')
swap('''<MDFinance      rotaSheets={rotaSheets}/>}''', '''<MDFinance      rotaSheets={rotaSheets} hundi={hundi} upHundi={upHundi} showToast={showToast}/>}''')

# ── Finance: Hundi collections panel and totals ───────────────────────────────
PANEL = r'''// ─── Hundi collections: the collection box, counted now and then ─────────────
function HundiCollections({ hundi, upHundi, showToast, shown }) {
  const today = new Date().toISOString().slice(0, 10);
  const blank = { date: today, amount: "", countedBy: "", witness: "", notes: "" };
  const [form, setForm] = useState(null);       // null, or the entry being added / edited
  const [delId, setDelId] = useState(null);
  const ic = "w-full border border-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-300";
  const save = () => {
    const amt = parseFloat(form.amount);
    if (!form.date || !(amt > 0)) return showToast("Enter the date counted and an amount","error");
    if (!form.countedBy.trim()) return showToast("Enter who counted it","error");
    const entry = { ...form, amount: amt.toFixed(2), countedBy: form.countedBy.trim(), witness: form.witness.trim(), notes: form.notes.trim(), at: new Date().toISOString() };
    upHundi(form.id ? hundi.map(h => h.id === form.id ? entry : h) : [...hundi, { ...entry, id: uid() }]);
    showToast(form.id ? "Hundi count updated" : "Hundi count added"); setForm(null);
  };
  const list = shown.slice().sort((a, b) => b.date.localeCompare(a.date));
  const total = shown.reduce((t, h) => t + parseFloat(h.amount || 0), 0);
  return (
    <div className="bg-white rounded-2xl border border-emerald-200 shadow-sm p-5 space-y-3">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex-1">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">🏺 Hundi collections</h3>
          <p className="text-xs text-slate-400 mt-0.5">Cash from the hundi, counted now and then. Each count is added to income and the balance sheet.</p>
        </div>
        <div className="text-right"><div className="text-xs text-slate-400">Total shown</div><div className="text-lg font-black text-emerald-700">£{total.toFixed(2)}</div></div>
        {!form && <button onClick={()=>setForm(blank)} className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-xl text-sm font-bold">+ Add hundi count</button>}
      </div>
      {form && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 grid sm:grid-cols-2 gap-2">
          <label className="text-xs font-semibold text-slate-600">Date counted *<input type="date" value={form.date} max={today} onChange={e=>setForm({...form,date:e.target.value})} className={ic}/></label>
          <label className="text-xs font-semibold text-slate-600">Amount £ *<input type="number" min="0" step="0.01" value={form.amount} onChange={e=>setForm({...form,amount:e.target.value})} placeholder="0.00" className={ic}/></label>
          <label className="text-xs font-semibold text-slate-600">Counted by *<input value={form.countedBy} onChange={e=>setForm({...form,countedBy:e.target.value})} placeholder="Names" className={ic}/></label>
          <label className="text-xs font-semibold text-slate-600">Witnessed by<input value={form.witness} onChange={e=>setForm({...form,witness:e.target.value})} placeholder="Name" className={ic}/></label>
          <label className="text-xs font-semibold text-slate-600 sm:col-span-2">Notes<input value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})} placeholder="e.g. Banked on Monday" className={ic}/></label>
          <div className="sm:col-span-2 flex gap-2">
            <button onClick={save} className="flex-1 bg-emerald-600 text-white rounded-lg py-2 text-sm font-bold hover:bg-emerald-700">{form.id ? "Save changes" : "Add"}</button>
            <button onClick={()=>setForm(null)} className="flex-1 bg-white border border-slate-200 text-slate-600 rounded-lg py-2 text-sm font-medium">Cancel</button>
          </div>
        </div>
      )}
      {list.length === 0 ? <p className="text-sm text-slate-400">No hundi counts{hundi.length ? " in this period" : " yet"}.</p> : (
        <div className="divide-y divide-slate-100">
          {list.map(h => (
            <div key={h.id} className="py-2 flex items-center gap-3 text-sm flex-wrap">
              <span className="w-24 font-medium text-slate-700">{new Date(h.date+"T12:00:00").toLocaleDateString("en-GB",{day:"numeric",month:"short",year:"numeric"})}</span>
              <span className="flex-1 min-w-0 text-slate-500 truncate">Counted by {h.countedBy}{h.witness ? " · witness "+h.witness : ""}{h.notes ? " · "+h.notes : ""}</span>
              <span className="font-bold text-emerald-700">£{parseFloat(h.amount).toFixed(2)}</span>
              {delId === h.id ? (
                <span className="flex gap-2"><button onClick={()=>{ upHundi(hundi.filter(x => x.id !== h.id)); setDelId(null); showToast("Hundi count removed"); }} className="text-xs bg-red-600 text-white px-2 py-1 rounded">Remove</button>
                  <button onClick={()=>setDelId(null)} className="text-xs text-slate-500">Keep</button></span>
              ) : (
                <span className="flex gap-2"><button onClick={()=>setForm({ ...blank, ...h })} className="text-xs text-indigo-600">Edit</button>
                  <button onClick={()=>setDelId(h.id)} className="text-xs text-red-500">Remove</button></span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

'''
swap("function MDFinance({ rotaSheets=[] }) {", PANEL + '''function MDFinance({ rotaSheets=[], hundi=[], upHundi, showToast }) {''')
# Months come from sheets and hundi counts
swap('''  months.sort(function(a,b){return a.key.localeCompare(b.key);});''',
     '''  hundi.forEach(function(h){
    var d = new Date(h.date+"T12:00:00");
    var key = d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0");
    if (!seenMonths[key]){ seenMonths[key]=true; months.push({key, label:d.toLocaleDateString("en-GB",{month:"long",year:"numeric"})}); }
  });
  months.sort(function(a,b){return a.key.localeCompare(b.key);});
  var hundiShown = filterMonth==="all" ? hundi : hundi.filter(function(h){ return (h.date||"").slice(0,7)===filterMonth; });
  var hundiCounted = hundiShown.reduce(function(t,h){return t+parseFloat(h.amount||0);},0);''')
# Sheet hundi (older sheets) plus the counts
swap('''  var totalHundi     = sum(sorted, function(s){return parseFloat((s.hundi&&s.hundi.amount)||0);});''',
     '''  var totalHundi     = sum(sorted, function(s){return parseFloat((s.hundi&&s.hundi.amount)||0);}) + hundiCounted;''')
swap('''         + parseFloat((s.hundi&&s.hundi.amount)||0);
  });''', '''         + parseFloat((s.hundi&&s.hundi.amount)||0);
  }) + hundiCounted;''')
# Empty state: still show the hundi panel
swap('''  if (closed.length === 0) return (
    <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
      <div className="text-5xl mb-3">📊</div>
      <p className="font-semibold text-slate-500">No closed rota sheets yet</p>
      <p className="text-sm text-slate-400 mt-1">Financial data appears once sheets are closed</p>
    </div>
  );''',
     '''  var hundiPanel = <HundiCollections hundi={hundi} upHundi={upHundi} showToast={showToast} shown={hundiShown}/>;
  if (closed.length === 0 && hundi.length === 0) return (
    <div className="space-y-5">
      {hundiPanel}
      <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
        <div className="text-5xl mb-3">📊</div>
        <p className="font-semibold text-slate-500">No closed rota sheets yet</p>
        <p className="text-sm text-slate-400 mt-1">Financial data appears once sheets are closed</p>
      </div>
    </div>
  );''')
swap('''      {/* KPI summary */}''', '''      {hundiPanel}

      {/* KPI summary */}''')
swap('''          <div className="text-emerald-200 text-xs mt-1">{sorted.length} session{sorted.length!==1?"s":""}</div>''',
     '''          <div className="text-emerald-200 text-xs mt-1">{sorted.length} session{sorted.length!==1?"s":""}{hundiShown.length ? " · "+hundiShown.length+" hundi count"+(hundiShown.length!==1?"s":"") : ""}</div>''')
swap('''<td className="py-2 font-medium text-slate-700">📱 SumUp</td>''', '''<td className="py-2 font-medium text-slate-700">💳 Card</td>''')
# Balance sheet: hundi counts are their own dated rows among the sessions
swap('''          <span className="text-xs text-slate-400">{sorted.length} sessions</span>''',
     '''          <span className="text-xs text-slate-400">{sorted.length} sessions{hundiShown.length ? " · "+hundiShown.length+" hundi counts" : ""}</span>''')
swap('''              {sorted.map(function(s){
                var arch = parseFloat((s.archanaTickets&&s.archanaTickets.amount)||0);''',
     '''              {sorted.map(function(s){ return { kind:"sheet", date:s.date, s:s }; })
                .concat(hundiShown.map(function(h){ return { kind:"hundi", date:h.date+"T12:00:00", h:h }; }))
                .sort(function(a,b){ return new Date(a.date)-new Date(b.date); })
                .map(function(row){
                if (row.kind==="hundi") {
                  var amt = parseFloat(row.h.amount||0);
                  running += amt;
                  var snap = running;
                  return (
                    <tr key={"h"+row.h.id} className="border-b border-slate-50 bg-emerald-50 bg-opacity-50">
                      <td className="px-4 py-2 font-medium text-slate-700 whitespace-nowrap">{new Date(row.date).toLocaleDateString("en-GB",{day:"numeric",month:"short",year:"2-digit"})}</td>
                      <td className="px-4 py-2 text-emerald-700 whitespace-nowrap hidden md:table-cell">🏺 Hundi count</td>
                      <td className="px-3 py-2 text-right text-slate-300">—</td>
                      <td className="px-3 py-2 text-right text-slate-300 hidden md:table-cell">—</td>
                      <td className="px-3 py-2 text-right text-slate-600 whitespace-nowrap hidden md:table-cell">{fmt(amt)}</td>
                      <td className="px-3 py-2 text-right font-semibold text-emerald-700 whitespace-nowrap">{fmt(amt)}</td>
                      <td className="px-3 py-2 text-right text-slate-300">—</td>
                      <td className="px-3 py-2 text-right font-semibold text-indigo-600 whitespace-nowrap">{fmt(amt)}</td>
                      <td className={"px-4 py-2 text-right font-black whitespace-nowrap "+(snap>=0?"text-slate-800":"text-red-600")}>{fmt(snap)}</td>
                    </tr>
                  );
                }
                var s = row.s;
                var arch = parseFloat((s.archanaTickets&&s.archanaTickets.amount)||0);''')

# ── Rota Sheet: no Hundi entry (phone card, laptop row) ───────────────────────
cut('''      {/* Hundi */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 flex items-center gap-3">''', '''      {/* Denomination table */}''')
cut('''              {/* Hundi row */}''', '''              {/* Expected Cash in Hand footer */}''')
swap('''Opening + cash income (Archana + Donation + Hundi) − expenses · must match closing balance →''',
     '''Opening + cash income (Archana + Donations) − cash expenses · must match closing balance →''')
# Reconciliation shows a Hundi line only for older sheets that recorded one
swap('''                      <div className="flex justify-between text-slate-500"><span>Hundi</span><span>£{hundiAmt.toFixed(2)}</span></div>''',
     '''                      {hundiAmt > 0 && <div className="flex justify-between text-slate-500"><span>Hundi</span><span>£{hundiAmt.toFixed(2)}</span></div>}''')
# Printout: Hundi row and wording only when an older sheet has one
swap('''    + "<tr><td><b>Hundi</b></td><td>—</td><td class='n'>—</td><td class='n'>" + gbp(hundi) + "</td><td class='n'>£0.00</td><td class='n'>£0.00</td><td class='n'><b>" + gbp(hundi) + "</b></td></tr>"''',
     '''    + (hundi > 0 ? "<tr><td><b>Hundi</b></td><td>—</td><td class='n'>—</td><td class='n'>" + gbp(hundi) + "</td><td class='n'>£0.00</td><td class='n'>£0.00</td><td class='n'><b>" + gbp(hundi) + "</b></td></tr>" : "")''')
swap('''    + "<tr><td>+ Cash in (Archana, Donations, Hundi)</td><td class='n'>"''',
     '''    + "<tr><td>+ Cash in (Archana, Donations" + (hundi > 0 ? ", Hundi" : "") + ")</td><td class='n'>"''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
