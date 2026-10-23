"""Special Occasions: upload from an Excel (.xlsx/.xls) or CSV file, with a template,
a preview and duplicate checks before anything is added.

Usage: python3 tools/specials-upload-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def swap(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


HELPERS = r'''// ─── Reading special occasions from a spreadsheet ────────────────────────────
// The spreadsheet library is only loaded when someone uploads or downloads a file.
let xlsxLoading = null;
const loadXLSX = () => window.XLSX ? Promise.resolve(window.XLSX) : (xlsxLoading = xlsxLoading || new Promise((ok, fail) => {
  const el = document.createElement("script");
  el.src = "https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js";
  el.onload = () => ok(window.XLSX);
  el.onerror = () => { xlsxLoading = null; fail(new Error("Couldn't load the spreadsheet reader — check the internet connection")); };
  document.head.appendChild(el);
}));
// A date cell as YYYY-MM-DD: Excel dates, 25/12/2027, 25-12-2027, 2027-12-25 or "25 Dec 2027"
function sheetDate(v) {
  const iso = d => d.getFullYear()+"-"+String(d.getMonth()+1).padStart(2,"0")+"-"+String(d.getDate()).padStart(2,"0");
  if (v instanceof Date && !isNaN(v)) return iso(v);
  if (typeof v === "number" && v > 20000 && v < 80000) return iso(new Date(Math.round((v - 25569) * 86400000) + 43200000));
  const t = String(v == null ? "" : v).trim(); if (!t) return "";
  let m = t.match(/^(\d{4})-(\d{1,2})-(\d{1,2})/);
  if (m) return iso(new Date(+m[1], +m[2]-1, +m[3]));
  m = t.match(/^(\d{1,2})[\/.\-](\d{1,2})[\/.\-](\d{2,4})$/);            // UK order: day first
  if (m) { const y = +m[3] < 100 ? 2000 + +m[3] : +m[3]; const d = new Date(y, +m[2]-1, +m[1]); return d.getMonth() === +m[2]-1 ? iso(d) : ""; }
  const d = new Date(t); return isNaN(d) ? "" : iso(d);
}
// Rows → [{date, label, tag, problem}] using the Date / Name / Type columns (any order, any case)
function readSpecialsSheet(rows) {
  const pick = (r, names) => { const k = Object.keys(r).find(k => names.includes(k.trim().toLowerCase())); return k ? r[k] : ""; };
  return rows.map(r => {
    const date = sheetDate(pick(r, ["date","day","occasion date"]));
    const label = String(pick(r, ["name","occasion","special occasion","event","title"]) || "").trim();
    const tag = String(pick(r, ["type","tag","category"]) || "").trim();
    return { date, label, tag, problem: !label && !date ? "empty" : !date ? "No valid date" : !label ? "No name" : "" };
  }).filter(r => r.problem !== "empty");
}

'''
swap("function SpecialOccasions(", HELPERS + "function SpecialOccasions(")

swap('''  const remove = s => { upSpecials(specials.filter(x=>x.key!==s.key)); showToast("Removed " + s.label); };''',
     '''  const remove = s => { upSpecials(specials.filter(x=>x.key!==s.key)); showToast("Removed " + s.label); };

  // ── Upload from Excel / CSV ──
  const [upload, setUpload] = useState(null);   // { file, rows:[{date,label,tag,problem}] }
  const fileRef = React.useRef(null);
  const ymd = d => { const x = new Date(d); return x.getFullYear()+"-"+String(x.getMonth()+1).padStart(2,"0")+"-"+String(x.getDate()).padStart(2,"0"); };
  const already = r => specials.some(sp => ymd(sp.date) === r.date && (sp.label||"").trim().toLowerCase() === r.label.toLowerCase());
  const readFile = async file => {
    if (!file) return;
    try {
      const X = await loadXLSX();
      const wb = X.read(await file.arrayBuffer(), { type:"array" });   // dates arrive as Excel day numbers
      const rows = readSpecialsSheet(X.utils.sheet_to_json(wb.Sheets[wb.SheetNames[0]], { defval:"" }));
      // Mark repeats within the file and ones already in the app
      const seen = new Set();
      rows.forEach(r => { if (r.problem) return; const k = r.date+"|"+r.label.toLowerCase();
        if (already(r)) r.problem = "Already added"; else if (seen.has(k)) r.problem = "Repeated in file"; seen.add(k); });
      if (!rows.length) showToast("No rows found — the first sheet needs Date and Name columns","error");
      setUpload({ file: file.name, rows });
    } catch (e) { showToast(e.message || "Couldn't read that file","error"); }
    if (fileRef.current) fileRef.current.value = "";
  };
  const importRows = () => {
    const good = upload.rows.filter(r => !r.problem);
    upSpecials([...specials, ...good.map(r => ({ key:uid(), label:r.label, date:new Date(r.date+"T12:00:00"), isSpecial:true, tag:r.tag||"Special" }))]);
    showToast(good.length+" special occasion"+(good.length===1?"":"s")+" added");
    setUpload(null);
  };
  const template = async () => {
    try {
      const X = await loadXLSX();
      const ws = X.utils.aoa_to_sheet([["Date","Name","Type"],["25/12/"+(new Date().getFullYear()+1),"Christmas Day Pooja","Festival"],["05/11/"+(new Date().getFullYear()+1),"Karthigai Deepam","Special"]]);
      ws["!cols"] = [{ wch:12 }, { wch:32 }, { wch:14 }];
      const wb = X.utils.book_new(); X.utils.book_append_sheet(wb, ws, "Special occasions");
      X.writeFile(wb, "special-occasions-template.xlsx");
    } catch (e) { showToast(e.message || "Couldn't make the template","error"); }
  };''')

swap('''            {!adding && <button onClick={()=>setAdding(true)} className="text-sm bg-amber-50 border border-amber-200 text-amber-700 rounded-lg px-3 py-1.5 font-medium hover:bg-amber-100">+ Add Special Occasion</button>}''',
     '''            {!adding && <button onClick={()=>setAdding(true)} className="text-sm bg-amber-50 border border-amber-200 text-amber-700 rounded-lg px-3 py-1.5 font-medium hover:bg-amber-100">+ Add Special Occasion</button>}
            <button onClick={()=>fileRef.current && fileRef.current.click()} className="text-sm bg-emerald-50 border border-emerald-200 text-emerald-700 rounded-lg px-3 py-1.5 font-medium hover:bg-emerald-100">📤 Upload from Excel</button>
            <input ref={fileRef} type="file" accept=".xlsx,.xls,.csv" className="hidden" onChange={e=>readFile(e.target.files[0])}/>
            <button onClick={template} className="text-xs text-slate-500 underline">Download template</button>''')

swap('''          {adding && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 space-y-2 fade-in">''',
     '''          {upload && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-3 space-y-2 fade-in">
              <div className="text-sm font-semibold text-emerald-800">{upload.file}: {upload.rows.filter(r=>!r.problem).length} to add{upload.rows.some(r=>r.problem) ? ", "+upload.rows.filter(r=>r.problem).length+" skipped" : ""}</div>
              <div className="max-h-64 overflow-y-auto bg-white border border-emerald-100 rounded-lg divide-y divide-slate-100">
                {upload.rows.map((r, i) => (
                  <div key={i} className={"flex items-center gap-3 px-3 py-1.5 text-sm "+(r.problem?"text-slate-400":"")}>
                    <span className="w-24 flex-shrink-0">{r.date ? new Date(r.date+"T12:00:00").toLocaleDateString("en-GB",{weekday:"short",day:"numeric",month:"short",year:"numeric"}) : "—"}</span>
                    <span className="flex-1 truncate">{r.label || "—"}</span>
                    <span className="text-xs text-amber-600">{r.tag||"Special"}</span>
                    {r.problem && <span className="text-xs text-red-500 font-semibold">{r.problem}</span>}
                  </div>
                ))}
              </div>
              <div className="flex gap-2">
                <button onClick={importRows} disabled={!upload.rows.some(r=>!r.problem)}
                  className="flex-1 bg-emerald-600 text-white rounded-lg py-1.5 text-sm font-bold hover:bg-emerald-700 disabled:opacity-40">Add {upload.rows.filter(r=>!r.problem).length} special occasions</button>
                <button onClick={()=>setUpload(null)} className="flex-1 bg-white border border-slate-200 text-slate-600 rounded-lg py-1.5 text-sm font-medium">Cancel</button>
              </div>
              <p className="text-xs text-slate-500">The first sheet needs columns <b>Date</b> and <b>Name</b> (and optionally <b>Type</b>). Dates like 25/12/2027 are read day first.</p>
            </div>
          )}
          {adding && (
            <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 space-y-2 fade-in">''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
