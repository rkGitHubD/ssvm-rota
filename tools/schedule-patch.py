"""Assignments: printable rota schedule (January–December) as a one-page PDF.

Usage: python3 tools/schedule-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def swap(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


PRINT = r'''// ─── Rota schedule for a year: one A4 page, scaled down to fit ───────────────
// Status per role: Done (week is over), Confirmed (someone assigned) or TBC (nobody yet)
function printRotaSchedule(year, { rotas = {}, members = [], specials = [], config = {} } = {}) {
  const esc = v => String(v == null ? "" : v).replace(/[&<>"']/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c]));
  const name = id => (members.find(m => m.id === id) || {}).name || "";
  const today = new Date(); today.setHours(0,0,0,0);
  const slots = [...getWeeksForYear(year), ...specials.filter(sp => new Date(sp.date).getFullYear() === year).map(sp => ({ ...sp, isSpecial:true }))]
    .sort((a, b) => new Date(a.date) - new Date(b.date));
  const status = (done, who) => done ? "<td class='st done'>Done</td>" : who ? "<td class='st ok'>Confirmed</td>" : "<td class='st tbc'>TBC</td>";
  let counts = { ok:0, tbc:0, done:0 };
  const rowsHtml = slots.map(sl => {
    const r = rotas[sl.key] || {};
    const done = new Date(sl.date) < today;
    const lead = name(r.lead), sec = (r.secondary || []).map(name).filter(Boolean).join(", ");
    if (done) counts.done++; else if (lead) counts.ok++; else counts.tbc++;
    const remarks = [sl.isSpecial ? "★ " + (sl.tag || sl.label || "Special") : "", r.notes || ""].filter(Boolean).join(" · ");
    return "<tr class='" + (done ? "past" : "") + "'><td>" + new Date(sl.date).toLocaleDateString("en-GB", { weekday:"short", day:"numeric", month:"short" })
      + (sl.isSpecial ? " <b>★</b>" : "") + "</td><td>" + (esc(lead) || "—") + "</td>" + status(done, lead)
      + "<td>" + (esc(sec) || "—") + "</td>" + status(done, sec) + "<td>" + esc(remarks) + "</td></tr>";
  }).join("");

  let h = "<!DOCTYPE html><html><head><meta charset='utf-8'/><title>Rota schedule " + year + "</title><style>"
    + "@page{size:A4;margin:10mm}*{box-sizing:border-box;margin:0;padding:0}"
    + "body{width:190mm;font-family:Arial,Helvetica,sans-serif;font-size:9.5px;color:#1e293b;background:#fff}"
    + ".hd{display:flex;align-items:center;gap:8px;border-bottom:2px solid #3730a3;padding-bottom:5px;margin-bottom:6px}"
    + ".hd img{height:36px;width:36px;object-fit:contain}.org{font-size:13px;font-weight:900;color:#1e1b4b}.sub{font-size:8.5px;color:#64748b}"
    + "table{width:100%;border-collapse:collapse}th{background:#3730a3;color:#fff;font-size:8.5px;text-align:left;padding:3px 4px}"
    + "td{padding:2.5px 4px;border-bottom:1px solid #e2e8f0;font-size:9px}"
    + ".st{font-weight:bold;text-align:center;width:62px}.ok{color:#166534;background:#dcfce7}.tbc{color:#b91c1c;background:#fee2e2}"
    + "tr.past td{background:#94a3b8;color:#f8fafc}tr.past td.done{background:#64748b;color:#fff}"
    + ".key{display:flex;gap:10px;margin-top:6px;font-size:8.5px;color:#475569}.key span{padding:1px 6px;border-radius:3px;font-weight:bold}"
    + "@media print{.noprint{display:none!important}}"
    + "</style></head><body>";
  h += "<div class='hd'>" + (config.logo ? "<img src='" + config.logo + "'/>" : "")
    + "<div><div class='org'>" + esc(config.fullName || config.orgName || "") + "</div>"
    + "<div class='sub'>Rota schedule · January – December " + year + "</div></div>"
    + "<div class='sub' style='margin-left:auto;text-align:right'>Printed " + new Date().toLocaleDateString("en-GB", { day:"numeric", month:"short", year:"numeric" })
    + "<br/>" + counts.ok + " confirmed · " + counts.tbc + " TBC · " + counts.done + " done</div></div>";
  h += "<table><tr><th>Date / Rota</th><th>Rota Lead</th><th style='text-align:center'>Status</th><th>Secondary</th><th style='text-align:center'>Status</th><th>Remarks</th></tr>"
    + (rowsHtml || "<tr><td colspan='6' style='text-align:center;color:#94a3b8'>No rota weeks for " + year + "</td></tr>") + "</table>";
  h += "<div class='key'><span class='ok'>Confirmed</span><span class='tbc'>TBC — still to be filled</span><span style='background:#64748b;color:#fff'>Done — week is over</span><span>★ Special occasion</span></div>";
  h += "<button class='noprint' onclick='window.print()' style='position:fixed;bottom:16px;right:16px;background:#3730a3;color:#fff;border:0;padding:8px 20px;border-radius:8px;font-size:12px;font-weight:bold;cursor:pointer'>Print / Save as PDF</button>"
    + "<script>window.onload=function(){var h=document.body.scrollHeight,max=1040;if(h>max)document.body.style.zoom=(max/h).toFixed(3);setTimeout(function(){window.print();},300);};<\/script>"
    + "</body></html>";
  const w = window.open("", "_blank");
  if (!w) return false;
  w.document.write(h); w.document.close();
  return true;
}

'''
swap("function MDAssignments(", PRINT + "function MDAssignments(")
swap('''function MDAssignments({ members, rotas, upRotas, allSlots, showToast, specials, upSpecials, generalOffers=[], upGeneralOffers }) {''',
     '''function MDAssignments({ members, rotas, upRotas, allSlots, showToast, specials, upSpecials, generalOffers=[], upGeneralOffers, config={} }) {
  const [schedYear, setSchedYear] = useState(config.year || new Date().getFullYear());''')
swap('''    <SwapPlanner members={members} rotas={rotas} upRotas={upRotas} allSlots={allSlots} generalOffers={generalOffers} upGeneralOffers={upGeneralOffers} showToast={showToast}/>''',
     '''    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 flex items-center gap-3 flex-wrap">
      <span className="text-xl">🖨</span>
      <div className="flex-1 min-w-0">
        <div className="font-semibold text-slate-800">Rota schedule (PDF)</div>
        <div className="text-xs text-slate-400">January – December: Rota Lead and Secondary for every week, with Confirmed / TBC / Done</div>
      </div>
      <select value={schedYear} onChange={e=>setSchedYear(parseInt(e.target.value))}
        className="border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white">
        {[-1,0,1].map(d => (config.year || new Date().getFullYear()) + d).map(y => <option key={y} value={y}>{y}</option>)}
      </select>
      <button onClick={()=>{ if (!printRotaSchedule(schedYear, { rotas, members, specials, config })) showToast("Allow pop-ups to print","error"); }}
        className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl text-sm font-bold">Print / PDF</button>
    </div>
    <SwapPlanner members={members} rotas={rotas} upRotas={upRotas} allSlots={allSlots} generalOffers={generalOffers} upGeneralOffers={upGeneralOffers} showToast={showToast}/>''')
swap('''generalOffers={generalOffers} upGeneralOffers={upGeneralOffers}/>}
      {section==="activities"''', '''generalOffers={generalOffers} upGeneralOffers={upGeneralOffers} config={config}/>}
      {section==="activities"''')
swap('''function MasterData({ generalOffers=[], upGeneralOffers,''', '''function MasterData({ config={}, generalOffers=[], upGeneralOffers,''')
swap('''<MasterData generalOffers={generalOffers}''', '''<MasterData config={config} generalOffers={generalOffers}''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
