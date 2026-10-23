// ─── Generate a year's rota ──────────────────────────────────────────────────
// Rules are kept in Settings (config.rotaRules) so they are the same next time:
//   minGap   — rota days a person must wait before their next turn (2 = never back to back)
//   maxPer   — { memberId: most turns in the year } for the one or two exceptions
//   exclude  — member ids left out of the year
//   includeSpecials — special occasions get their own Rota Lead / Secondary too
// Generated weeks are saved as not yet confirmed, so the schedule shows them as TBC.
const DEFAULT_ROTA_RULES = { minGap: 2, includeSpecials: true, maxPer: {}, exclude: [] };

// Share `n` rota days in date order among `ids`: everyone an equal share except people
// with a yearly maximum, spread evenly through the year, keeping `minGap` between turns.
function planRole(n, ids, rules) {
  const cap = id => { const v = parseInt((rules.maxPer||{})[id], 10); return v > 0 ? v : Infinity; };
  // Equal shares: people capped below the fair share keep their cap, the rest split what's left
  const quota = {};
  let open = ids.slice(), left = n;
  for (;;) {
    const fair = open.length ? left / open.length : 0;
    const under = open.filter(id => cap(id) < fair);
    if (!under.length) break;
    under.forEach(id => { quota[id] = cap(id); left -= cap(id); });
    open = open.filter(id => !under.includes(id));
  }
  open.forEach((id, i) => { quota[id] = Math.floor(left / open.length) + (i < left % open.length ? 1 : 0); });
  const count = {}, last = {};
  const plan = [];
  for (let i = 0; i < n; i++) {
    const can = ids.filter(id => (count[id]||0) < (quota[id]||0));
    const rested = can.filter(id => last[id] === undefined || i - last[id] >= rules.minGap);
    const pool = rested.length ? rested : can;
    // Most behind their even pace first; then whoever has waited longest
    pool.sort((a, b) => ((count[a]||0)+1)/quota[a] - ((count[b]||0)+1)/quota[b] || (last[a] ?? -1e9) - (last[b] ?? -1e9));
    const id = pool[0] || "";
    if (id) { count[id] = (count[id]||0) + 1; last[id] = i; }
    plan.push(id);
  }
  return plan;
}

function RotaGenerator({ members, rotas, upRotas, specials, config, upConfig, showToast }) {
  const [open, setOpen]   = useState(false);
  const [year, setYear]   = useState((config.year || new Date().getFullYear()) + 1);
  const [plan, setPlan]   = useState(null);   // [{ key, date, label, lead, sec }]
  const rules = { ...DEFAULT_ROTA_RULES, ...(config.rotaRules||{}) };
  const setRules = patch => upConfig({ ...config, rotaRules: { ...rules, ...patch } });

  const approved = m => m.approved !== false && m.approved !== "rejected";
  const leads = members.filter(m => approved(m) && m.role === "primary");
  const secs  = members.filter(m => approved(m) && m.role === "secondary");
  const name  = id => (members.find(m => m.id === id)||{}).name || "";
  const ymd   = d => { const x = new Date(d); return x.getFullYear()+"-"+(x.getMonth()+1)+"-"+x.getDate(); };

  // Rota days for the year: every Sunday, plus special occasions on other days if wanted
  const days = () => {
    const weeks = getWeeksForYear(year).map(w => ({ key:w.key, date:w.date, label:"" }));
    (specials||[]).filter(sp => new Date(sp.date).getFullYear() === year).forEach(sp => {
      const w = weeks.find(x => ymd(x.date) === ymd(sp.date));
      if (w) w.label = (w.label ? w.label+" · " : "") + (sp.label || sp.tag || "Special");
      else if (rules.includeSpecials) weeks.push({ key:sp.key, date:new Date(sp.date), label:sp.label || sp.tag || "Special", special:true });
    });
    return weeks.sort((a, b) => new Date(a.date) - new Date(b.date));
  };
  const generate = () => {
    const d = days();
    const keep = id => !(rules.exclude||[]).includes(id);
    const L = planRole(d.length, leads.map(m => m.id).filter(keep), rules);   // Rota Leads first
    const S = planRole(d.length, secs.map(m => m.id).filter(keep), rules);
    setPlan(d.map((x, i) => ({ ...x, lead: L[i], sec: S[i] })));
  };
  const setCell = (i, f, v) => setPlan(plan.map((p, j) => j === i ? { ...p, [f]: v } : p));

  // Checks on the current plan
  const issues = {}; const totals = {};
  if (plan) ["lead","sec"].forEach(f => {
    const last = {};
    plan.forEach((p, i) => {
      const id = p[f]; if (!id) { issues[i+f] = "Nobody"; return; }
      totals[id] = (totals[id]||0) + 1;
      if (last[id] !== undefined && i - last[id] < rules.minGap) issues[i+f] = "Too soon after "+new Date(plan[last[id]].date).toLocaleDateString("en-GB",{day:"numeric",month:"short"});
      last[id] = i;
    });
  });
  const overMax = Object.keys(totals).filter(id => parseInt((rules.maxPer||{})[id]) > 0 && totals[id] > parseInt(rules.maxPer[id]));
  const existing = plan ? plan.filter(p => (rotas[p.key]||{}).lead || ((rotas[p.key]||{}).secondary||[]).length).length : 0;

  const save = () => {
    const next = { ...rotas };
    plan.forEach(p => {
      next[p.key] = { lead:"", primary:[], secondary:[], actOwners:{}, ...(rotas[p.key]||{}),
        lead: p.lead || "", secondary: p.sec ? [p.sec] : [], leadConfirmed: false, secondaryConfirmed: false, generated: year };
    });
    upRotas(next);
    showToast(year+" rota saved — every week shows TBC until confirmed");
    setPlan(null);
  };

  const sel = "w-full border border-slate-200 rounded-lg px-2 py-1 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-300";
  const person = (m, roleLabel) => (
    <div key={m.id} className="flex items-center gap-2 text-sm py-1 border-b border-slate-100 last:border-0">
      <span className="flex-1 truncate">{m.name} <span className="text-xs text-slate-400">{roleLabel}</span></span>
      <label className="flex items-center gap-1 text-xs text-slate-500">Max
        <input type="number" min="1" value={(rules.maxPer||{})[m.id]||""} placeholder="—"
          onChange={e=>setRules({ maxPer: { ...(rules.maxPer||{}), [m.id]: e.target.value } })}
          className="w-14 border border-slate-200 rounded px-1 py-0.5 text-sm"/></label>
      <label className="flex items-center gap-1 text-xs text-slate-500">
        <input type="checkbox" checked={(rules.exclude||[]).includes(m.id)}
          onChange={e=>setRules({ exclude: e.target.checked ? [...(rules.exclude||[]), m.id] : (rules.exclude||[]).filter(x => x !== m.id) })}/> Leave out</label>
    </div>
  );

  return (
    <div className="bg-white rounded-2xl border border-indigo-200 shadow-sm">
      <button onClick={()=>setOpen(!open)} className="w-full flex items-center gap-3 p-4 text-left">
        <span className="text-xl">🗓</span>
        <div className="flex-1">
          <div className="font-semibold text-slate-800">Generate rota for next year</div>
          <div className="text-xs text-slate-400">Shares the weeks fairly between Rota Leads and Secondaries using your rules; review, adjust, then save</div>
        </div>
        <span className={"text-slate-400 text-xs transition-transform "+(open?"rotate-90":"")}>▶</span>
      </button>
      {open && (
        <div className="px-4 pb-4 pt-4 border-t border-slate-100 space-y-4">
          {/* Rules */}
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Rules</div>
              <label className="flex items-center gap-2 text-sm">Year
                <select value={year} onChange={e=>{setYear(parseInt(e.target.value)); setPlan(null);}} className="border border-slate-200 rounded-lg px-2 py-1 text-sm">
                  {[0,1,2].map(d => (config.year || new Date().getFullYear()) + d).map(y => <option key={y} value={y}>{y}</option>)}
                </select></label>
              <label className="flex items-center gap-2 text-sm">Same person again only after
                <select value={rules.minGap} onChange={e=>setRules({ minGap: parseInt(e.target.value) })} className="border border-slate-200 rounded-lg px-2 py-1 text-sm">
                  <option value={2}>1 week off (never back to back)</option>
                  <option value={3}>2 weeks off</option>
                  <option value={4}>3 weeks off</option>
                  <option value={1}>no gap needed</option>
                </select></label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={!!rules.includeSpecials} onChange={e=>setRules({ includeSpecials: e.target.checked })}/>
                Give special occasions on other days their own Rota Lead and Secondary</label>
              <p className="text-xs text-slate-400">Everyone gets an equal share of the year, except anyone with a maximum. Rota Leads are planned first, then Secondaries.</p>
            </div>
            <div>
              <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">Exceptions — most turns per year</div>
              <div className="max-h-56 overflow-y-auto border border-slate-100 rounded-xl px-3">
                {leads.map(m => person(m, "Rota Lead"))}
                {secs.map(m => person(m, "Secondary"))}
                {leads.length + secs.length === 0 && <p className="text-sm text-slate-400 py-2">No Rota Leads or Secondaries yet.</p>}
              </div>
            </div>
          </div>
          <button onClick={generate} disabled={leads.length + secs.length === 0}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded-xl text-sm font-bold disabled:opacity-40">{plan ? "↻ Generate again" : "Generate "+year+" rota"}</button>

          {/* Review */}
          {plan && (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2 text-xs">
                {[...leads, ...secs].filter(m => !(rules.exclude||[]).includes(m.id)).map(m => (
                  <span key={m.id} className={"px-2 py-1 rounded-full border "+(overMax.includes(m.id)?"bg-red-50 border-red-300 text-red-700":"bg-slate-50 border-slate-200 text-slate-600")}>
                    {m.name}: <b>{totals[m.id]||0}</b>{parseInt((rules.maxPer||{})[m.id])>0 ? " / max "+rules.maxPer[m.id] : ""}</span>
                ))}
              </div>
              <div className="border border-slate-200 rounded-xl overflow-x-auto max-h-[28rem] overflow-y-auto">
                <table className="w-full text-sm min-w-[560px]">
                  <thead className="bg-slate-100 text-xs text-slate-500 uppercase sticky top-0">
                    <tr><th className="text-left px-3 py-2">Date</th><th className="text-left px-2 py-2">Rota Lead</th><th className="text-left px-2 py-2">Secondary</th><th className="text-left px-2 py-2">Occasion</th></tr>
                  </thead>
                  <tbody>
                    {plan.map((p, i) => (
                      <tr key={p.key} className="border-t border-slate-100">
                        <td className="px-3 py-1.5 whitespace-nowrap">{new Date(p.date).toLocaleDateString("en-GB",{weekday:"short",day:"numeric",month:"short"})}</td>
                        {["lead","sec"].map(f => (
                          <td key={f} className="px-2 py-1">
                            <select value={p[f]} onChange={e=>setCell(i, f, e.target.value)}
                              className={sel+(issues[i+f] ? " border-amber-400 bg-amber-50" : "")} title={issues[i+f]||""}>
                              <option value="">TBC</option>
                              {(f === "lead" ? leads : secs).map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                            </select>
                            {issues[i+f] && issues[i+f] !== "Nobody" && <div className="text-xs text-amber-700">{issues[i+f]}</div>}
                          </td>
                        ))}
                        <td className="px-2 py-1 text-xs text-slate-500">{p.label && "★ "+p.label}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {existing > 0 ? (
                <TypedConfirm word="REPLACE" label={"Save as the "+year+" rota"} onConfirm={save}
                  warning={existing+" of these days already have people assigned. Saving replaces their Rota Lead and Secondary."}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2 rounded-xl text-sm font-bold"/>
              ) : (
                <button onClick={save} className="bg-emerald-600 hover:bg-emerald-700 text-white px-5 py-2 rounded-xl text-sm font-bold">Save as the {year} rota</button>
              )}
              <p className="text-xs text-slate-400">Saved weeks show as <b>TBC</b> on the schedule until confirmed (tick "Confirmed" when you open a week below). {year !== config.year && <>The calendar shows {year} once Settings → Rota Year is changed to {year}.</>}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

