"""Budgets in Finance (yearly temple budget + festival budgets, built from cost lines),
sponsorships linked to budgets with an amount each, and PDFs of the filtered
sponsorship list, the item report and the year's budgets.
New key rota-budgets (admin only).

Usage: python3 tools/budgets-patch.py Index.html
"""
import os
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()
new = open(os.path.join(os.path.dirname(__file__), "budgets.jsx"), encoding="utf-8").read()


def swap(old, rep, n=1):
    global s
    assert s.count(old) == n, (s.count(old), old[:80])
    s = s.replace(old, rep)


# ── App state, load, save, backup ──
swap('''  const [hundi,         setHundi]         = useState([]);''',
     '''  const [hundi,         setHundi]         = useState([]);
  const [budgets,       setBudgets]       = useState([]);''')
swap('''  const upHundi        = v => { setHundi(v);        DB.set("rota-hundi",        v); };''',
     '''  const upHundi        = v => { setHundi(v);        DB.set("rota-hundi",        v); };
  const upBudgets      = v => { setBudgets(v);      DB.set("rota-budgets",      v); };''')
swap('''    setHundi(LS.get("rota-hundi", []));''',
     '''    setHundi(LS.get("rota-hundi", []));
    setBudgets(LS.get("rota-budgets", []));''')
swap('''        setHundi(g("rota-hundi", []));''',
     '''        setHundi(g("rota-hundi", []));
        setBudgets(g("rota-budgets", []));''')
swap('''priests={priests} upPriests={upPriests} hundi={hundi} upHundi={upHundi}/>}''',
     '''priests={priests} upPriests={upPriests} hundi={hundi} upHundi={upHundi} budgets={budgets} upBudgets={upBudgets}/>}''')
swap('''itineraries,prasadham,priests,hundi}}/>}''', '''itineraries,prasadham,priests,hundi,budgets}}/>}''')
swap('''    "rota-hundi":        allData.hundi,''', '''    "rota-hundi":        allData.hundi,
    "rota-budgets":      allData.budgets,''')

# ── Master Data wiring ──
swap('''priests, upPriests, hundi=[], upHundi }) {''', '''priests, upPriests, hundi=[], upHundi, budgets=[], upBudgets }) {''')
swap('''<MDFinance      rotaSheets={rotaSheets} hundi={hundi} upHundi={upHundi} showToast={showToast} generalOffers={generalOffers}/>''',
     '''<MDFinance      rotaSheets={rotaSheets} hundi={hundi} upHundi={upHundi} showToast={showToast} generalOffers={generalOffers} budgets={budgets} upBudgets={upBudgets} sponsorships={sponsorships} upSponsorships={upSponsorships} specials={specials} config={config}/>''')
swap('''<MDSponsorships sponsorships={sponsorships} upSponsorships={upSponsorships} showToast={showToast} sevas={sevas}/>''',
     '''<MDSponsorships sponsorships={sponsorships} upSponsorships={upSponsorships} showToast={showToast} sevas={sevas} budgets={budgets} config={config}/>''')

# ── Finance: the budgets panel at the top ──
swap('''// ── MD: Finance ───────────────────────────────────────────────────────────────''',
     new + '''// ── MD: Finance ───────────────────────────────────────────────────────────────''')
swap('''function MDFinance({ rotaSheets=[], hundi=[], upHundi, showToast, generalOffers=[] }) {''',
     '''function MDFinance({ rotaSheets=[], hundi=[], upHundi, showToast, generalOffers=[], budgets=[], upBudgets, sponsorships=[], upSponsorships, specials=[], config={} }) {''')
swap('''  var hundiPanel = <HundiCollections hundi={hundi} upHundi={upHundi} showToast={showToast} shown={hundiShown}/>;''',
     '''  var hundiPanel = <HundiCollections hundi={hundi} upHundi={upHundi} showToast={showToast} shown={hundiShown}/>;
  var budgetPanel = <BudgetsPanel budgets={budgets} upBudgets={upBudgets} sponsorships={sponsorships} upSponsorships={upSponsorships} specials={specials} rotaSheets={rotaSheets} hundi={hundi} config={config} showToast={showToast}/>;''')
swap('''    <div className="space-y-5">
      {hundiPanel}
      <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">''',
     '''    <div className="space-y-5">
      {budgetPanel}
      {hundiPanel}
      <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">''')
swap('''    <div className="space-y-5">

      {/* Month filter */}''', '''    <div className="space-y-5">
      {budgetPanel}

      {/* Month filter */}''')

# ── Sponsorship form: count towards budgets ──
swap('''function SponsorshipForm({ initial, items, sevas, onSave, onCancel, showToast }) {''',
     '''function SponsorshipForm({ initial, items, sevas, budgets = [], onSave, onCancel, showToast }) {''')
swap('''  const dates = sponsorDates(f);
  const save = () => {''', '''  const dates = sponsorDates(f);
  // Budgets for the years this sponsorship covers (and any it's already linked to)
  const links = f.budgetLinks || [];
  const yrs = dates.length ? dates.map(d => parseInt(d.slice(0, 4))) : [new Date().getFullYear()];
  const budgetChoices = budgets.filter(b => yrs.includes(b.year) || links.some(l => l.budgetId === b.id))
    .sort((a, b) => a.year - b.year || (a.kind === b.kind ? (a.date || "").localeCompare(b.date || "") : a.kind === "yearly" ? -1 : 1));
  const linked = links.reduce((t, l) => t + (parseFloat(l.amount) || 0), 0);
  const toggleLink = b => setF({ ...f, budgetLinks: links.some(l => l.budgetId === b.id) ? links.filter(l => l.budgetId !== b.id)
    : [...links, { budgetId: b.id, amount: Math.max(0, (parseFloat(f.amount) || 0) - linked).toFixed(2) }] });
  const save = () => {''')
swap('''    if (!dates.length) return showToast(f.frequency === "one-off" ? "Add at least one date" : "Choose a start date","error");
    onSave({ ...f, amount: parseFloat(f.amount).toFixed(2), rotaDates: dates });''',
     '''    if (!dates.length) return showToast(f.frequency === "one-off" ? "Add at least one date" : "Choose a start date","error");
    if (links.some(l => !(parseFloat(l.amount) > 0))) return showToast("Enter how much counts towards each budget ticked","error");
    if (linked > parseFloat(f.amount) + 0.005) return showToast("The budget amounts add up to more than was paid","error");
    onSave({ ...f, amount: parseFloat(f.amount).toFixed(2), rotaDates: dates, budgetLinks: links.map(l => ({ budgetId: l.budgetId, amount: parseFloat(l.amount).toFixed(2) })) });''')
swap('''      <label className={lbl+" sm:col-span-2"}>Notes<input value={f.notes||""} onChange={e=>setF({...f,notes:e.target.value})} placeholder="Optional" className={ic}/></label>''',
     '''      {budgetChoices.length > 0 && (
        <div className="sm:col-span-2 bg-white border border-indigo-100 rounded-lg p-2 space-y-1">
          <div className={lbl}>📒 Counts towards a budget <span className="font-normal text-slate-400">(optional — the yearly budget and/or a festival)</span></div>
          {budgetChoices.map(b => { const l = links.find(x => x.budgetId === b.id); return (
            <div key={b.id} className="flex items-center gap-2 text-sm">
              <label className="flex items-center gap-1.5 flex-1 min-w-0"><input type="checkbox" checked={!!l} onChange={()=>toggleLink(b)}/>
                <span className="truncate">{b.kind === "yearly" ? "Yearly" : "★"} {budgetLabel(b)}{b.date ? " · " + shortDay(b.date) : ""}</span></label>
              {l && <span className="flex items-center gap-1 text-xs text-slate-500">£<input type="number" min="0" step="0.01" value={l.amount}
                onChange={e=>setF({ ...f, budgetLinks: links.map(x => x.budgetId === b.id ? { ...x, amount: e.target.value } : x) })} className="w-24 border border-slate-200 rounded-lg px-2 py-1 text-sm"/></span>}
            </div>); })}
          {links.length > 1 && <div className="text-xs text-slate-400">Split between budgets: £{linked.toFixed(2)} of £{(parseFloat(f.amount) || 0).toFixed(2)}</div>}
        </div>
      )}
      <label className={lbl+" sm:col-span-2"}>Notes<input value={f.notes||""} onChange={e=>setF({...f,notes:e.target.value})} placeholder="Optional" className={ic}/></label>''')

# ── Sponsorships list: budget filter + column, PDFs ──
swap('''function MDSponsorships({ sponsorships=[], upSponsorships, showToast, sevas=[] }) {
  const blank = { donor:"", contact:"", itemKey:"", newItem:"", amount:"", frequency:"one-off", rotaDates:[], startDate:"", endDate:"", customWeeks:"", notes:"" };''',
     '''function MDSponsorships({ sponsorships=[], upSponsorships, showToast, sevas=[], budgets=[], config={} }) {
  const blank = { donor:"", contact:"", itemKey:"", newItem:"", amount:"", frequency:"one-off", rotaDates:[], startDate:"", endDate:"", customWeeks:"", notes:"", budgetLinks:[] };
  const [budgetFilter, setBudgetFilter] = useState("");''')
swap('''  const shown = records.filter(r => (!itemFilter || r.areaId === itemFilter) && (!statusFilter || r.status === statusFilter)''',
     '''  const budgetNames = r => (r.budgetLinks || []).map(l => budgets.find(b => b.id === l.budgetId)).filter(Boolean).map(budgetLabel);
  const shown = records.filter(r => (!itemFilter || r.areaId === itemFilter) && (!statusFilter || r.status === statusFilter)
    && (!budgetFilter || (budgetFilter === "none" ? !budgetNames(r).length : (r.budgetLinks || []).some(l => l.budgetId === budgetFilter)))''')
swap('''  const ic = "border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white";
  const th = "text-left px-2 py-2 font-semibold text-slate-500 whitespace-nowrap";
''', '''  const ic = "border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white";
  const th = "text-left px-2 py-2 font-semibold text-slate-500 whitespace-nowrap";
  const sumPaid = rs => rs.reduce((t, r) => t + parseFloat(r.amount || 0), 0);
  const range = r => shortDay(r.first) + (r.dates.length > 1 ? " – " + shortDay(r.last) : "");
  const cap = x => x ? x.charAt(0).toUpperCase() + x.slice(1) : "";
  const popupBlocked = ok => { if (!ok) showToast("Allow pop-ups to print","error"); };
  const listPdf = () => {
    const what = [itemFilter && "Item: " + ((items.find(a => a.id === itemFilter) || {}).name || ""), statusFilter && "Status: " + statusFilter,
      budgetFilter && "Budget: " + (budgetFilter === "none" ? "not linked" : budgetLabel(budgets.find(b => b.id === budgetFilter) || { name:"" })), search && "Search: “" + search + "”"].filter(Boolean).join(" · ");
    popupBlocked(printTableReport({ title:"Sponsorships", subtitle: what || "All records", config, fileTitle:"Sponsorships",
      head:[["Donor",20],["Contact",15],["Item",13],["Paid £",9,"r"],["How often",10],["From – to",17],["Days",7,"c"],["Status",9]],
      rows: shown.map(r => ({ cells:[escHtml(r.donor), escHtml(r.contact || ""), escHtml(r.item), parseFloat(r.amount || 0).toFixed(2), cap(r.frequency), range(r), r.done + "/" + r.dates.length, r.status] }))
        .concat(shown.length ? [{ cls:"tot", cells:["Total", "", "", sumPaid(shown).toFixed(2), "", "", "", ""] }] : []),
      stats:[["Records", shown.length], ["Sponsors", new Set(shown.map(r => r.donor.toLowerCase())).size], ["Total paid", gbp2(sumPaid(shown))], ["Days still to come", shown.reduce((t, r) => t + r.dates.length - r.done, 0)]] }));
  };
  const reportPdf = () => {
    const rs = rep.slice().sort((x, y) => (x.first || "").localeCompare(y.first || ""));
    popupBlocked(printTableReport({ title:"Sponsors — " + repArea.name, subtitle:"Past, present and future", config, fileTitle:"Sponsors - " + repArea.name,
      head:[["Donor",22],["Paid £",10,"r"],["How often",11],["From – to",19],["Done",8,"c"],["To come",9,"c"],["Next",11],["Status",10]],
      rows: rs.map(r => ({ cells:[escHtml(r.donor), parseFloat(r.amount || 0).toFixed(2), cap(r.frequency), range(r), r.done, r.dates.length - r.done, shortDay(r.next), r.status] }))
        .concat(rs.length ? [{ cls:"tot", cells:["Total", sumPaid(rs).toFixed(2), "", "", rs.reduce((t, r) => t + r.done, 0), rs.reduce((t, r) => t + r.dates.length - r.done, 0), "", ""] }] : []),
      stats:[["Sponsors", new Set(rs.map(r => r.donor.toLowerCase())).size], ["Total paid", gbp2(sumPaid(rs))], ["Days covered", rs.reduce((t, r) => t + r.dates.length, 0)], ["Days still to come", rs.reduce((t, r) => t + r.dates.length - r.done, 0)]] }));
  };
''')
swap('''<SponsorshipForm key={form.id || "new"} initial={form} items={items} sevas={sevas} onSave''',
     '''<SponsorshipForm key={form.id || "new"} initial={form} items={items} sevas={sevas} budgets={budgets} onSave''')
swap('''          <select value={statusFilter} onChange={e=>setStatusFilter(e.target.value)} className={ic}><option value="">Any status</option>{["Upcoming","Active","Completed"].map(x => <option key={x}>{x}</option>)}</select>
        </div>''', '''          <select value={statusFilter} onChange={e=>setStatusFilter(e.target.value)} className={ic}><option value="">Any status</option>{["Upcoming","Active","Completed"].map(x => <option key={x}>{x}</option>)}</select>
          {budgets.length > 0 && <select value={budgetFilter} onChange={e=>setBudgetFilter(e.target.value)} className={ic}><option value="">Any budget</option><option value="none">Not linked</option>{budgets.slice().sort((a,b)=>b.year-a.year).map(b => <option key={b.id} value={b.id}>{budgetLabel(b)}</option>)}</select>}
          {shown.length > 0 && <button onClick={listPdf} className="text-xs bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 px-3 py-1.5 rounded-lg font-bold">🖨 PDF</button>}
        </div>''')
swap('''<table className="w-full text-sm min-w-[720px]">
              <thead><tr className="border-b border-slate-200 bg-slate-50"><th className={th}>Donor</th><th className={th}>Item</th>''',
     '''<table className="w-full text-sm min-w-[780px]">
              <thead><tr className="border-b border-slate-200 bg-slate-50"><th className={th}>Donor</th><th className={th}>Item</th>''')
swap('''                    <td className="px-2 py-2">{r.item}</td>''',
     '''                    <td className="px-2 py-2">{r.item}{budgetNames(r).length > 0 && <div className="text-xs text-indigo-500">📒 {budgetNames(r).join(", ")}</div>}</td>''')
swap('''          <select value={reportItem} onChange={e=>setReportItem(e.target.value)} className={ic}><option value="">Choose an item…</option>{items.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}</select>''',
     '''          <select value={reportItem} onChange={e=>setReportItem(e.target.value)} className={ic}><option value="">Choose an item…</option>{items.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}</select>
          {repArea && rep.length > 0 && <button onClick={reportPdf} className="text-xs bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 px-3 py-1.5 rounded-lg font-bold">🖨 PDF</button>}''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
