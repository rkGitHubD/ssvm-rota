"""Rota Sheet donations: amount + donor name (and optional email/phone) before payment.

Cash/Card/Online and + stay disabled until the amount is above £0 and a donor name
is entered. While the order is open the amount, name and contact are locked; after
"Payment taken" they clear for the next donor. Each receipt is recorded in
donationBook.donors.

Usage: python3 tools/donor-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def swap(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


# ── Shared helpers ────────────────────────────────────────────────────────────
swap('''const NO_ORDER = { orderPay:"", orderCount:0 };''',
     '''const NO_ORDER = { orderPay:"", orderCount:0 };
// Donations also clear the amount and donor once paid, ready for the next donor
const NO_DONATION = { ...NO_ORDER, perAmount:"", orderName:"", orderContact:"" };
// A donation can only be taken once it has an amount above £0 and a donor name
const donationReady = db => parseFloat((db||{}).perAmount||0) > 0 && !!((db||{}).orderName||"").trim();
// One receipt per + : who gave, how much and how
const addDonor = (db, no) => [...(db.donors||[]), { no, name:(db.orderName||"").trim(), contact:(db.orderContact||"").trim(),
  amount:parseFloat(db.perAmount||0).toFixed(2), pay:db.orderPay, at:new Date().toISOString() }];
const dropDonor = (db, no) => (db.donors||[]).filter(d => d.no !== no);''')

# ── Full form: counters ───────────────────────────────────────────────────────
swap('''    const db       = s.donationBook;
    if (!db.orderPay) return showToast("Choose Cash, Card or Online first", "error");
    const prefix   = donationReg ? (donationReg.prefix || "D") : "D";
    const firstNum = db.firstNum || parseInt((db.start||"").replace(/\\D/g,"")) + 1 || 1;
    const newCnt   = (parseInt(db.count||0)) + 1;
    const newEnd   = fmtRegNum(prefix, firstNum + newCnt - 1);
    up({ donationBook: { ...db, count: newCnt, end: newEnd, firstNum, ...orderMoney(db, parseFloat(db.perAmount||0), 1) } });''',
     '''    const db       = s.donationBook;
    if (!donationReady(db)) return showToast("Enter the amount and donor name first", "error");
    if (!db.orderPay) return showToast("Choose Cash, Card or Online first", "error");
    const prefix   = donationReg ? (donationReg.prefix || "D") : "D";
    const firstNum = db.firstNum || parseInt((db.start||"").replace(/\\D/g,"")) + 1 || 1;
    const newCnt   = (parseInt(db.count||0)) + 1;
    const newEnd   = fmtRegNum(prefix, firstNum + newCnt - 1);
    up({ donationBook: { ...db, count: newCnt, end: newEnd, firstNum, donors: addDonor(db, newEnd), ...orderMoney(db, parseFloat(db.perAmount||0), 1) } });''')
swap('''    const newEnd   = newCnt > 0 ? fmtRegNum(prefix, firstNum + newCnt - 1) : db.start;
    up({ donationBook: { ...db, count: newCnt, end: newEnd, ...orderMoney(db, parseFloat(db.perAmount||0), -1) } });''',
     '''    const newEnd   = newCnt > 0 ? fmtRegNum(prefix, firstNum + newCnt - 1) : db.start;
    up({ donationBook: { ...db, count: newCnt, end: newEnd, donors: dropDonor(db, db.end), ...orderMoney(db, parseFloat(db.perAmount||0), -1) } });''')

# ── Full form: donation row ───────────────────────────────────────────────────
swap('''                  <div className="font-semibold text-sm text-blue-800">📖 Donation Book</div>
                </div>''',
     '''                  <div className="font-semibold text-sm text-blue-800">📖 Donation Book</div>
                  {!isClosed && (() => {
                    const db = s.donationBook||{};
                    const locked = db.orderCount > 0;
                    const cls = "w-full border border-slate-200 rounded-lg px-2 py-1 text-xs bg-white focus:outline-none focus:ring-2 focus:ring-blue-200 disabled:bg-slate-100 disabled:text-slate-500";
                    return (
                      <div className="mt-1.5 space-y-1">
                        <input value={db.orderName||""} disabled={locked} placeholder="Donor name *"
                          onChange={e=>up({donationBook:{...db,orderName:e.target.value}})} className={cls}/>
                        <input value={db.orderContact||""} disabled={locked} placeholder="Email or phone"
                          onChange={e=>up({donationBook:{...db,orderContact:e.target.value}})} className={cls}/>
                      </div>
                    );
                  })()}
                  {(s.donationBook?.donors||[]).length > 0 && (
                    <div className="mt-1.5 text-xs text-slate-500 space-y-0.5">
                      {s.donationBook.donors.map(d => <div key={d.no}>{d.no} · {d.name} · £{d.amount} · {PAY_LABEL[d.pay]||d.pay}</div>)}
                    </div>
                  )}
                </div>''')
swap('''<button onClick={incrDonation} disabled={!s.donationBook?.orderPay} title={s.donationBook?.orderPay?"":"Choose Cash, Card or Online first"}''',
     '''<button onClick={incrDonation} disabled={!s.donationBook?.orderPay||!donationReady(s.donationBook)} title={!donationReady(s.donationBook)?"Enter the amount and donor name first":s.donationBook?.orderPay?"":"Choose Cash, Card or Online first"}''')
# Payment type: needs amount + name; "Taken" clears the donor too
swap('''                        <select value={r.orderPay||""} disabled={open} onChange={e=>up({donationBook:{...r,orderPay:e.target.value}})}''',
     '''                        <select value={r.orderPay||""} disabled={open||!donationReady(r)} onChange={e=>up({donationBook:{...r,orderPay:e.target.value}})}''')
swap('''                          <button onClick={()=>up({donationBook:{...r,...NO_ORDER}})}''',
     '''                          <button onClick={()=>up({donationBook:{...r,...NO_DONATION}})}''')
swap('''                      placeholder="£ each"
                      className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm text-right font-semibold focus:outline-none focus:ring-2 focus:ring-blue-200 bg-white"/>''',
     '''                      placeholder="£ amount *"
                      className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm text-right font-semibold focus:outline-none focus:ring-2 focus:ring-blue-200 bg-white disabled:bg-slate-100"/>''')

# ── Mobile: counters ──────────────────────────────────────────────────────────
swap('''    var db = s.donationBook||{};
    if (!db.orderPay) return showToast("Choose Cash, Card or Online first","error");''',
     '''    var db = s.donationBook||{};
    if (!donationReady(db)) return showToast("Enter the amount and donor name first","error");
    if (!db.orderPay) return showToast("Choose Cash, Card or Online first","error");''')
swap('''    up({donationBook:{...db,count:newCnt,end:newEnd,firstNum,...orderMoney(db,parseFloat(db.perAmount||0),1)}});''',
     '''    up({donationBook:{...db,count:newCnt,end:newEnd,firstNum,donors:addDonor(db,newEnd),...orderMoney(db,parseFloat(db.perAmount||0),1)}});''')
swap('''    up({donationBook:{...db,count:newCnt,end:newEnd,...orderMoney(db,parseFloat(db.perAmount||0),-1)}});''',
     '''    up({donationBook:{...db,count:newCnt,end:newEnd,donors:dropDonor(db,db.end),...orderMoney(db,parseFloat(db.perAmount||0),-1)}});''')

# ── Mobile: register card ─────────────────────────────────────────────────────
swap('''        onPerAmt=props.onPerAmt, onTaken=props.onTaken, priceNow=parseFloat(props.price||0);
    var open = orderCount > 0;''',
     '''        onPerAmt=props.onPerAmt, onTaken=props.onTaken, priceNow=parseFloat(props.price||0),
        donor=props.donor, onDonor=props.onDonor, amtLabel=props.amtLabel||"£ per entry";
    var open = orderCount > 0;
    // Donations need an amount and a donor name before any payment can be taken
    var ready = !donor || donationReady({perAmount:perAmt, orderName:donor.name});''')
swap('''            <span className="text-xs text-slate-500 w-20 flex-shrink-0">£ per entry</span>''',
     '''            <span className="text-xs text-slate-500 w-20 flex-shrink-0">{amtLabel}</span>''')
swap('''        {/* 1. Payment type for this order — locked once something is added */}
        <div className="px-4 pb-1 text-xs font-semibold text-slate-500">{open ? "This order is paying by" : "1. How are they paying?"}</div>''',
     '''        {donor && (
          <div className="px-4 pb-2 space-y-1.5">
            <input value={donor.name||""} onChange={function(e){onDonor("orderName",e.target.value);}} disabled={isClosed||open}
              placeholder="Donor name *" className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-300 disabled:bg-slate-100"/>
            <input value={donor.contact||""} onChange={function(e){onDonor("orderContact",e.target.value);}} disabled={isClosed||open}
              placeholder="Email or phone" inputMode="email" className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-300 disabled:bg-slate-100"/>
          </div>
        )}
        {/* 1. Payment type for this order — locked once something is added */}
        <div className="px-4 pb-1 text-xs font-semibold text-slate-500">{open ? "This order is paying by" : !ready ? "Enter the amount and donor name first" : "1. How are they paying?"}</div>''')
swap('''<button key={p} onClick={function(){onPayType&&onPayType(p);}} disabled={isClosed||(open&&!on)}''',
     '''<button key={p} onClick={function(){onPayType&&onPayType(p);}} disabled={isClosed||(open&&!on)||!ready}''')
swap('''          <button onClick={onIncr} disabled={isClosed||!orderPay}''',
     '''          <button onClick={onIncr} disabled={isClosed||!orderPay||!ready}''')
swap('''            <div className="text-xs text-slate-400">{orderPay ? "in this order"''',
     '''            <div className="text-xs text-slate-400">{!ready ? "amount and name needed" : orderPay ? "in this order"''')
# Today's donors under the card
swap('''        <div className="px-4 pb-2 text-xs text-slate-500">Today so far: <b>{count}</b> {startNum && endNum && count>0 ? "("+startNum+" → "+endNum+")" : ""}</div>''',
     '''        <div className="px-4 pb-2 text-xs text-slate-500">Today so far: <b>{count}</b> {startNum && endNum && count>0 ? "("+startNum+" → "+endNum+")" : ""}</div>
        {(props.donors||[]).length > 0 && (
          <div className="px-4 pb-2 space-y-0.5">
            {props.donors.map(function(d){return (
              <div key={d.no} className="text-xs text-slate-600 flex gap-2"><span className="font-mono text-slate-400">{d.no}</span><span className="flex-1 truncate">{d.name}</span><span className="font-semibold">£{d.amount}</span><span>{(PAY_LABEL[d.pay]||"").split(" ")[0]}</span></div>
            );})}
          </div>
        )}''')

# Donations card props
swap('''        onPayType={function(p){up({donationBook:{...db,orderPay:p}});}}
        onTaken={function(){up({donationBook:{...db,...NO_ORDER}});}}''',
     '''        onPayType={function(p){up({donationBook:{...db,orderPay:p}});}}
        onTaken={function(){up({donationBook:{...db,...NO_DONATION}});}}
        amtLabel="Amount £" donors={db.donors}
        donor={{name:db.orderName, contact:db.orderContact}}
        onDonor={function(f,v){up({donationBook:{...db,[f]:v}});}}''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
