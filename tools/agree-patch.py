"""Generated rota needs members' agreement:
- generator renamed "Generate a new rota for next year"; warns before generating again
- Rota calendar shows assigned-but-not-agreed days as TBC (amber), not green
- members agree to their weeks from My Requests (badge counts weeks waiting)

Usage: python3 tools/agree-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def swap(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


# ── Generator: name and warning before generating again ───────────────────────
swap('''<div className="font-semibold text-slate-800">Generate rota for next year</div>''',
     '''<div className="font-semibold text-slate-800">Generate a new rota for next year</div>''')
swap('''  const generate = () => {''', '''  // Generating again replaces what's saved (and members' agreements) once the new draft is saved
  const [askRegen, setAskRegen] = useState(false);
  const savedDays = days().filter(d => (rotas[d.key]||{}).lead || (rotas[d.key]||{}).committee || ((rotas[d.key]||{}).secondary||[]).length);
  const agreedDays = savedDays.filter(d => { const r = rotas[d.key]; return (r.lead && r.leadConfirmed !== false) || (r.secondary||[]).length && r.secondaryConfirmed !== false; });
  const tryGenerate = () => { if (savedDays.length || plan) setAskRegen(true); else generate(); };
  const generate = () => {
    setAskRegen(false);''')
swap('''          <button onClick={generate} disabled={leads.length + secs.length === 0}
            className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded-xl text-sm font-bold disabled:opacity-40">{plan ? "↻ Generate again" : "Generate "+year+" rota"}</button>''',
     '''          {askRegen ? (
            <div className="border border-amber-300 bg-amber-50 rounded-xl p-3 space-y-2">
              <p className="text-sm text-amber-800">
                {savedDays.length > 0 && <><b>A {year} rota is already saved</b> — {savedDays.length} days assigned{agreedDays.length ? ", "+agreedDays.length+" already agreed" : ""}. A new draft replaces it, and members' agreements, when you save it. </>}
                {plan && <>Your changes to the current draft will be lost. </>}
                Generate a new draft?
              </p>
              <div className="flex gap-2">
                <button onClick={generate} className="bg-amber-600 hover:bg-amber-700 text-white px-4 py-2 rounded-lg text-sm font-bold">Yes, generate a new draft</button>
                <button onClick={()=>setAskRegen(false)} className="text-sm text-slate-600 px-3">Cancel</button>
              </div>
            </div>
          ) : (
            <button onClick={tryGenerate} disabled={leads.length + secs.length === 0}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2 rounded-xl text-sm font-bold disabled:opacity-40">{plan ? "↻ Generate again" : "Generate "+year+" rota"}</button>
          )}''')
swap('''<p className="text-xs text-slate-400">Saved weeks show as <b>TBC</b> on the schedule until confirmed (tick "Confirmed" when you open a week below).''',
     '''<p className="text-xs text-slate-400">Saved weeks show as <b>TBC</b> until each member agrees to their week (from My Requests), or you tick "Confirmed" when you open a week below.''')

# ── Rota calendar: assigned but not yet agreed = TBC (amber) ──────────────────
swap('''          const filled   = slot ? !!rotas[slot.key]?.lead : false;''',
     '''          const filled   = slot ? !!rotas[slot.key]?.lead : false;
          const tbc      = filled && rotas[slot.key].leadConfirmed === false;   // assigned, not yet agreed''')
swap('''            else if (filled) cellCls += " bg-emerald-100 text-emerald-800 hover:bg-emerald-200";''',
     '''            else if (tbc)    cellCls += " bg-amber-100 text-amber-800 hover:bg-amber-200";
            else if (filled) cellCls += " bg-emerald-100 text-emerald-800 hover:bg-emerald-200";''')
swap('''            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-emerald-400 inline-block"></span>Filled</span>''',
     '''            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-emerald-400 inline-block"></span>Filled</span>
            <span className="flex items-center gap-1"><span className="w-3 h-3 rounded-full bg-amber-400 inline-block"></span>TBC</span>''')
swap('''                const filled   = r?.lead;''', '''                const filled   = r?.lead;
                const tbc      = filled && r.leadConfirmed === false;   // assigned, not yet agreed''')
swap('''                else if (s && filled)      bg = "bg-emerald-50";''', '''                else if (s && tbc)         bg = "bg-amber-50";
                else if (s && filled)      bg = "bg-emerald-50";''')
swap(''': filled  ? "bg-emerald-500" : "bg-red-400";''', ''': tbc ? "bg-amber-400" : filled  ? "bg-emerald-500" : "bg-red-400";''')
swap('''Lead assigned</span>''', '''Lead agreed</span>
              <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full md:rounded-sm bg-amber-400 md:bg-amber-100 md:border md:border-amber-300 inline-block"/>TBC — awaiting agreement</span>''')
swap('''                {rota.lead
                  ? <div className="text-xs bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2 mb-2 font-semibold text-emerald-700">🎯 {name(rota.lead)}</div>''',
     '''                {rota.lead && rota.leadConfirmed === false
                  ? <div className="text-xs bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-2 font-semibold text-amber-700">🎯 {name(rota.lead)} · TBC</div>
                  : rota.lead
                  ? <div className="text-xs bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2 mb-2 font-semibold text-emerald-700">🎯 {name(rota.lead)}</div>''')
swap('''<InfoPill label="Rota Lead" value={selRota.committee ? "Committee" : selRota.lead ? getName(selRota.lead) : "Not assigned"} filled={!!selRota.lead || !!selRota.committee} icon="🎯"/>''',
     '''<InfoPill label="Rota Lead" value={selRota.committee ? "Committee" : selRota.lead ? getName(selRota.lead) + (selRota.leadConfirmed === false ? " · TBC" : "") : "Not assigned"} filled={(!!selRota.lead && selRota.leadConfirmed !== false) || !!selRota.committee} icon="🎯"/>''')

# ── Members agree to their weeks ──────────────────────────────────────────────
AGREE = r'''// ─── My weeks waiting for agreement (a generated rota starts as TBC) ──────────
function myUnagreedWeeks(rotas, allSlots, me) {
  const today = new Date(); today.setHours(0,0,0,0);
  return allSlots.filter(s => new Date(s.date) >= today).flatMap(s => {
    const r = rotas[s.key] || {};
    return [r.lead === me && r.leadConfirmed === false ? { slot:s, role:"lead" } : null,
            (r.secondary||[]).includes(me) && r.secondaryConfirmed === false ? { slot:s, role:"secondary" } : null].filter(Boolean);
  });
}
function AgreeMyWeeks({ rotas, upRotas, allSlots, currentUser, showToast }) {
  const weeks = myUnagreedWeeks(rotas, allSlots, currentUser.memberId);
  if (!weeks.length) return null;
  const agree = list => {
    const next = { ...rotas };
    list.forEach(w => { next[w.slot.key] = { ...next[w.slot.key], [w.role === "lead" ? "leadConfirmed" : "secondaryConfirmed"]: true }; });
    upRotas(next);
    showToast("Thank you — " + list.length + " week" + (list.length > 1 ? "s" : "") + " confirmed");
  };
  return (
    <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 space-y-3">
      <div className="flex items-start gap-3">
        <span className="text-2xl">🗓</span>
        <div className="flex-1">
          <h3 className="font-bold text-amber-800 text-sm">Please confirm your rota weeks</h3>
          <p className="text-xs text-amber-700 mt-0.5">You've been given these weeks. Agree to each one, or ask for a swap below if you can't make it.</p>
        </div>
        {weeks.length > 1 && <button onClick={()=>agree(weeks)} className="text-xs bg-emerald-600 text-white px-3 py-1.5 rounded-lg font-bold whitespace-nowrap">✓ Agree to all</button>}
      </div>
      <div className="divide-y divide-amber-100 bg-white rounded-xl border border-amber-100">
        {weeks.map(w => (
          <div key={w.slot.key+w.role} className="flex items-center gap-3 px-3 py-2 text-sm">
            <span className="flex-1">{slotText(w.slot)} <span className="text-xs text-slate-500">as {SWAP_ROLE[w.role]}</span></span>
            <button onClick={()=>agree([w])} className="text-xs bg-emerald-50 border border-emerald-200 text-emerald-700 px-3 py-1 rounded-lg font-semibold">✓ I agree</button>
          </div>
        ))}
      </div>
    </div>
  );
}

'''
swap("function VolunteerRequests(", AGREE + "function VolunteerRequests(")
swap('''      <SwapRequestForm rotas={rotas} allSlots={allSlots} members={members} generalOffers={generalOffers} upGeneralOffers={upGeneralOffers} currentUser={currentUser} showToast={showToast}/>''',
     '''      <AgreeMyWeeks rotas={rotas} upRotas={upRotas} allSlots={allSlots} currentUser={currentUser} showToast={showToast}/>
      <SwapRequestForm rotas={rotas} allSlots={allSlots} members={members} generalOffers={generalOffers} upGeneralOffers={upGeneralOffers} currentUser={currentUser} showToast={showToast}/>''')
# Badge on Volunteer / My Requests counts weeks waiting for agreement
swap('''    return s + hwCount;
  }, 0) : 0;''', '''    return s + hwCount;
  }, 0) + myUnagreedWeeks(rotas, allSlots, currentUser.memberId).length : 0;''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
