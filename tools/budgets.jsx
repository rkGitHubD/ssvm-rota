// ─── A printable report: one bordered table, laid out page by page ───────────
// rows: [{ cells:[html…], cls }]; head: [[label, width %, "r"|"c"|""]]. Cells don't wrap,
// so every row is the same height and each page ends cleanly with its own border.
function printTableReport({ title, subtitle, config = {}, head, rows, stats = [], note = "", fileTitle }) {
  const esc = v => String(v == null ? "" : v).replace(/[&<>"']/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c]));
  const FIRST = stats.length ? 34 : 38, REST = 40;
  const pages = [];
  for (let i = 0; i < rows.length || pages.length === 0; ) { const n = pages.length === 0 ? FIRST : REST; pages.push(rows.slice(i, i + n)); i += n; }
  const org = esc(config.fullName || config.orgName || "");
  const thead = "<thead><tr>" + head.map(([l, w, a]) => "<th class='" + (a||"") + "' style='width:" + w + "%'>" + esc(l) + "</th>").join("") + "</tr></thead>";
  const row = r => "<tr class='" + (r.cls||"") + "'>" + r.cells.map((c, i) => "<td class='" + (head[i][2]||"") + "'>" + (c == null ? "" : c) + "</td>").join("") + "</tr>";
  let h = "<!DOCTYPE html><html><head><meta charset='utf-8'/><title>" + esc(fileTitle || title) + "</title><style>"
    + "@page{size:A4;margin:12mm}*{box-sizing:border-box;margin:0;padding:0}"
    + "body{font-family:Arial,Helvetica,sans-serif;color:#0f172a;background:#e2e8f0}"
    + ".page{width:186mm;padding-top:4mm;background:#fff;page-break-after:always;break-after:page;break-inside:avoid}.page:last-child{page-break-after:auto;break-after:auto}"
    + ".hd{display:flex;align-items:center;gap:10px;border-bottom:2px solid #1e1b4b;padding-bottom:3mm;margin-bottom:4mm}.hd img{height:12mm;width:12mm;object-fit:contain}"
    + ".org{font-size:16px;font-weight:900;color:#1e1b4b}.sub{font-size:10.5px;color:#334155}.cont{font-size:11px;font-weight:bold;color:#1e1b4b;margin-bottom:3mm}"
    + ".stats{display:flex;gap:3mm;margin-bottom:4mm}.stats div{flex:1;border:1px solid #cbd5e1;border-radius:3px;padding:1.5mm 2.5mm}.stats b{display:block;font-size:13px}.stats span{font-size:9px;color:#475569}"
    + "table{width:100%;table-layout:fixed;border-collapse:collapse;border:2px solid #0f172a}"
    + "th,td{border:1px solid #1e293b;height:5.6mm;padding:0 1.6mm;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:9.5px;text-align:left}"
    + "th{background:#1e1b4b;color:#fff;height:7mm}.r{text-align:right}.c{text-align:center}"
    + "tr.grp td{background:#e0e7ff;font-weight:bold}tr.tot td{background:#f1f5f9;font-weight:bold}tr.sub td{color:#475569}"
    + ".short{color:#b91c1c;font-weight:bold}.over{color:#15803d;font-weight:bold}"
    + ".note{margin-top:3mm;font-size:9.5px;color:#334155}"
    + ".foot{display:flex;justify-content:space-between;font-size:9.5px;color:#334155;border-top:1px solid #94a3b8;padding-top:2mm;margin-top:4mm}"
    + "@media screen{body{padding:8mm 0}.page{margin:0 auto 8mm;padding:12mm;width:210mm;box-shadow:0 1px 4px #0003}}@media print{body{background:#fff}.noprint{display:none!important}}"
    + "</style></head><body>";
  pages.forEach((pg, i) => {
    h += "<div class='page'>";
    if (i === 0) h += "<div class='hd'>" + (config.logo ? "<img src='" + config.logo + "'/>" : "") + "<div><div class='org'>" + org + "</div><div class='sub'>" + esc(title) + (subtitle ? " · " + esc(subtitle) : "") + "</div></div></div>"
      + (stats.length ? "<div class='stats'>" + stats.map(([l, v]) => "<div><span>" + esc(l) + "</span><b>" + v + "</b></div>").join("") + "</div>" : "");
    else h += "<div class='cont'>" + org + " — " + esc(title) + " (continued)</div>";
    h += "<table>" + thead + "<tbody>" + (pg.map(row).join("") || "<tr><td colspan='" + head.length + "' class='c'>Nothing to show</td></tr>") + "</tbody></table>";
    if (i === pages.length - 1 && note) h += "<div class='note'>" + note + "</div>";
    h += "<div class='foot'><span>Printed " + new Date().toLocaleDateString("en-GB", { day:"numeric", month:"short", year:"numeric" }) + "</span><span>Page " + (i + 1) + " of " + pages.length + "</span></div></div>";
  });
  h += "<button class='noprint' onclick='window.print()' style='position:fixed;bottom:16px;right:16px;background:#3730a3;color:#fff;border:0;padding:8px 20px;border-radius:8px;font-size:12px;font-weight:bold;cursor:pointer'>Print / Save as PDF</button>"
    + "<script>window.onload=function(){setTimeout(function(){window.print();},300);};<\/script></body></html>";
  const w = window.open("", "_blank");
  if (!w) return false;
  w.document.write(h); w.document.close();
  return true;
}
const escHtml = v => String(v == null ? "" : v).replace(/[&<>"']/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c]));

// ─── Budgets ─────────────────────────────────────────────────────────────────
// budgets = [{ id, kind:"yearly"|"occasion", year, name, specialKey?, date?, notes,
//   lines:[{ id, cat, label, qty, unit, rate }] }]. A line costs qty × rate.
// Sponsorships count towards budgets through budgetLinks:[{ budgetId, amount }] on the record.
const BUDGET_LINE_KINDS = [
  { cat:"Hall rent",        unit:"hours",     rate:"£ per hour" },
  { cat:"Priest",           unit:"functions", rate:"£ per function" },
  { cat:"Running expenses", unit:"months",    rate:"£ per month" },
  { cat:"Other",            unit:"items",     rate:"£ each" },
];
const unitOf = (k, q) => parseFloat(q) === 1 ? k.unit.replace(/s$/, "") : k.unit;
const lineCost = l => (parseFloat(l.qty) || 0) * (parseFloat(l.rate) || 0);
const budgetCost = b => (b.lines || []).reduce((t, l) => t + lineCost(l), 0);
const gbp2 = n => "£" + (n || 0).toFixed(2);
const budgetLabel = b => b.name.includes(String(b.year)) ? b.name : b.name + " " + b.year;
// Every sponsorship amount that counts towards each budget
function budgetFunding(sponsorships = []) {
  const by = {};
  sponsorships.forEach(a => (a.donations || []).forEach(d => (d.budgetLinks || []).forEach(l => {
    const amt = parseFloat(l.amount) || 0;
    if (!amt) return;
    (by[l.budgetId] = by[l.budgetId] || { total:0, rows:[] });
    by[l.budgetId].total += amt;
    by[l.budgetId].rows.push({ donor:d.donor, item:a.name, amount:amt, first:(d.rotaDates || []).slice().sort()[0] || d.startDate || "" });
  })));
  return by;
}
// Short by / covered, for a budget and what's come in for it
const gapText = (cost, got) => got >= cost ? (got > cost ? gbp2(got - cost) + " over" : "Fully covered") : gbp2(cost - got) + " short";

function BudgetForm({ initial, budgets, specials = [], onSave, onCancel, showToast }) {
  const [f, setF] = useState(initial);
  const ic = "w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-300";
  const lbl = "text-xs font-semibold text-slate-600";
  const yr = parseInt(f.year) || new Date().getFullYear();
  const occasions = specials.filter(sp => new Date(sp.date).getFullYear() === yr).sort((a, b) => new Date(a.date) - new Date(b.date));
  const lastYear = budgets.find(b => b.kind === "yearly" && b.year === yr - 1);
  const setLine = (id, k, v) => setF(p => ({ ...p, lines: p.lines.map(l => l.id === id ? { ...l, [k]: v } : l) }));
  const addLine = k => setF(p => ({ ...p, lines: [...p.lines, { id:uid(), cat:k.cat, label:"", qty:"", unit:k.unit, rate:"" }] }));
  const pickOccasion = key => {
    const sp = specials.find(x => x.key === key);
    setF(sp ? { ...f, specialKey:key, name:sp.label || sp.tag || "", date:new Date(sp.date).toISOString().slice(0, 10) } : { ...f, specialKey:"" });
  };
  const save = () => {
    if (!f.name.trim()) return showToast(f.kind === "yearly" ? "Enter a name" : "Choose or type the festival / occasion","error");
    if (f.kind === "yearly" && budgets.some(b => b.kind === "yearly" && b.year === yr && b.id !== f.id)) return showToast("There's already a yearly budget for " + yr,"error");
    const lines = f.lines.filter(l => l.label.trim() || lineCost(l) > 0);
    if (!lines.length) return showToast("Add at least one budget line","error");
    onSave({ ...f, year: yr, name: f.name.trim(), lines });
  };
  const total = budgetCost(f);
  return (
    <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 space-y-3">
      <div className="grid sm:grid-cols-3 gap-3">
        <label className={lbl}>Budget for
          <select value={f.kind} onChange={e=>setF({ ...f, kind:e.target.value, name: e.target.value === "yearly" ? "Temple running costs" : "", specialKey:"", date:"" })} className={ic}>
            <option value="yearly">The whole year (temple)</option><option value="occasion">A festival / special occasion</option>
          </select></label>
        <label className={lbl}>Year<input type="number" min="2020" max="2100" value={f.year} onChange={e=>setF({ ...f, year:e.target.value })} className={ic}/></label>
        {f.kind === "occasion" && occasions.length > 0
          ? <label className={lbl}>Occasion *
              <select value={f.specialKey || ""} onChange={e=>pickOccasion(e.target.value)} className={ic}>
                <option value="">Type a name instead…</option>
                {occasions.map(sp => <option key={sp.key} value={sp.key}>{sp.label || sp.tag} — {new Date(sp.date).toLocaleDateString("en-GB",{ day:"numeric", month:"short" })}</option>)}
              </select></label>
          : <div/>}
        <label className={lbl + " sm:col-span-2"}>Name *<input value={f.name} onChange={e=>setF({ ...f, name:e.target.value })} placeholder={f.kind === "yearly" ? "Temple running costs" : "e.g. Diwali"} className={ic}/></label>
        {f.kind === "occasion" && <label className={lbl}>Date<input type="date" value={f.date || ""} onChange={e=>setF({ ...f, date:e.target.value })} className={ic}/></label>}
      </div>

      <div className="bg-white rounded-lg border border-indigo-100 p-2 space-y-2">
        <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">What it costs</div>
        {f.lines.length === 0 && <p className="text-xs text-slate-400">Add the costs below — e.g. hall rent for so many hours, the priest per function, running costs per month.</p>}
        {f.lines.map(l => {
          const k = BUDGET_LINE_KINDS.find(x => x.cat === l.cat) || BUDGET_LINE_KINDS[3];
          return (
            <div key={l.id} className="grid grid-cols-12 gap-1.5 items-end">
              <label className={lbl + " col-span-12 sm:col-span-4"}>{l.cat}<input value={l.label} onChange={e=>setLine(l.id, "label", e.target.value)} placeholder={l.cat === "Hall rent" ? "e.g. Community hall" : l.cat === "Priest" ? "e.g. Priest fee" : l.cat === "Running expenses" ? "e.g. Electricity" : "What for"} className={ic}/></label>
              <label className={lbl + " col-span-4 sm:col-span-2"}>{k.unit.charAt(0).toUpperCase() + k.unit.slice(1)}<input type="number" min="0" step="any" value={l.qty} onChange={e=>setLine(l.id, "qty", e.target.value)} className={ic}/></label>
              <label className={lbl + " col-span-4 sm:col-span-2"}>{k.rate}<input type="number" min="0" step="0.01" value={l.rate} onChange={e=>setLine(l.id, "rate", e.target.value)} className={ic}/></label>
              <div className="col-span-3 sm:col-span-3 text-right text-sm font-bold text-slate-700 pb-2">{gbp2(lineCost(l))}</div>
              <button onClick={()=>setF({ ...f, lines: f.lines.filter(x => x.id !== l.id) })} className="col-span-1 text-red-400 hover:text-red-600 font-bold pb-2" title="Remove line">×</button>
            </div>
          );
        })}
        <div className="flex gap-1.5 flex-wrap pt-1">
          {BUDGET_LINE_KINDS.map(k => <button key={k.cat} onClick={()=>addLine(k)} className="text-xs bg-indigo-100 hover:bg-indigo-200 text-indigo-700 px-2.5 py-1 rounded-lg font-semibold">+ {k.cat}</button>)}
          {f.kind === "yearly" && lastYear && !f.lines.length && <button onClick={()=>setF({ ...f, lines: lastYear.lines.map(l => ({ ...l, id:uid() })) })} className="text-xs bg-white border border-indigo-200 text-indigo-700 px-2.5 py-1 rounded-lg font-semibold">Copy {yr - 1}'s lines</button>}
          <span className="ml-auto text-sm font-black text-slate-800">Total {gbp2(total)}</span>
        </div>
      </div>
      <label className={lbl + " block"}>Notes<input value={f.notes || ""} onChange={e=>setF({ ...f, notes:e.target.value })} placeholder="Optional" className={ic}/></label>
      <div className="flex gap-2">
        <button onClick={save} className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg py-2 text-sm font-bold">{initial.id ? "Save changes" : "Add budget"}</button>
        <button onClick={onCancel} className="flex-1 bg-white border border-slate-200 text-slate-600 rounded-lg py-2 text-sm font-medium">Cancel</button>
      </div>
    </div>
  );
}

function BudgetsPanel({ budgets = [], upBudgets, sponsorships = [], upSponsorships, specials = [], rotaSheets = [], hundi = [], config = {}, showToast }) {
  const thisYear = new Date().getFullYear();
  const years = [...new Set([thisYear, thisYear + 1, ...budgets.map(b => b.year)])].sort();
  const [year, setYear] = useState(thisYear);
  const [form, setForm] = useState(null);
  const [open, setOpen] = useState(null);
  const [delId, setDelId] = useState(null);
  const funding = budgetFunding(sponsorships);
  const list = budgets.filter(b => b.year === year).sort((a, b) => a.kind === b.kind ? (a.date || "").localeCompare(b.date || "") : a.kind === "yearly" ? -1 : 1);
  const cost = list.reduce((t, b) => t + budgetCost(b), 0);
  const got = list.reduce((t, b) => t + ((funding[b.id] || {}).total || 0), 0);
  // Other money in this year (closed Rota Sheets and hundi counts), for context
  const yearOf = d => String(d || "").slice(0, 4) === String(year);
  const otherIncome = rotaSheets.filter(s => s.status === "closed" && yearOf(new Date(s.date).toISOString()))
    .reduce((t, s) => t + parseFloat((s.archanaTickets || {}).amount || 0) + parseFloat((s.donationBook || {}).amount || 0) + parseFloat((s.hundi || {}).amount || 0), 0)
    + hundi.filter(h => yearOf(h.date)).reduce((t, h) => t + parseFloat(h.amount || 0), 0);

  const save = b => {
    upBudgets(b.id ? budgets.map(x => x.id === b.id ? b : x) : [...budgets, { ...b, id:uid() }]);
    setForm(null); setYear(b.year); showToast(b.id ? "Budget updated" : "Budget added");
  };
  const remove = b => {
    upBudgets(budgets.filter(x => x.id !== b.id));
    // the sponsorships that counted towards it no longer do
    if (sponsorships.some(a => (a.donations || []).some(d => (d.budgetLinks || []).some(l => l.budgetId === b.id))))
      upSponsorships(sponsorships.map(a => ({ ...a, donations:(a.donations || []).map(d => d.budgetLinks ? { ...d, budgetLinks:d.budgetLinks.filter(l => l.budgetId !== b.id) } : d) })));
    setDelId(null); showToast("Budget removed");
  };
  const pdf = () => {
    const rows = [];
    list.forEach(b => {
      const c = budgetCost(b), g = (funding[b.id] || {}).total || 0;
      rows.push({ cls:"grp", cells:[escHtml(budgetLabel(b)) + (b.date ? " · " + shortDay(b.date) : ""), b.kind === "yearly" ? "Yearly" : "Occasion", "", "", gbp2(c)] });
      (b.lines || []).forEach(l => { const k = BUDGET_LINE_KINDS.find(x => x.cat === l.cat) || BUDGET_LINE_KINDS[3];
        rows.push({ cls:"sub", cells:["&nbsp;&nbsp;" + escHtml(l.cat + (l.label ? " — " + l.label : "")), "", (parseFloat(l.qty) || 0) + " " + unitOf(k, l.qty), gbp2(parseFloat(l.rate) || 0), gbp2(lineCost(l))] }); });
      ((funding[b.id] || {}).rows || []).forEach(r => rows.push({ cls:"sub", cells:["&nbsp;&nbsp;Sponsor: " + escHtml(r.donor) + " (" + escHtml(r.item) + ")", "", "", "", "−" + gbp2(r.amount)] }));
      rows.push({ cls:"tot", cells:["&nbsp;&nbsp;Sponsored " + gbp2(g), "", "", "Difference", "<span class='" + (g >= c ? "over" : "short") + "'>" + gapText(c, g) + "</span>"] });
    });
    if (!printTableReport({ title:"Budget " + year, config, fileTitle:"Budget " + year,
      head:[["Budget / item", 52], ["Type", 12], ["Quantity", 12, "r"], ["Rate", 11, "r"], ["£", 13, "r"]], rows,
      stats:[["Budgeted", gbp2(cost)], ["Sponsored", gbp2(got)], ["Difference", "<span class='" + (got >= cost ? "over" : "short") + "'>" + gapText(cost, got) + "</span>"], ["Other income " + year + " so far", gbp2(otherIncome)]],
      note:"Sponsored = sponsorship money linked to each budget. Other income (Rota Sheets and hundi) is shown for reference and is not counted against the budgets." })) showToast("Allow pop-ups to print","error");
  };
  const bar = (c, g) => <div className="h-2 bg-slate-100 rounded-full overflow-hidden"><div className={"h-full " + (g >= c ? "bg-emerald-500" : "bg-amber-500")} style={{ width: (c > 0 ? Math.min(100, g / c * 100) : 100) + "%" }}/></div>;

  return (
    <div className="bg-white rounded-2xl border border-indigo-200 shadow-sm p-5 space-y-3">
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex-1 min-w-[12rem]">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">📒 Budgets</h3>
          <p className="text-xs text-slate-400 mt-0.5">A yearly budget for the temple and one for each festival. Link sponsorships to them to see what's covered and what's still needed.</p>
        </div>
        <select value={year} onChange={e=>{ setYear(parseInt(e.target.value)); setOpen(null); }} className="border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white">{years.map(y => <option key={y} value={y}>{y}</option>)}</select>
        {list.length > 0 && <button onClick={pdf} className="text-xs bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 px-3 py-2 rounded-xl font-bold">🖨 PDF</button>}
        {!form && <button onClick={()=>setForm({ kind: list.some(b => b.kind === "yearly") ? "occasion" : "yearly", year, name: list.some(b => b.kind === "yearly") ? "" : "Temple running costs", lines:[], notes:"" })}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded-xl text-xs font-bold">+ New budget</button>}
      </div>
      {form && <BudgetForm key={form.id || "new"} initial={form} budgets={budgets} specials={specials} onSave={save} onCancel={()=>setForm(null)} showToast={showToast}/>}

      {list.length === 0 ? <p className="text-sm text-slate-400">No budgets for {year} yet.</p> : (<>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <div className="bg-slate-50 rounded-xl p-3"><div className="text-xs text-slate-500">Budgeted {year}</div><div className="text-lg font-black text-slate-800">{gbp2(cost)}</div></div>
          <div className="bg-slate-50 rounded-xl p-3"><div className="text-xs text-slate-500">Sponsored</div><div className="text-lg font-black text-indigo-700">{gbp2(got)}</div></div>
          <div className={"rounded-xl p-3 " + (got >= cost ? "bg-emerald-50" : "bg-red-50")}><div className="text-xs text-slate-500">Difference</div><div className={"text-lg font-black " + (got >= cost ? "text-emerald-700" : "text-red-700")}>{gapText(cost, got)}</div></div>
          <div className="bg-slate-50 rounded-xl p-3" title="Closed Rota Sheets and hundi counts — not counted against the budgets"><div className="text-xs text-slate-500">Other income so far</div><div className="text-lg font-black text-slate-600">{gbp2(otherIncome)}</div></div>
        </div>
        <div className="divide-y divide-slate-100">
          {list.map(b => {
            const c = budgetCost(b), fd = funding[b.id] || { total:0, rows:[] }, g = fd.total;
            return (
              <div key={b.id} className="py-3 space-y-1.5">
                <div className="flex items-center gap-2 flex-wrap text-sm">
                  <span className={"text-xs font-semibold px-2 py-0.5 rounded-full " + (b.kind === "yearly" ? "bg-indigo-100 text-indigo-700" : "bg-amber-100 text-amber-800")}>{b.kind === "yearly" ? "Yearly" : "★ Occasion"}</span>
                  <span className="font-bold text-slate-800">{b.name}</span>
                  {b.date && <span className="text-xs text-slate-400">{shortDay(b.date)}</span>}
                  <span className="ml-auto text-xs text-slate-500">{gbp2(g)} of {gbp2(c)}</span>
                  <span className={"text-xs font-bold " + (g >= c ? "text-emerald-700" : "text-red-600")}>{gapText(c, g)}</span>
                </div>
                {bar(c, g)}
                <div className="flex gap-3 text-xs">
                  <button onClick={()=>setOpen(open === b.id ? null : b.id)} className="text-indigo-600 font-semibold">{open === b.id ? "Hide details" : "Details"}</button>
                  <button onClick={()=>setForm(b)} className="text-indigo-600">Edit</button>
                  {delId === b.id
                    ? <><button onClick={()=>remove(b)} className="bg-red-600 text-white px-2 rounded">Remove</button><button onClick={()=>setDelId(null)} className="text-slate-500">Keep</button></>
                    : <button onClick={()=>setDelId(b.id)} className="text-red-500">Remove</button>}
                </div>
                {open === b.id && (
                  <div className="grid md:grid-cols-2 gap-3 pt-1">
                    <table className="w-full text-xs"><thead><tr className="text-slate-500 border-b border-slate-100"><th className="text-left py-1">Cost</th><th className="text-right">Qty × rate</th><th className="text-right">£</th></tr></thead>
                      <tbody>{(b.lines || []).map(l => { const k = BUDGET_LINE_KINDS.find(x => x.cat === l.cat) || BUDGET_LINE_KINDS[3];
                        return <tr key={l.id} className="border-b border-slate-50"><td className="py-1">{l.cat}{l.label ? " — " + l.label : ""}</td><td className="text-right whitespace-nowrap">{(parseFloat(l.qty) || 0)} {unitOf(k, l.qty)} × {gbp2(parseFloat(l.rate) || 0)}</td><td className="text-right font-semibold">{gbp2(lineCost(l))}</td></tr>; })}</tbody></table>
                    <table className="w-full text-xs"><thead><tr className="text-slate-500 border-b border-slate-100"><th className="text-left py-1">Sponsored by</th><th className="text-left">Item</th><th className="text-right">£</th></tr></thead>
                      <tbody>{fd.rows.length === 0 ? <tr><td colSpan="3" className="py-1 text-slate-400">No sponsorships linked yet — link them from Temple Admin → Sponsorships.</td></tr>
                        : fd.rows.map((r, i) => <tr key={i} className="border-b border-slate-50"><td className="py-1">{r.donor}</td><td>{r.item}</td><td className="text-right font-semibold">{gbp2(r.amount)}</td></tr>)}</tbody></table>
                    {b.notes && <p className="text-xs text-slate-500 md:col-span-2">{b.notes}</p>}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </>)}
    </div>
  );
}

