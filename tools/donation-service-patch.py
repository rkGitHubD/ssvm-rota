"""Rota Sheet:
- registers show only the next number to issue
- laptop: Donations and Expenses as side-by-side cards (details first, then payment)
- Services row removed; donations choose "General" or a service (price fills the amount)
- donations take a date; service donors show as sponsors on that day, tagged "service paid"
- card totals include expenses paid by card

Usage: python3 tools/donation-service-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def swap(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


def cut(start, end):
    """Remove text from `start` (inclusive) up to `end` (exclusive)."""
    global s
    assert s.count(start) == 1, start
    i = s.index(start)
    j = s.index(end, i)
    s = s[:i] + s[j:]


# ── Helpers ───────────────────────────────────────────────────────────────────
swap('''const NO_DONATION = { ...NO_ORDER, perAmount:"", orderName:"", orderContact:"" };''',
     '''const NO_DONATION = { ...NO_ORDER, perAmount:"", orderName:"", orderContact:"", orderServiceId:"", orderServiceName:"", orderDate:"" };
// The next receipt number a register will issue
const nextRegNum = (r, prefix, count) => fmtRegNum(prefix, ((r||{}).firstNum || parseInt(((r||{}).start||"").replace(/\\D/g,"")) + 1 || 1) + (parseInt(count)||0));
// Donation record: what it was for (General or a service) and the date it's for
const addDonation = (db, no, sheetDate) => addDonor(db, no)
  .map((p, i, all) => i === all.length-1 ? { ...p, purpose: db.orderServiceName || "General", serviceId: db.orderServiceId || "", date: db.orderDate || sheetDate } : p);
// Donors who paid for a service to be done on `date`, from every Rota Sheet's donation book
const servicePaidOn = (sheets, date) => (sheets||[]).flatMap(sh => (sh.donationBook||{}).donors||[])
  .filter(d => d.serviceId && d.date === date)
  .map(d => ({ id: d.no+d.at, donor: d.name, area: d.purpose+" · service paid" }));''')

# ── Phone card: next number, service choice, donation date ────────────────────
swap('''          {startNum && <span className="text-xs text-slate-400 ml-2">{startNum}{endNum&&endNum!==startNum?" → "+endNum:""}</span>}''',
     '''          {props.nextNum && !isClosed && <span className="text-xs text-slate-500 ml-2">Next: <b className="font-mono">{props.nextNum}</b></span>}''')
swap('''      <div className="px-4 pb-2 text-xs text-slate-500">Today so far: <b>{count}</b> {startNum && endNum && count>0 ? "("+startNum+" → "+endNum+")" : ""}</div>''',
     '''      <div className="px-4 pb-2 text-xs text-slate-500">Today so far: <b>{count}</b></div>''')
swap('''      {/* Per-amount field (not for archana, which uses the Normal/Special price) */}''',
     '''      {/* Donations: General or one of the services (its price fills the amount) */}
      {props.services && (
        <div className="px-4 pb-2 flex items-center gap-2">
          <span className="text-xs text-slate-500 w-20 flex-shrink-0">Donation for</span>
          <select value={props.serviceId||""} disabled={isClosed||open} onChange={function(e){props.onService(props.services.find(function(sv){return sv.id===e.target.value;})||null);}}
            className="flex-1 min-w-0 border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-300 disabled:bg-slate-100">
            <option value="">General donation</option>
            {props.services.map(function(sv){return <option key={sv.id} value={sv.id}>{sv.name} — £{sv.charge}</option>;})}
          </select>
        </div>
      )}
      {/* Per-amount field (not for archana, which uses the Normal/Special price) */}''')
swap('''          {expense && (''',
     '''          {props.donationDate !== undefined && (
            <label className="flex items-center gap-2">
              <span className="text-xs text-slate-500 whitespace-nowrap flex-shrink-0">{props.serviceId ? "Service date *" : "Date *"}</span>
              <input type="date" value={props.donationDate} onChange={function(e){onDonor("orderDate",e.target.value);}} disabled={isClosed||open}
                className="flex-1 min-w-0 border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-300 disabled:bg-slate-100"/>
            </label>
          )}
          {expense && (''')

# ── Phone sheet: wire up the cards ────────────────────────────────────────────
swap('''function RotaSheetMobile({ sheet, upSheet, onBack, archanaiReg, donationReg, expenseReg, upRegs, registers, showToast, cashInHand, upCashInHand, isAdmin, onFullForm }) {''',
     '''function RotaSheetMobile({ sheet, upSheet, onBack, archanaiReg, donationReg, expenseReg, upRegs, registers, showToast, cashInHand, upCashInHand, isAdmin, onFullForm, sevas=[] }) {''')
swap('''<RotaSheetMobile sheet={currentSheet} upSheet={upSheet}''', '''<RotaSheetMobile sevas={sevas||[]} sheet={currentSheet} upSheet={upSheet}''')
swap('''donors:addDonor(db,newEnd)''', '''donors:addDonation(db,newEnd,s.date)''')
swap('''        orderPay={at.orderPay} orderCount={at.orderCount} price={at.dayType==="special"?5:3}''',
     '''        orderPay={at.orderPay} orderCount={at.orderCount} price={at.dayType==="special"?5:3}
        nextNum={nextRegNum(at, archanaiReg ? (archanaiReg.prefix||"A") : "A", at.ticketCount)}''')
swap('''        orderPay={db.orderPay} orderCount={db.orderCount} price={db.perAmount} perAmt={db.perAmount||""}''',
     '''        orderPay={db.orderPay} orderCount={db.orderCount} price={db.perAmount} perAmt={db.perAmount||""}
        nextNum={nextRegNum(db, donationReg ? (donationReg.prefix||"D") : "D", db.count)}
        services={sevas} serviceId={db.orderServiceId} donationDate={db.orderDate||s.date}
        onService={function(sv){up({donationBook:{...db,orderServiceId:sv?sv.id:"",orderServiceName:sv?sv.name:"",perAmount:sv?sv.charge:db.perAmount}});}}''')
swap('''        orderPay={ev.orderPay} orderCount={ev.orderCount} price={ev.perAmount} perAmt={ev.perAmount||""}''',
     '''        orderPay={ev.orderPay} orderCount={ev.orderCount} price={ev.perAmount} perAmt={ev.perAmount||""}
        nextNum={nextRegNum(ev, expenseReg ? (expenseReg.prefix||"E") : "E", ev.count)}''')

# ── Full form: donation records ───────────────────────────────────────────────
swap('''donors: addDonor(db, newEnd)''', '''donors: addDonation(db, newEnd, s.date)''')

# ── Full form: Sponsors line includes service donors; Services row removed ────
swap('''function RotaSheetForm({ onPhoneView, sheet,''', '''function RotaSheetForm({ rotaSheets=[], onPhoneView, sheet,''')
swap('''<RotaSheetForm onPhoneView=''', '''<RotaSheetForm rotaSheets={rotaSheets} onPhoneView=''')
swap('''                    .map(don => ({ id: don.id, donor: don.donor, area: area.name }))
                );''',
     '''                    .map(don => ({ id: don.id, donor: don.donor, area: area.name }))
                ).concat(servicePaidOn(rotaSheets, sheetDate));''')
cut('''                    {/* Services row */}''', '''                    {/* Inventory low-stock warning */}''')

# ── Full form: table shows only the next number; Donation/Expense rows move out
OLD_COLS = '''gridTemplateColumns:"3fr 1fr 1fr 1fr 1.2fr 1.2fr"'''
NEW_COLS = '''gridTemplateColumns:"3fr 1.2fr 1fr 1.2fr 1.2fr"'''
swap('''                <div className="px-2 py-2 text-center">Start</div>
                <div className="px-2 py-2 text-center">End</div>''',
     '''                <div className="px-2 py-2 text-center">Next No.</div>''')
# Opening balance and Hundi: one empty cell fewer
swap('''                    <div className="px-2 py-2.5"></div>
                    <div className="px-2 py-2.5"></div>
                    <div className="px-2 py-2.5"></div>
                    <div className="px-2 py-2.5"></div>''',
     '''                    <div className="px-2 py-2.5"></div>
                    <div className="px-2 py-2.5"></div>
                    <div className="px-2 py-2.5"></div>''')
swap('''                <div className="px-2 py-3"></div>
                <div className="px-2 py-3"></div>
                <div className="px-2 py-3"></div>
                <div className="px-2 py-3"></div>''',
     '''                <div className="px-2 py-3"></div>
                <div className="px-2 py-3"></div>
                <div className="px-2 py-3"></div>''')
swap('''                <div className="px-2 py-3 text-center">
                  <span className="font-mono font-bold text-violet-600 text-sm bg-violet-100 bg-opacity-60 px-1.5 py-0.5 rounded">{s.archanaTickets?.start||"—"}</span>
                </div>
                <div className="px-2 py-3 text-center">
                  <span className="font-mono font-bold text-violet-700 text-sm">{s.archanaTickets?.end||s.archanaTickets?.start||"—"}</span>
                </div>''',
     '''                <div className="px-2 py-3 text-center">
                  <span className="font-mono font-bold text-violet-700 text-sm bg-violet-100 bg-opacity-60 px-1.5 py-0.5 rounded">{isClosed ? (s.archanaTickets?.end||"—") : nextRegNum(s.archanaTickets, archanaiReg ? archanaiReg.prefix : "A", s.archanaTickets?.ticketCount)}</span>
                </div>''')
cut('''              {/* Donation Book row */}''', '''              {/* Archana Tickets row */}''')
cut('''              {/* Expense Vouchers row */}''', '''              {/* Hundi row */}''')
swap(OLD_COLS, NEW_COLS, 4)
swap('''            {/* LEFT: Register card — 7 cols: Type(3) Start End Count Pay Amount */}''',
     '''            {/* LEFT: Register card — Type, Next No., Count, Pay, Amount */}''')

# Laptop: Donations and Expenses cards side by side, under the table
swap('''          {/* ── Bottom strip: 3 aligned columns ── */}''',
     '''          {/* ── Donations and Expenses: details first, then payment ── */}
          {(() => {
            const db = s.donationBook||{}, ev = s.expenseVouchers||{};
            return (
              <div className="grid md:grid-cols-2 gap-4 mt-4 items-start">
                <SheetRegCard isClosed={isClosed}
                  label="Donations" icon="📖" color="emerald"
                  count={parseInt(db.count||0)} total={db.amount||"0.00"}
                  orderPay={db.orderPay} orderCount={db.orderCount} price={db.perAmount} perAmt={db.perAmount||""}
                  nextNum={nextRegNum(db, donationReg ? (donationReg.prefix||"D") : "D", db.count)}
                  services={sevas||[]} serviceId={db.orderServiceId} donationDate={db.orderDate||s.date}
                  onService={sv=>up({donationBook:{...db,orderServiceId:sv?sv.id:"",orderServiceName:sv?sv.name:"",perAmount:sv?sv.charge:db.perAmount}})}
                  cash={db.cashAmount||"0.00"} sumup={db.sumupAmount||"0.00"} online={db.onlineAmount||"0.00"}
                  onIncr={incrDonation} onDecr={decrDonation}
                  onPayType={p=>up({donationBook:{...db,orderPay:p}})}
                  onPerAmt={v=>up({donationBook:{...db,perAmount:v}})}
                  onTaken={()=>up({donationBook:{...db,...NO_DONATION}})}
                  amtLabel="Amount £" donors={db.donors}
                  donor={{name:db.orderName, contact:db.orderContact}}
                  onDonor={(f,v)=>up({donationBook:{...db,[f]:v}})}/>
                <SheetRegCard isClosed={isClosed}
                  label="Expenses" icon="🧾" color="amber"
                  count={parseInt(ev.count||0)} total={ev.amount||"0.00"}
                  orderPay={ev.orderPay} orderCount={ev.orderCount} price={ev.perAmount} perAmt={ev.perAmount||""}
                  nextNum={nextRegNum(ev, expenseReg ? (expenseReg.prefix||"E") : "E", ev.count)}
                  cash={ev.cashAmount||"0.00"} sumup={ev.sumupAmount||"0.00"} online={ev.onlineAmount||"0.00"}
                  onIncr={incrExpense} onDecr={decrExpense}
                  onPayType={p=>up({expenseVouchers:{...ev,orderPay:p}})}
                  onPerAmt={v=>up({expenseVouchers:{...ev,perAmount:v}})}
                  onTaken={()=>up({expenseVouchers:takeExpense(ev)})}
                  amtLabel="Amount £" nameLabel="Paid to (name or company) *" donors={ev.payees}
                  donor={{name:ev.orderName, contact:ev.orderContact}}
                  expense={{purpose:ev.orderPurpose, date:ev.orderDate}}
                  onDonor={(f,v)=>up({expenseVouchers:{...ev,[f]:v}})}
                  sig={ev.orderSig} onSig={v=>up({expenseVouchers:{...ev,orderSig:v}})}/>
              </div>
            );
          })()}

          {/* ── Bottom strip: 3 aligned columns ── */}''')

# ── Card totals include expenses paid by card ─────────────────────────────────
swap('''    const don = parseFloat(s.donationBook?.sumupAmount||0);
    return (arc + don).toFixed(2);''',
     '''    const don = parseFloat(s.donationBook?.sumupAmount||0);
    const exp = parseFloat(s.expenseVouchers?.sumupAmount||0);
    return (arc + don - exp).toFixed(2);''')
swap('''                      <div className="font-bold text-slate-600 mb-1.5">💳 SumUp</div>
                      <div className="flex justify-between text-slate-500"><span>Archanai</span><span>£{parseFloat(s.archanaTickets?.sumupAmount||0).toFixed(2)}</span></div>
                      <div className="flex justify-between text-slate-500"><span>Donation</span><span>£{parseFloat(s.donationBook?.sumupAmount||0).toFixed(2)}</span></div>''',
     '''                      <div className="font-bold text-slate-600 mb-1.5">💳 Card</div>
                      <div className="flex justify-between text-slate-500"><span>Archanai</span><span>£{parseFloat(s.archanaTickets?.sumupAmount||0).toFixed(2)}</span></div>
                      <div className="flex justify-between text-slate-500"><span>Donation</span><span>£{parseFloat(s.donationBook?.sumupAmount||0).toFixed(2)}</span></div>
                      <div className="flex justify-between text-slate-500"><span>Expenses</span><span className="text-red-500">−£{parseFloat(s.expenseVouchers?.sumupAmount||0).toFixed(2)}</span></div>''')

# ── Dashboard: next rota's sponsors include service donors ────────────────────
swap('''            .map(don => ({ area: area.name, donor: don.donor, amount: don.amount }))
        );''',
     '''            .map(don => ({ area: area.name, donor: don.donor, amount: don.amount }))
        ).concat(servicePaidOn(rotaSheets, nextDateStr));''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
