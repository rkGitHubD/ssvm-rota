"""Swap planner: the "new person" list shows each person with their own weeks, so
picking "Lakshmi — Sat 13 Dec" swaps the two weeks in one go. A plan started from a
request stays on that request's role (a Rota Lead isn't swapped with a Secondary).

Usage: python3 tools/swap-pairs-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def swap(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


# Choosing someone's week: this row goes to them, and their week comes back to this row's person
swap('''  const setRow = (i, patch) => setRows(rows.map((r, j) => j === i ? { ...r, ...patch } : r));''',
     '''  const setRow = (i, patch) => setRows(rows.map((r, j) => j === i ? { ...r, ...patch } : r));
  // The new person for a row, optionally swapping weeks with them ("id|theirSlotKey").
  // A week added this way is marked auto and removed again if the choice changes.
  const pickPerson = (i, value) => {
    const [toId, theirKey] = value.split("|");
    const row = rows[i];
    let next = rows.map((r, j) => j === i ? { ...r, toId, pairKey: theirKey || "" } : r)
      .filter(r => !(r.auto && r.pairOf === row.slotKey && r.slotKey === row.pairKey));
    if (theirKey) {
      const back = { slotKey: theirKey, fromId: toId, toId: current(row.slotKey, row.fromId), auto: true, pairOf: row.slotKey };
      const k = next.findIndex(r => r.slotKey === theirKey && r.fromId === toId);
      next = k >= 0 ? next.map((r, j) => j === k ? { ...r, toId: back.toId } : r) : [...next, back];
    }
    setRows(next);
  };
  // Each person's upcoming weeks in this role
  const weeksOf = id => upcoming.filter(s => inRole(rotas[s.key], role, id));
  const dayText = s => new Date(s.date).toLocaleDateString("en-GB",{weekday:"short",day:"numeric",month:"short"}) + (s.isSpecial ? " ⭐" : "");''')

# Plans from a request: link the paired week the same way
swap('''    if (req.withSlotKey) plan.push({ slotKey:req.withSlotKey, fromId: req.role === "lead" ? ((rotas[req.withSlotKey]||{}).lead||"") : (req.withId || ((rotas[req.withSlotKey]||{}).secondary||[])[0] || ""), toId:req.memberId });''',
     '''    if (req.withSlotKey) { plan.push({ slotKey:req.withSlotKey, fromId: req.role === "lead" ? ((rotas[req.withSlotKey]||{}).lead||"") : (req.withId || ((rotas[req.withSlotKey]||{}).secondary||[])[0] || ""), toId:req.memberId, auto:true, pairOf:req.slotKey }); r1.pairKey = req.withSlotKey; }''')

# Role buttons: a plan for a request keeps that request's role
swap('''              {["lead","secondary"].map(r => (
                <button key={r} onClick={()=>reset(r)}
                  className={"text-xs px-3 py-1.5 rounded-full font-semibold border "+(role===r?"bg-violet-600 text-white border-violet-600":"bg-white text-slate-600 border-slate-200")}>{r === "lead" ? "Rota Leads" : "Secondaries"}</button>
              ))}''',
     '''              {["lead","secondary"].map(r => (
                <button key={r} onClick={()=>reset(r)} disabled={linked.length > 0 && role !== r}
                  title={linked.length > 0 && role !== r ? "This request is for a "+SWAP_ROLE[role]+" — Clear the plan to swap "+(r==="lead"?"Rota Leads":"Secondaries") : ""}
                  className={"text-xs px-3 py-1.5 rounded-full font-semibold border disabled:opacity-30 "+(role===r?"bg-violet-600 text-white border-violet-600":"bg-white text-slate-600 border-slate-200")}>{r === "lead" ? "Rota Leads" : "Secondaries"}</button>
              ))}
              {linked.length > 0 && <span className="text-xs text-violet-700">Planning {SWAP_ROLE[role]} request</span>}''')

# The new-person list: each person, then their weeks to swap with
swap('''                  <select value={r.toId} onChange={e=>setRow(i, { toId:e.target.value })} disabled={!r.slotKey} className={sel}>
                    <option value="">New {SWAP_ROLE[role]}…</option>
                    {people.map(m => <option key={m.id} value={m.id}>{m.name}</option>)}
                  </select>''',
     '''                  <select value={r.toId ? r.toId+"|"+(r.pairKey||"") : ""} onChange={e=>pickPerson(i, e.target.value)} disabled={!r.slotKey || r.auto} className={sel}
                    title={r.auto ? "Filled in by the swap above" : ""}>
                    <option value="">New {SWAP_ROLE[role]}…</option>
                    {people.filter(m => m.id !== current(r.slotKey, r.fromId)).map(m => {
                      const theirs = weeksOf(m.id).filter(s => s.key !== r.slotKey);
                      return (
                        <optgroup key={m.id} label={m.name+(theirs.length ? " — "+theirs.length+" week"+(theirs.length>1?"s":"") : " — no weeks")}>
                          {theirs.map(s => <option key={s.key} value={m.id+"|"+s.key}>{m.name} ⇄ swap for {dayText(s)}</option>)}
                          <option value={m.id+"|"}>{m.name} — just takes this week</option>
                        </optgroup>
                      );
                    })}
                  </select>''')
# Auto-added weeks: a hint instead of the remove cross
swap('''                  <button onClick={()=>setRows(rows.length > 1 ? rows.filter((_, j) => j !== i) : [{ slotKey:"", fromId:"", toId:"" }])}
                    className="text-slate-400 hover:text-red-500 text-sm px-2" title="Remove this week">✕</button>''',
     '''                  <button onClick={()=>setRows(rows.length > 1 ? rows.filter((_, j) => j !== i && !(rows[j].auto && rows[j].pairOf === r.slotKey)) : [{ slotKey:"", fromId:"", toId:"" }])}
                    className="text-slate-400 hover:text-red-500 text-sm px-2" title="Remove this week">✕</button>''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
