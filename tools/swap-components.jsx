// ─── Rota Lead / Secondary swaps ─────────────────────────────────────────────
// A swap request is stored with the availability offers (rota-offers), which every
// member may save:
//   { id, type:"swap", memberId, name, slotKey, role:"lead"|"secondary",
//     withId, withSlotKey, note, status:"pending"|"done"|"declined"|"cancelled",
//     createdAt, resolvedAt, adminNote }
// The admin plans and applies swaps on the Assignments screen; applying updates the rota.
const SWAP_ROLE = { lead:"Rota Lead", secondary:"Secondary" };
const isSwap = o => o && o.type === "swap";
const slotText = s => s ? new Date(s.date).toLocaleDateString("en-GB",{weekday:"short",day:"numeric",month:"short",year:"numeric"}) + (s.isSpecial ? " ⭐ "+s.label : "") : "—";
// Is this member in this role on this week?
const inRole = (r, role, id) => role === "lead" ? (r||{}).lead === id : ((r||{}).secondary||[]).includes(id);
// Members who can take a role: leads come from Rota Leads and Secondaries (as in the lead picker)
const eligibleFor = (members, role) => members.filter(m => m.approved !== false && m.approved !== "rejected"
  && (role === "lead" ? (m.role === "primary" || m.role === "secondary") : m.role === "secondary"));

// ── Member side: ask the admin for a swap ─────────────────────────────────────
function SwapRequestForm({ rotas, allSlots, members, generalOffers, upGeneralOffers, currentUser, showToast }) {
  const me = currentUser.memberId;
  const today = new Date(); today.setHours(0,0,0,0);
  const upcoming = allSlots.filter(s => new Date(s.date) >= today);
  const myWeeks = upcoming.flatMap(s => ["lead","secondary"].filter(role => inRole(rotas[s.key], role, me)).map(role => ({ slot:s, role })));
  const mine = (generalOffers||[]).filter(o => isSwap(o) && o.memberId === me).slice().reverse();
  const [pick, setPick]       = useState("");   // "slotKey|role"
  const [withId, setWithId]   = useState("");
  const [withKey, setWithKey] = useState("");
  const [note, setNote]       = useState("");
  if (myWeeks.length === 0 && mine.length === 0) return null;

  const [slotKey, role] = pick ? pick.split("|") : ["", ""];
  const others = role ? eligibleFor(members, role).filter(m => m.id !== me) : [];
  // Their weeks: weeks where the chosen person has the same role (or any week, if no one chosen)
  const theirWeeks = upcoming.filter(s => s.key !== slotKey && (!withId || inRole(rotas[s.key], role, withId)));
  const getName = id => (members.find(m => m.id === id)||{}).name || "—";
  const slotOf = k => allSlots.find(s => s.key === k);

  const send = () => {
    if (!pick) return showToast("Choose the week you can't do","error");
    if ((generalOffers||[]).some(o => isSwap(o) && o.status === "pending" && o.memberId === me && o.slotKey === slotKey && o.role === role))
      return showToast("You already have a request open for that week","error");
    upGeneralOffers([...(generalOffers||[]), { id:uid(), type:"swap", memberId:me, name:currentUser.name, slotKey, role,
      withId, withSlotKey:withKey, note:note.trim(), status:"pending", createdAt:new Date().toISOString() }]);
    setPick(""); setWithId(""); setWithKey(""); setNote("");
    showToast("Swap request sent to the admin");
  };
  const cancel = id => upGeneralOffers((generalOffers||[]).map(o => o.id === id ? { ...o, status:"cancelled", resolvedAt:new Date().toISOString() } : o));

  const sel = "w-full border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-violet-300";
  const STATUS = { pending:["⏳ Waiting for admin","bg-amber-100 text-amber-700"], done:["✅ Swapped","bg-emerald-100 text-emerald-700"],
                   declined:["❌ Not possible","bg-red-100 text-red-600"], cancelled:["Cancelled","bg-slate-100 text-slate-500"] };
  return (
    <div className="bg-gradient-to-br from-violet-50 to-indigo-50 border border-violet-200 rounded-2xl p-5 space-y-3">
      <div className="flex items-start gap-3">
        <span className="text-2xl">🔁</span>
        <div>
          <h3 className="font-bold text-violet-800 text-sm">Ask to swap a week</h3>
          <p className="text-xs text-violet-600 mt-0.5">Can't do one of your weeks? Ask the admin to swap it. If you've already agreed a swap with someone, choose them and their week.</p>
        </div>
      </div>
      {myWeeks.length > 0 && (
        <div className="grid sm:grid-cols-2 gap-2">
          <label className="block sm:col-span-2"><span className="text-xs font-semibold text-slate-600">My week I can't do *</span>
            <select value={pick} onChange={e=>{setPick(e.target.value); setWithId(""); setWithKey("");}} className={sel}>
              <option value="">Choose…</option>
              {myWeeks.map(w => <option key={w.slot.key+w.role} value={w.slot.key+"|"+w.role}>{slotText(w.slot)} — as {SWAP_ROLE[w.role]}</option>)}
            </select>
          </label>
          <label className="block"><span className="text-xs font-semibold text-slate-600">Swap with (if agreed)</span>
            <select value={withId} onChange={e=>{setWithId(e.target.value); setWithKey("");}} disabled={!pick} className={sel}>
              <option value="">Anyone — admin to find</option>
              {others.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
            </select>
          </label>
          <label className="block"><span className="text-xs font-semibold text-slate-600">I'll take their week</span>
            <select value={withKey} onChange={e=>setWithKey(e.target.value)} disabled={!pick} className={sel}>
              <option value="">{withId ? "Choose their week…" : "Any week"}</option>
              {theirWeeks.map(s => <option key={s.key} value={s.key}>{slotText(s)}{withId ? "" : rotas[s.key] && role==="lead" && rotas[s.key].lead ? " — "+getName(rotas[s.key].lead) : ""}</option>)}
            </select>
          </label>
          <label className="block sm:col-span-2"><span className="text-xs font-semibold text-slate-600">Note</span>
            <textarea value={note} onChange={e=>setNote(e.target.value)} rows={2} placeholder="e.g. Away that weekend"
              className={sel+" resize-none"}/>
          </label>
          <button onClick={send} disabled={!pick}
            className="sm:col-span-2 bg-violet-600 hover:bg-violet-700 text-white rounded-xl py-2.5 text-sm font-bold disabled:opacity-40">Send swap request</button>
        </div>
      )}
      {mine.length > 0 && (
        <div className="space-y-1.5">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">My swap requests</div>
          {mine.map(o => (
            <div key={o.id} className="bg-white border border-slate-200 rounded-xl px-3 py-2 text-sm flex items-start gap-2">
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-slate-700">{slotText(slotOf(o.slotKey))} <span className="font-normal text-slate-500">as {SWAP_ROLE[o.role]}</span></div>
                {(o.withId || o.withSlotKey) && <div className="text-xs text-slate-500">with {o.withId ? getName(o.withId) : "anyone"}{o.withSlotKey ? " · their week "+slotText(slotOf(o.withSlotKey)) : ""}</div>}
                {o.adminNote && <div className="text-xs text-slate-600 mt-0.5">Admin: {o.adminNote}</div>}
              </div>
              <span className={"text-xs font-semibold px-2 py-0.5 rounded-full whitespace-nowrap "+(STATUS[o.status]||STATUS.pending)[1]}>{(STATUS[o.status]||STATUS.pending)[0]}</span>
              {o.status === "pending" && <button onClick={()=>cancel(o.id)} className="text-xs text-slate-400 underline">Cancel</button>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Admin side: plan and apply swaps (two people, or a chain of several weeks) ─
function SwapPlanner({ members, rotas, upRotas, allSlots, generalOffers, upGeneralOffers, showToast }) {
  const today = new Date(); today.setHours(0,0,0,0);
  const upcoming = allSlots.filter(s => new Date(s.date) >= today);
  const pending = (generalOffers||[]).filter(o => isSwap(o) && o.status === "pending");
  // Open whenever requests are waiting, unless the admin has folded or opened it
  const [openChoice, setOpen] = useState(null);
  const open = openChoice === null ? pending.length > 0 : openChoice;
  const [role, setRole]       = useState("lead");
  const [rows, setRows]       = useState([{ slotKey:"", fromId:"", toId:"" }]);
  const [linked, setLinked]   = useState([]);    // request ids this plan answers
  const [declining, setDeclining] = useState(null);
  const [declineNote, setDeclineNote] = useState("");

  const getName = id => (members.find(m => m.id === id)||{}).name || "—";
  const slotOf  = k => allSlots.find(s => s.key === k);
  const people  = eligibleFor(members, role);
  // Who is in the role on a week now (for a Secondary row: the chosen person, or the first one)
  const current = (k, fromId) => role === "lead" ? ((rotas[k]||{}).lead || "") : (fromId || ((rotas[k]||{}).secondary||[])[0] || "");
  const weekLabel = s => {
    const r = rotas[s.key]||{};
    const who = role === "lead" ? (r.lead ? getName(r.lead) : "no lead") : ((r.secondary||[]).map(getName).join(", ") || "no secondary");
    return slotText(s) + " — " + who;
  };

  const reset = (newRole) => { setRows([{ slotKey:"", fromId:"", toId:"" }]); setLinked([]); if (newRole) setRole(newRole); };
  const setRow = (i, patch) => setRows(rows.map((r, j) => j === i ? { ...r, ...patch } : r));
  const pickWeek = (i, k) => setRow(i, { slotKey:k, fromId: role === "lead" ? ((rotas[k]||{}).lead||"") : (((rotas[k]||{}).secondary||[])[0]||"") });
  // Each week takes the person from the week above; the first takes the last one's person
  const rotate = () => setRows(rows.map((r, i) => ({ ...r, toId: current(rows[(i + rows.length - 1) % rows.length].slotKey, rows[(i + rows.length - 1) % rows.length].fromId) })));

  // Start a plan from a member's request
  const planFrom = req => {
    const r1 = { slotKey:req.slotKey, fromId:req.memberId, toId:req.withId||"" };
    const plan = [r1];
    if (req.withSlotKey) plan.push({ slotKey:req.withSlotKey, fromId: req.role === "lead" ? ((rotas[req.withSlotKey]||{}).lead||"") : (req.withId || ((rotas[req.withSlotKey]||{}).secondary||[])[0] || ""), toId:req.memberId });
    if (req.withSlotKey && !r1.toId) r1.toId = plan[1].fromId;
    setRole(req.role); setRows(plan); setLinked([req.id]); setOpen(true);
  };
  const decline = req => {
    upGeneralOffers((generalOffers||[]).map(o => o.id === req.id ? { ...o, status:"declined", adminNote:declineNote.trim(), resolvedAt:new Date().toISOString() } : o));
    setDeclining(null); setDeclineNote(""); showToast("Request declined");
  };

  // Checks before applying
  const filled = rows.filter(r => r.slotKey && r.toId);
  const problems = [];
  rows.forEach((r, i) => {
    if (!r.slotKey) return;
    const s = slotOf(r.slotKey), rr = rotas[r.slotKey]||{};
    if (!r.toId) problems.push(slotText(s)+": choose who takes it");
    else if (r.toId === current(r.slotKey, r.fromId)) problems.push(slotText(s)+": "+getName(r.toId)+" already has it");
    else if (role === "lead" && (rr.secondary||[]).includes(r.toId)) problems.push(slotText(s)+": "+getName(r.toId)+" is already Secondary that week");
    else if (role === "secondary" && (rr.lead === r.toId || (rr.secondary||[]).includes(r.toId))) problems.push(slotText(s)+": "+getName(r.toId)+" is already on that week");
    if (rows.some((o, j) => j !== i && o.slotKey === r.slotKey && o.fromId === r.fromId)) problems.push(slotText(s)+" is in the plan twice");
  });
  // How many weeks each person ends up with in this role (upcoming weeks)
  const before = {}, after = {};
  upcoming.forEach(s => { const r = rotas[s.key]||{}; (role === "lead" ? [r.lead] : (r.secondary||[])).filter(Boolean).forEach(id => { before[id] = (before[id]||0) + 1; after[id] = (after[id]||0) + 1; }); });
  filled.forEach(r => { const f = current(r.slotKey, r.fromId); if (f) after[f] = (after[f]||0) - 1; after[r.toId] = (after[r.toId]||0) + 1; });
  const changed = Object.keys(after).filter(id => (before[id]||0) !== after[id]);

  const apply = () => {
    if (filled.length === 0) return showToast("Add at least one week","error");
    if (problems.length) return showToast(problems[0],"error");
    const at = new Date().toISOString();
    const next = { ...rotas };
    filled.forEach(r => {
      const rr = { lead:"", primary:[], secondary:[], actOwners:{}, ...(next[r.slotKey]||{}) };
      const from = current(r.slotKey, r.fromId);
      if (role === "lead") rr.lead = r.toId;
      else rr.secondary = from && (rr.secondary||[]).includes(from) ? rr.secondary.map(x => x === from ? r.toId : x) : [...(rr.secondary||[]), r.toId];
      rr.swapLog = [...(rr.swapLog||[]), { at, role, from, to:r.toId }];
      next[r.slotKey] = rr;
    });
    upRotas(next);
    // Requests answered by this plan: the ones it started from, and any pending ones it covers
    const covered = o => isSwap(o) && o.status === "pending" && o.role === role
      && (linked.includes(o.id) || filled.some(r => r.slotKey === o.slotKey && current(r.slotKey, r.fromId) === o.memberId));
    if ((generalOffers||[]).some(covered))
      upGeneralOffers((generalOffers||[]).map(o => covered(o) ? { ...o, status:"done", resolvedAt:at } : o));
    showToast(filled.length+" week"+(filled.length>1?"s":"")+" updated");
    reset();
  };

  const sel = "w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-violet-300";
  return (
    <div className="bg-white rounded-2xl border border-violet-200 shadow-sm">
      <button onClick={()=>setOpen(!open)} className="w-full flex items-center gap-3 p-4 text-left">
        <span className="text-xl">🔁</span>
        <div className="flex-1">
          <div className="font-semibold text-slate-800">Swap Rota Leads / Secondaries</div>
          <div className="text-xs text-slate-400">Swap two people's weeks, or move several weeks round in a chain</div>
        </div>
        {pending.length > 0 && <span className="bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">{pending.length} request{pending.length>1?"s":""}</span>}
        <span className={"text-slate-400 text-xs transition-transform "+(open?"rotate-90":"")}>▶</span>
      </button>
      {open && (
        <div className="px-4 pb-4 space-y-4 border-t border-slate-100 pt-4">
          {/* Requests from members */}
          {pending.length > 0 && (
            <div className="space-y-2">
              <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Swap requests</div>
              {pending.map(o => (
                <div key={o.id} className={"rounded-xl border px-3 py-2 text-sm "+(linked.includes(o.id)?"border-violet-400 bg-violet-50":"border-slate-200")}>
                  <div className="flex items-start gap-2 flex-wrap">
                    <div className="flex-1 min-w-0">
                      <b>{o.name}</b> can't do <b>{slotText(slotOf(o.slotKey))}</b> as {SWAP_ROLE[o.role]}
                      {(o.withId || o.withSlotKey) && <span className="text-slate-500"> · agreed with {o.withId ? getName(o.withId) : "anyone"}{o.withSlotKey ? " for "+slotText(slotOf(o.withSlotKey)) : ""}</span>}
                      {o.note && <div className="text-xs text-slate-500 italic">"{o.note}"</div>}
                    </div>
                    <button onClick={()=>planFrom(o)} className="text-xs bg-violet-600 text-white px-3 py-1.5 rounded-lg font-semibold hover:bg-violet-700">Plan swap</button>
                    <button onClick={()=>{setDeclining(o.id); setDeclineNote("");}} className="text-xs text-red-500 underline">Decline</button>
                  </div>
                  {declining === o.id && (
                    <div className="flex gap-2 mt-2">
                      <input value={declineNote} onChange={e=>setDeclineNote(e.target.value)} placeholder="Reason (shown to them)" autoFocus
                        className="flex-1 border border-slate-200 rounded-lg px-2 py-1 text-xs"/>
                      <button onClick={()=>decline(o)} className="text-xs bg-red-600 text-white px-3 py-1 rounded-lg font-semibold">Decline</button>
                      <button onClick={()=>setDeclining(null)} className="text-xs text-slate-500">Cancel</button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Planner */}
          <div className="space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Swap</span>
              {["lead","secondary"].map(r => (
                <button key={r} onClick={()=>reset(r)}
                  className={"text-xs px-3 py-1.5 rounded-full font-semibold border "+(role===r?"bg-violet-600 text-white border-violet-600":"bg-white text-slate-600 border-slate-200")}>{r === "lead" ? "Rota Leads" : "Secondaries"}</button>
              ))}
            </div>
            {rows.map((r, i) => {
              const rr = rotas[r.slotKey]||{};
              return (
                <div key={i} className="grid grid-cols-1 md:grid-cols-[2fr_1.2fr_auto_1.2fr_auto] gap-2 items-center bg-slate-50 rounded-xl p-2">
                  <select value={r.slotKey} onChange={e=>pickWeek(i, e.target.value)} className={sel}>
                    <option value="">Choose week…</option>
                    {upcoming.map(s => <option key={s.key} value={s.key}>{weekLabel(s)}</option>)}
                  </select>
                  {role === "lead" || (rr.secondary||[]).length <= 1 ? (
                    <div className="text-sm text-slate-600 px-2 truncate">{r.slotKey ? (current(r.slotKey, r.fromId) ? getName(current(r.slotKey, r.fromId)) : "— nobody —") : ""}</div>
                  ) : (
                    <select value={r.fromId} onChange={e=>setRow(i, { fromId:e.target.value })} className={sel}>
                      {(rr.secondary||[]).map(id => <option key={id} value={id}>{getName(id)}</option>)}
                    </select>
                  )}
                  <span className="text-slate-400 text-center hidden md:block">→</span>
                  <select value={r.toId} onChange={e=>setRow(i, { toId:e.target.value })} disabled={!r.slotKey} className={sel}>
                    <option value="">New {SWAP_ROLE[role]}…</option>
                    {people.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                  </select>
                  <button onClick={()=>setRows(rows.length > 1 ? rows.filter((_, j) => j !== i) : [{ slotKey:"", fromId:"", toId:"" }])}
                    className="text-slate-400 hover:text-red-500 text-sm px-2" title="Remove this week">✕</button>
                </div>
              );
            })}
            <div className="flex gap-2 flex-wrap">
              <button onClick={()=>setRows([...rows, { slotKey:"", fromId:"", toId:"" }])}
                className="text-xs border border-slate-200 bg-white px-3 py-1.5 rounded-lg font-semibold text-slate-600 hover:bg-slate-50">+ Add week</button>
              {rows.filter(r => r.slotKey).length >= 2 && (
                <button onClick={rotate} className="text-xs border border-violet-200 bg-violet-50 px-3 py-1.5 rounded-lg font-semibold text-violet-700 hover:bg-violet-100"
                  title="Each week takes the person from the week above; the first week takes the last one's person">↻ Fill in as a swap / chain</button>
              )}
            </div>
          </div>

          {/* Preview */}
          {filled.length > 0 && (
            <div className="bg-violet-50 border border-violet-200 rounded-xl p-3 text-sm space-y-1">
              <div className="text-xs font-bold text-violet-700 uppercase tracking-wider">After the swap</div>
              {filled.map((r, i) => <div key={i}>{slotText(slotOf(r.slotKey))}: <s className="text-slate-400">{current(r.slotKey, r.fromId) ? getName(current(r.slotKey, r.fromId)) : "nobody"}</s> → <b>{getName(r.toId)}</b></div>)}
              {changed.length > 0 && (
                <div className="text-xs text-slate-500 pt-1">Upcoming weeks as {SWAP_ROLE[role]}: {changed.map(id => getName(id)+" "+(before[id]||0)+"→"+after[id]).join(" · ")}</div>
              )}
            </div>
          )}
          {problems.length > 0 && filled.length > 0 && (
            <div className="text-xs text-red-600 space-y-0.5">{problems.map((p, i) => <div key={i}>⚠ {p}</div>)}</div>
          )}
          <div className="flex gap-2">
            <button onClick={apply} disabled={filled.length === 0 || problems.length > 0}
              className="bg-violet-600 hover:bg-violet-700 text-white px-5 py-2 rounded-xl text-sm font-bold disabled:opacity-40">Apply swap to the rota</button>
            {(rows.length > 1 || rows[0].slotKey) && <button onClick={()=>reset()} className="text-sm text-slate-500 px-2">Clear</button>}
          </div>
        </div>
      )}
    </div>
  );
}

