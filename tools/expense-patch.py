"""Rota Sheet: donor contact required; expenses need payee, contact, amount and the
receiver's signature; phone cards no longer lose typing focus.

Usage: python3 tools/expense-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def swap(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


# ── 2. Helpers: contact check, ready rules, payee records, signature pad ──────
swap('''// A donation can only be taken once it has an amount above £0 and a donor name
const donationReady = db => parseFloat((db||{}).perAmount||0) > 0 && !!((db||{}).orderName||"").trim();''',
     '''// An email address, or a phone number with at least 7 digits
const validContact = c => /^\\S+@\\S+\\.\\S+$/.test((c||"").trim()) || (c||"").replace(/\\D/g,"").length >= 7;
// Donations and expenses can only be taken once they have an amount above £0, a name and a contact
const partyReady = r => parseFloat((r||{}).perAmount||0) > 0 && !!((r||{}).orderName||"").trim() && validContact((r||{}).orderContact);
const donationReady = partyReady;
// Expenses also clear the receiver's signature once paid
const NO_EXPENSE = { ...NO_DONATION, orderSig:"" };
// "Payment taken" on an expense: the receiver's signature goes on every voucher in the order
const takeExpense = ev => ({ ...ev, payees: (ev.payees||[]).map((p,i,all) => i >= all.length-(ev.orderCount||0) ? { ...p, sig: ev.orderSig } : p), ...NO_EXPENSE });

// Finger or mouse signature box; onChange gets a PNG data URL ("" when cleared)
function SignaturePad({ value, onChange, disabled }) {
  const ref = React.useRef(null);
  const last = React.useRef(null);
  React.useEffect(() => {
    const c = ref.current; if (!c) return;
    const ctx = c.getContext("2d"); ctx.clearRect(0, 0, c.width, c.height);
    if (value) { const img = new Image(); img.onload = () => ctx.drawImage(img, 0, 0); img.src = value; }
  }, [value]);
  const at = e => { const c = ref.current, r = c.getBoundingClientRect(); return [(e.clientX-r.left)*c.width/r.width, (e.clientY-r.top)*c.height/r.height]; };
  const down = e => { if (disabled) return; e.preventDefault(); ref.current.setPointerCapture(e.pointerId); last.current = at(e); };
  const move = e => {
    if (!last.current) return; e.preventDefault();
    const ctx = ref.current.getContext("2d"), p = at(e);
    ctx.beginPath(); ctx.moveTo(last.current[0], last.current[1]); ctx.lineTo(p[0], p[1]);
    ctx.strokeStyle = "#1e3a8a"; ctx.lineWidth = 3; ctx.lineCap = "round"; ctx.stroke();
    last.current = p;
  };
  const up = () => { if (!last.current) return; last.current = null; onChange(ref.current.toDataURL()); };
  return (
    <div>
      <div className={"border-2 border-dashed rounded-xl overflow-hidden "+(value?"border-emerald-300 bg-white":"border-slate-300 bg-slate-50")} style={{height:"90px"}}>
        <canvas ref={ref} width="600" height="180" style={{width:"100%",height:"100%",touchAction:"none",display:"block"}}
          onPointerDown={down} onPointerMove={move} onPointerUp={up} onPointerCancel={up}/>
      </div>
      {!disabled && value && <button onClick={()=>onChange("")} className="text-xs text-slate-400 underline mt-1">Clear signature</button>}
    </div>
  );
}''')
swap('''const addDonor = (db, no) => [...(db.donors||[]), { no, name:(db.orderName||"").trim(), contact:(db.orderContact||"").trim(),''',
     '''const addDonor = (db, no) => [...(db.donors||[]), { no, name:(db.orderName||"").trim(), contact:(db.orderContact||"").trim(),''')

# Error message now mentions the contact too
swap('"Enter the amount and donor name first"', '"Enter the amount, donor name and email or phone first"', 4)

# ── 3. Phone card: generic name/contact ("party"), optional signature ─────────
swap('''        donor=props.donor, onDonor=props.onDonor, amtLabel=props.amtLabel||"£ per entry";''',
     '''        donor=props.donor, onDonor=props.onDonor, amtLabel=props.amtLabel||"£ per entry",
        nameLabel=props.nameLabel||"Donor name *", sig=props.sig, onSig=props.onSig;''')
swap('''    // Donations need an amount and a donor name before any payment can be taken
    var ready = !donor || donationReady({perAmount:perAmt, orderName:donor.name});''',
     '''    // Donations and expenses need an amount, a name and a contact before any payment can be taken
    var ready = !donor || partyReady({perAmount:perAmt, orderName:donor.name, orderContact:donor.contact});
    var needSig = !!onSig;''')
swap('''              placeholder="Donor name *" className="w-full border''', '''              placeholder={nameLabel} className="w-full border''')
swap('''              placeholder="Email or phone" inputMode="email" className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-300 disabled:bg-slate-100"/>''',
     '''              placeholder="Email or phone *" inputMode="email" className={"w-full border rounded-lg px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-300 disabled:bg-slate-100 "+(donor.contact&&!validContact(donor.contact)?"border-red-300":"border-slate-200")}/>''')
swap('''{open ? "This order is paying by" : !ready ? "Enter the amount, donor name and email or phone first" : "1. How are they paying?"}''',
     '''{open ? "This order is paying by" : !ready ? "Enter the amount, name and email or phone first" : "1. How are they paying?"}''')
swap('''{!ready ? "amount and name needed" : orderPay''', '''{!ready ? "details needed" : orderPay''')
swap('''        {open && !isClosed && (
          <div className="px-4 pb-3">
            <button onClick={onTaken}
              className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm active:scale-[0.98] transition-transform">
              ✓ Payment taken — next order
            </button>
          </div>
        )}''',
     '''        {open && !isClosed && needSig && (
          <div className="px-4 pb-2">
            <div className="text-xs font-semibold text-slate-500 mb-1">✍️ Receiver's signature *</div>
            <SignaturePad value={sig} onChange={onSig}/>
          </div>
        )}
        {open && !isClosed && (
          <div className="px-4 pb-3">
            <button onClick={onTaken} disabled={needSig && !sig}
              className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm active:scale-[0.98] transition-transform disabled:opacity-40">
              {needSig && !sig ? "Receiver signs above first" : needSig ? "✓ Paid — next expense" : "✓ Payment taken — next order"}
            </button>
          </div>
        )}''')
swap('''            {props.donors.map(function(d){return (
              <div key={d.no} className="text-xs text-slate-600 flex gap-2"><span className="font-mono text-slate-400">{d.no}</span><span className="flex-1 truncate">{d.name}</span><span className="font-semibold">£{d.amount}</span><span>{(PAY_LABEL[d.pay]||"").split(" ")[0]}</span></div>
            );})}''',
     '''            {props.donors.map(function(d){return (
              <div key={d.no} className="text-xs text-slate-600 flex items-center gap-2"><span className="font-mono text-slate-400">{d.no}</span><span className="flex-1 truncate">{d.name}</span><span className="font-semibold">£{d.amount}</span><span>{(PAY_LABEL[d.pay]||"").split(" ")[0]}</span>{d.sig && <img src={d.sig} alt="signed" className="h-5 border border-slate-200 rounded bg-white"/>}</div>
            );})}''')

# ── 4. Phone: expense counters and card ───────────────────────────────────────
swap('''    var ev = s.expenseVouchers||{};
    if (!ev.orderPay) return showToast("Choose Cash, Card or Online first","error");''',
     '''    var ev = s.expenseVouchers||{};
    if (!partyReady(ev)) return showToast("Enter the amount, paid to and email or phone first","error");
    if (!ev.orderPay) return showToast("Choose Cash, Card or Online first","error");''')
swap('''    up({expenseVouchers:{...ev,count:newCnt,end:newEnd,firstNum,...orderMoney(ev,parseFloat(ev.perAmount||0),1)}});''',
     '''    up({expenseVouchers:{...ev,count:newCnt,end:newEnd,firstNum,payees:addDonor({...ev,donors:ev.payees},newEnd),...orderMoney(ev,parseFloat(ev.perAmount||0),1)}});''')
swap('''    up({expenseVouchers:{...ev,count:newCnt,end:newEnd,...orderMoney(ev,parseFloat(ev.perAmount||0),-1)}});''',
     '''    up({expenseVouchers:{...ev,count:newCnt,end:newEnd,payees:dropDonor({donors:ev.payees},ev.end),...orderMoney(ev,parseFloat(ev.perAmount||0),-1)}});''')
swap('''        onPayType={function(p){up({expenseVouchers:{...ev,orderPay:p}});}}
        onTaken={function(){up({expenseVouchers:{...ev,...NO_ORDER}});}}''',
     '''        onPayType={function(p){up({expenseVouchers:{...ev,orderPay:p}});}}
        onTaken={function(){up({expenseVouchers:takeExpense(ev)});}}
        amtLabel="Amount £" nameLabel="Paid to (name or company) *" donors={ev.payees}
        donor={{name:ev.orderName, contact:ev.orderContact}}
        onDonor={function(f,v){up({expenseVouchers:{...ev,[f]:v}});}}
        sig={ev.orderSig} onSig={function(v){up({expenseVouchers:{...ev,orderSig:v}});}}''')

# ── 5. Full form: donation contact, expense details ───────────────────────────
swap('''placeholder="Email or phone"
                          onChange={e=>up({donationBook:{...db,orderContact:e.target.value}})} className={cls}/>''',
     '''placeholder="Email or phone *"
                          onChange={e=>up({donationBook:{...db,orderContact:e.target.value}})} className={cls}/>''')
swap('''    const ev       = s.expenseVouchers;
    if (!ev.orderPay) return showToast("Choose Cash, Card or Online first", "error");''',
     '''    const ev       = s.expenseVouchers;
    if (!partyReady(ev)) return showToast("Enter the amount, paid to and email or phone first", "error");
    if (!ev.orderPay) return showToast("Choose Cash, Card or Online first", "error");''')
swap('''    up({ expenseVouchers: { ...ev, count: newCnt, end: newEnd, firstNum, ...orderMoney(ev, parseFloat(ev.perAmount||0), 1) } });''',
     '''    up({ expenseVouchers: { ...ev, count: newCnt, end: newEnd, firstNum, payees: addDonor({ ...ev, donors: ev.payees }, newEnd), ...orderMoney(ev, parseFloat(ev.perAmount||0), 1) } });''')
swap('''    up({ expenseVouchers: { ...ev, count: newCnt, end: newEnd, ...orderMoney(ev, parseFloat(ev.perAmount||0), -1) } });''',
     '''    up({ expenseVouchers: { ...ev, count: newCnt, end: newEnd, payees: dropDonor({ donors: ev.payees }, ev.end), ...orderMoney(ev, parseFloat(ev.perAmount||0), -1) } });''')
swap('''                  <div className="font-semibold text-sm text-amber-800">🧾 Expense Vouchers</div>
                </div>''',
     '''                  <div className="font-semibold text-sm text-amber-800">🧾 Expense Vouchers</div>
                  {!isClosed && (() => {
                    const ev = s.expenseVouchers||{};
                    const locked = ev.orderCount > 0;
                    const cls = "w-full border border-slate-200 rounded-lg px-2 py-1 text-xs bg-white focus:outline-none focus:ring-2 focus:ring-amber-200 disabled:bg-slate-100 disabled:text-slate-500";
                    return (
                      <div className="mt-1.5 space-y-1">
                        <input value={ev.orderName||""} disabled={locked} placeholder="Paid to (name or company) *"
                          onChange={e=>up({expenseVouchers:{...ev,orderName:e.target.value}})} className={cls}/>
                        <input value={ev.orderContact||""} disabled={locked} placeholder="Email or phone *"
                          onChange={e=>up({expenseVouchers:{...ev,orderContact:e.target.value}})} className={cls}/>
                        {locked && (
                          <div>
                            <div className="text-xs font-semibold text-slate-500 mt-1">✍️ Receiver's signature *</div>
                            <SignaturePad value={ev.orderSig} onChange={v=>up({expenseVouchers:{...ev,orderSig:v}})}/>
                          </div>
                        )}
                      </div>
                    );
                  })()}
                  {(s.expenseVouchers?.payees||[]).length > 0 && (
                    <div className="mt-1.5 text-xs text-slate-500 space-y-0.5">
                      {s.expenseVouchers.payees.map(d => <div key={d.no} className="flex items-center gap-1.5">{d.no} · {d.name} · {d.contact} · £{d.amount} · {PAY_LABEL[d.pay]||d.pay}{d.sig && <img src={d.sig} alt="signed" className="h-5 border border-slate-200 rounded bg-white"/>}</div>)}
                    </div>
                  )}
                </div>''')
swap('''<button onClick={incrExpense} disabled={!s.expenseVouchers?.orderPay} title={s.expenseVouchers?.orderPay?"":"Choose Cash, Card or Online first"}''',
     '''<button onClick={incrExpense} disabled={!s.expenseVouchers?.orderPay||!partyReady(s.expenseVouchers)} title={!partyReady(s.expenseVouchers)?"Enter the amount, paid to and email or phone first":s.expenseVouchers?.orderPay?"":"Choose Cash, Card or Online first"}''')
swap('''                        <select value={r.orderPay||""} disabled={open} onChange={e=>up({expenseVouchers:{...r,orderPay:e.target.value}})}''',
     '''                        <select value={r.orderPay||""} disabled={open||!partyReady(r)} onChange={e=>up({expenseVouchers:{...r,orderPay:e.target.value}})}''')
swap('''                          <button onClick={()=>up({expenseVouchers:{...r,...NO_ORDER}})}
                            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg px-1 py-1 text-xs font-bold">✓ Taken ({r.orderCount})</button>''',
     '''                          <button onClick={()=>up({expenseVouchers:takeExpense(r)})} disabled={!r.orderSig} title={r.orderSig?"":"The receiver signs first"}
                            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg px-1 py-1 text-xs font-bold disabled:opacity-40">✓ Paid ({r.orderCount})</button>''')
swap('''                      placeholder="£ each"
                      className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm text-right font-semibold focus:outline-none focus:ring-2 focus:ring-amber-200 bg-white"/>''',
     '''                      placeholder="£ amount *"
                      className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm text-right font-semibold focus:outline-none focus:ring-2 focus:ring-amber-200 bg-white disabled:bg-slate-100"/>''')

# ── 1. Hoist the phone register card out of RotaSheetMobile ───────────────────
# Defined inside the component it was a new component type on every render, so
# React rebuilt it after each keystroke and the phone keyboard dropped out.
start = s.index("  // ── Payment type selector ──")
end = s.index("  // ── Reconciliation helpers (same as RotaSheetForm)")
block = s[start:end]
s = s[:start] + s[end:]
block = block.replace("  var RegCard = function(props) {", "  var RegCard = function(props) {\n    var isClosed=props.isClosed;", 1)
assert block.rstrip().endswith("};")
block = block.rstrip()[:-2] + "}\n"
block = "\n".join(l[2:] if l.startswith("  ") else l for l in block.split("\n"))
block = block.replace("var RegCard = function(props) {", "function SheetRegCard(props) {", 1)
block = block.replace("// ── Payment type selector ──", "// ── Rota Sheet (phone): payment type selector ──", 1)
swap("function RotaSheetMobile(", block + "\nfunction RotaSheetMobile(")
swap("      <RegCard\n", "      <SheetRegCard isClosed={isClosed}\n", 3)

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
