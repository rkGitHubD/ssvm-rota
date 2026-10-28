// ─── Prasadham plan: who brings prasadham on the next 6–8 rota days ──────────
// Stored on the rota day itself (rotas[key].prasadhamId), so it shows on the Rota Calendar,
// Dashboard and that day's Rota Sheet. A special occasion on a Sunday shares the Sunday's row.
const localDay = d => { const x = new Date(d); return x.getFullYear()+"-"+String(x.getMonth()+1).padStart(2,"0")+"-"+String(x.getDate()).padStart(2,"0"); };
function prasadhamSlots(specials = [], n = 8) {
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
}

function PrasadhamPlan({ prasadham = [], rotas = {}, upRotas, specials = [], showToast }) {
  const [n, setN] = useState(8);
  const slots = prasadhamSlots(specials, n);
  const who = s => s.keys.map(k => (rotas[k] || {}).prasadhamId).find(Boolean) || "";
  const pname = id => (prasadham.find(p => p.id === id) || {}).name || "";
  const assign = changes => upRotas(prev => {
    const next = { ...prev };
    changes.forEach(([s, id]) => s.keys.forEach(k => { next[k] = { ...(next[k] || {}), prasadhamId: id }; }));
    return next;
  });
  // Fill the empty days: whoever has provided least often, then least recently, never twice in a row
  const fill = () => {
    if (!prasadham.length) return showToast("Add prasadham providers first","error");
    const today = localDay(new Date());
    const stats = Object.fromEntries(prasadham.map(p => [p.id, { count:0, last:"" }]));
    const dayOf = k => { const sl = /^\d{4}-w\d+$/.test(k) ? getWeeksForYear(parseInt(k)).find(w => w.key === k) : specials.find(sp => sp.key === k); return sl ? localDay(sl.date) : ""; };
    Object.entries(rotas).forEach(([k, r]) => { const st = r && stats[r.prasadhamId]; if (!st) return;
      const d = dayOf(k); if (d && d >= today) return;   // upcoming days are counted below
      st.count++; if (d > st.last) st.last = d; });
    slots.forEach(s => { const st = stats[who(s)]; if (st) { st.count++; if (s.day > st.last) st.last = s.day; } });
    const changes = [];
    let prev = "";
    slots.forEach(s => {
      let id = who(s);
      if (!id) {
        const pick = prasadham.filter(p => p.id !== prev || prasadham.length === 1)
          .sort((a, b) => stats[a.id].count - stats[b.id].count || stats[a.id].last.localeCompare(stats[b.id].last))[0];
        id = pick.id; stats[id].count++; stats[id].last = s.day; changes.push([s, id]);
      }
      prev = id;
    });
    if (!changes.length) return showToast("Every day already has a provider");
    assign(changes); showToast(changes.length + " day" + (changes.length > 1 ? "s" : "") + " filled — check and adjust");
  };
  const share = () => {
    const lines = slots.map(s => "• " + new Date(s.date).toLocaleDateString("en-GB",{ weekday:"short", day:"numeric", month:"short" })
      + (s.occasions.length ? " (" + s.occasions.join(", ") + ")" : "") + " — " + (pname(who(s)) || "To be filled"));
    window.open("https://wa.me/?text=" + encodeURIComponent("🍛 *Prasadham — next " + slots.length + " weeks*\n" + lines.join("\n")), "_blank");
  };
  const filled = slots.filter(s => who(s)).length;
  return (
    <div className="bg-white rounded-2xl border border-amber-200 shadow-sm p-5 space-y-3">
      <div className="flex items-center gap-2 flex-wrap">
        <div className="flex-1 min-w-[12rem]">
          <h3 className="font-bold text-slate-800">🍛 Prasadham plan — next
            <select value={n} onChange={e=>setN(parseInt(e.target.value))} className="mx-1.5 border border-slate-200 rounded-lg px-1.5 py-0.5 text-sm bg-white">{[6,7,8].map(x => <option key={x} value={x}>{x}</option>)}</select>weeks</h3>
          <p className="text-xs text-slate-400 mt-0.5">{filled} of {slots.length} filled. Each provider shows on that day's Rota Calendar, Dashboard and Rota Sheet.</p>
        </div>
        <button onClick={fill} className="bg-amber-500 hover:bg-amber-600 text-white px-3 py-2 rounded-xl text-xs font-bold">✨ Fill empty weeks</button>
        <button onClick={share} title="Share on WhatsApp" className="bg-[#25D366] hover:bg-[#1ebe57] text-white px-3 py-2 rounded-xl text-xs font-bold">Share list</button>
      </div>
      <div className="divide-y divide-slate-100">
        {slots.map(s => { const id = who(s), pv = prasadham.find(p => p.id === id); return (
          <div key={s.day} className="py-2 flex items-center gap-2 flex-wrap text-sm">
            <span className="w-28 font-medium text-slate-700">{new Date(s.date).toLocaleDateString("en-GB",{ weekday:"short", day:"numeric", month:"short" })}</span>
            <span className="flex-1 min-w-[6rem] text-xs text-violet-700 font-semibold truncate">{s.occasions.map(o => "★ " + o).join(" · ")}</span>
            {pv && pv.phone && <span className="text-xs text-slate-400">📱 {pv.phone}</span>}
            <select value={id} onChange={e=>assign([[s, e.target.value]])}
              className={"border rounded-lg px-2 py-1.5 text-sm w-48 " + (id ? "border-emerald-300 bg-emerald-50 text-emerald-800 font-semibold" : "border-red-200 bg-red-50 text-red-600")}>
              <option value="">— To be filled —</option>
              {prasadham.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </div>); })}
      </div>
    </div>
  );
}

