"""Rota Sheet: one order at a time — pick Cash/Card/Online, add items (type locked), then "Payment taken".

Usage: python3 tools/pay-order-patch.py <file>   (the master Index.html, or build/app.jsx to test)
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def between(start, end, new):
    """Replace the text from `start` (inclusive) up to `end` (exclusive)."""
    global s
    assert s.count(start) == 1, start
    i = s.index(start)
    j = s.index(end, i)
    s = s[:i] + new + s[j:]


def swap(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:80])
    s = s.replace(old, new)


# ── Shared helper, placed just before the mobile sheet ────────────────────────
swap("function RotaSheetMobile(", '''// ─── Rota Sheet orders ───────────────────────────────────────────────────────
// Money is taken one order at a time: choose Cash / Card / Online, add tickets or
// entries, then "Payment taken". orderPay/orderCount describe the open order;
// its payment type can't change once something has been added to it.
const PAY_FIELD = { cash:"cashAmount", sumup:"sumupAmount", online:"onlineAmount" };
const PAY_LABEL = { cash:"💵 Cash", sumup:"💳 Card", online:"🌐 Online" };
// Money fields after adding (dir 1) or removing (dir -1) one item at `price` in the open order
function orderMoney(r, price, dir) {
  const f = PAY_FIELD[r.orderPay];
  const next = { ...r, [f]: Math.max(0, parseFloat(r[f]||0) + dir*price).toFixed(2) };
  return { [f]: next[f], payType: r.orderPay, orderCount: Math.max(0, (r.orderCount||0) + dir),
    amount: Object.values(PAY_FIELD).reduce((t,k)=>t+parseFloat(next[k]||0), 0).toFixed(2) };
}
const NO_ORDER = { orderPay:"", orderCount:0 };

function RotaSheetMobile(''')

# ── Full form: counters ───────────────────────────────────────────────────────
between("  const issueArchana = () => {", "  // ── Donation Book counter", '''  const issueArchana = () => {
    if (s.status === "closed") return showToast("Sheet is closed", "error");
    const reg = archanaiReg;
    if (!reg) return showToast("No Archanai register configured", "error");
    const at       = s.archanaTickets;
    if (!at.orderPay) return showToast("Choose Cash, Card or Online first", "error");
    const firstNum = at.firstNum || parseInt((at.start||"").replace(/\\D/g,"")) + 1 || 1;
    const newCount = (at.ticketCount || 0) + 1;
    const newEnd   = fmtRegNum(reg.prefix, firstNum + newCount - 1);
    const price    = archDayPrice();
    const payType  = at.orderPay;

    // Update sumup and online rows on the sheet too
    const newSumup  = { amount: (parseFloat(s.sumup?.amount||0)  + (payType==="sumup"  ? price : 0)).toFixed(2) };
    const newOnline = { amount: (parseFloat(s.online?.amount||0) + (payType==="online" ? price : 0)).toFixed(2) };

    up({
      archanaTickets: { ...at, ticketCount: newCount, count: newCount, end: newEnd, firstNum, ...orderMoney(at, price, 1) },
      sumup:  payType === "sumup"  ? newSumup  : s.sumup,
      online: payType === "online" ? newOnline : s.online,
    });
    showToast(`Issued ${newEnd} · £${price.toFixed(2)} ${PAY_LABEL[payType]}`);
  };

  const undoArchana = () => {
    if (s.status === "closed") return showToast("Sheet is closed", "error");
    const at = s.archanaTickets;
    if (!(at.orderCount > 0)) return showToast("Only tickets in the current order can be taken off", "error");
    const reg      = archanaiReg;
    if (!reg) return showToast("No Archanai register configured", "error");
    const firstNum = at.firstNum || parseInt((at.start||"").replace(/\\D/g,"")) + 1 || 1;
    const newCount = (at.ticketCount||0) - 1;
    const newEnd   = newCount > 0 ? fmtRegNum(reg.prefix, firstNum + newCount - 1) : at.start;
    const price    = archDayPrice();
    const payType  = at.orderPay;

    const newSumup  = { amount: Math.max(0, parseFloat(s.sumup?.amount||0)  - (payType==="sumup"  ? price : 0)).toFixed(2) };
    const newOnline = { amount: Math.max(0, parseFloat(s.online?.amount||0) - (payType==="online" ? price : 0)).toFixed(2) };

    up({
      archanaTickets: { ...at, ticketCount: newCount, count: newCount, end: newEnd, ...orderMoney(at, price, -1) },
      sumup:  payType === "sumup"  ? newSumup  : s.sumup,
      online: payType === "online" ? newOnline : s.online,
    });
    showToast("Last ticket undone");
  };

''')

between("  // ── Donation Book counter", "  // Update a donation payment split field", '''  // ── Donation Book counter ────────────────────────────────────────────────────
  const incrDonation = () => {
    if (s.status === "closed") return;
    const db       = s.donationBook;
    if (!db.orderPay) return showToast("Choose Cash, Card or Online first", "error");
    const prefix   = donationReg ? (donationReg.prefix || "D") : "D";
    const firstNum = db.firstNum || parseInt((db.start||"").replace(/\\D/g,"")) + 1 || 1;
    const newCnt   = (parseInt(db.count||0)) + 1;
    const newEnd   = fmtRegNum(prefix, firstNum + newCnt - 1);
    up({ donationBook: { ...db, count: newCnt, end: newEnd, firstNum, ...orderMoney(db, parseFloat(db.perAmount||0), 1) } });
  };
  const decrDonation = () => {
    if (s.status === "closed") return;
    const db       = s.donationBook;
    if (!(db.orderCount > 0)) return showToast("Only entries in the current order can be taken off", "error");
    const prefix   = donationReg ? (donationReg.prefix || "D") : "D";
    const newCnt   = Math.max(0, (parseInt(db.count||0)) - 1);
    const firstNum = db.firstNum || parseInt((db.start||"").replace(/\\D/g,"")) + 1 || 1;
    const newEnd   = newCnt > 0 ? fmtRegNum(prefix, firstNum + newCnt - 1) : db.start;
    up({ donationBook: { ...db, count: newCnt, end: newEnd, ...orderMoney(db, parseFloat(db.perAmount||0), -1) } });
  };
''')

between("  // ── Expense Voucher counter", "  // Update an expense payment split field", '''  // ── Expense Voucher counter ──────────────────────────────────────────────────
  const incrExpense = () => {
    if (s.status === "closed") return;
    const ev       = s.expenseVouchers;
    if (!ev.orderPay) return showToast("Choose Cash, Card or Online first", "error");
    const prefix   = expenseReg ? (expenseReg.prefix || "E") : "E";
    const firstNum = ev.firstNum || parseInt((ev.start||"").replace(/\\D/g,"")) + 1 || 1;
    const newCnt   = (parseInt(ev.count||0)) + 1;
    const newEnd   = fmtRegNum(prefix, firstNum + newCnt - 1);
    up({ expenseVouchers: { ...ev, count: newCnt, end: newEnd, firstNum, ...orderMoney(ev, parseFloat(ev.perAmount||0), 1) } });
  };
  const decrExpense = () => {
    if (s.status === "closed") return;
    const ev       = s.expenseVouchers;
    if (!(ev.orderCount > 0)) return showToast("Only entries in the current order can be taken off", "error");
    const prefix   = expenseReg ? (expenseReg.prefix || "E") : "E";
    const newCnt   = Math.max(0, (parseInt(ev.count||0)) - 1);
    const firstNum = ev.firstNum || parseInt((ev.start||"").replace(/\\D/g,"")) + 1 || 1;
    const newEnd   = newCnt > 0 ? fmtRegNum(prefix, firstNum + newCnt - 1) : ev.start;
    up({ expenseVouchers: { ...ev, count: newCnt, end: newEnd, ...orderMoney(ev, parseFloat(ev.perAmount||0), -1) } });
  };
''')

swap('''    const total= (parseFloat(next.cashAmount||0) + parseFloat(next.onlineAmount||0)).toFixed(2);
    up({ expenseVouchers: { ...next, amount: total } });''',
     '''    const total= (parseFloat(next.cashAmount||0) + parseFloat(next.sumupAmount||0) + parseFloat(next.onlineAmount||0)).toFixed(2);
    up({ expenseVouchers: { ...next, amount: total } });''')

# ── Full form: rows ───────────────────────────────────────────────────────────
# Payment cell: choose a type (locked while the order has items), then "Payment taken"
def pay_cell(key, cnt, ring):
    return f'''{{!isClosed ? (() => {{
                    const r = s.{key}||{{}};
                    const open = (r.orderCount||0) > 0;
                    return (
                      <div className="space-y-1">
                        <select value={{r.orderPay||""}} disabled={{open}} onChange={{e=>up({{{key}:{{...r,orderPay:e.target.value}}}})}}
                          title={{open ? "Finish this order before changing the payment type" : ""}}
                          className={{`w-full border rounded-lg px-1.5 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-{ring}-200 ${{open?"bg-slate-100 text-slate-500 cursor-not-allowed border-slate-200":r.orderPay?"bg-white border-slate-200":"bg-white border-red-300"}}`}}>
                          <option value="">Choose…</option>
                          <option value="cash">💵 Cash</option>
                          <option value="sumup">💳 Card</option>
                          <option value="online">🌐 Online</option>
                        </select>
                        {{open && (
                          <button onClick={{()=>up({{{key}:{{...r,...NO_ORDER}}}})}}
                            className="w-full bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg px-1 py-1 text-xs font-bold">✓ Taken ({{r.orderCount}})</button>
                        )}}
                      </div>
                    );
                  }})() : (
                    <div className="text-xs text-slate-400 text-center">—</div>
                  )}}'''

# Donation row payment cell
between('''                  {!isClosed ? (() => {
                    const hasCount = (s.donationBook?.count||0) > 0;''',
        '''                </div>
                <div className="px-2 py-3">
                  {!isClosed ? (
                    <input type="text" inputMode="decimal" value={s.donationBook?.perAmount||""}''',
        pay_cell("donationBook", "count", "blue") + "\n")
# Archana row payment cell
between('''                  {!isClosed ? (() => {
                    const hasCount = (s.archanaTickets?.ticketCount||0) > 0;
                    return (
                      <select''',
        '''                </div>
                <div className="px-2 py-3 text-right">''',
        pay_cell("archanaTickets", "ticketCount", "violet") + "\n")
# Expense row payment cell
between('''                  {!isClosed ? (() => {
                    const hasCount = (s.expenseVouchers?.count||0) > 0;''',
        '''                </div>
                <div className="px-2 py-3">
                  {!isClosed ? (
                    <input type="text" inputMode="decimal" value={s.expenseVouchers?.perAmount||""}''',
        pay_cell("expenseVouchers", "count", "amber") + "\n")

# +/− buttons: + needs a type, − only takes off items from the open order
for incr, decr, key in [("incrDonation", "decrDonation", "donationBook"),
                        ("issueArchana", "undoArchana", "archanaTickets"),
                        ("incrExpense", "decrExpense", "expenseVouchers")]:
    swap(f'<button onClick={{{decr}}} className="w-5 h-5 rounded',
         f'<button onClick={{{decr}}} disabled={{!(s.{key}?.orderCount>0)}} className="disabled:opacity-30 w-5 h-5 rounded')
    swap(f'<button onClick={{{incr}}} className="w-5 h-5 rounded',
         f'<button onClick={{{incr}}} disabled={{!s.{key}?.orderPay}} title={{s.{key}?.orderPay?"":"Choose Cash, Card or Online first"}} className="disabled:opacity-30 w-5 h-5 rounded')

# The £-each amount and the Normal/Special price can't change in the middle of an order
swap('''value={s.donationBook?.perAmount||""}
                      onChange''', '''value={s.donationBook?.perAmount||""} disabled={s.donationBook?.orderCount>0}
                      onChange''')
swap('''value={s.expenseVouchers?.perAmount||""}
                      onChange''', '''value={s.expenseVouchers?.perAmount||""} disabled={s.expenseVouchers?.orderCount>0}
                      onChange''')
swap('''onChange={()=>up({archanaTickets:{...s.archanaTickets,dayType:opt.v}})} className="sr-only"/>''',
     '''onChange={()=>up({archanaTickets:{...s.archanaTickets,dayType:opt.v}})} disabled={s.archanaTickets?.orderCount>0} className="sr-only"/>''')

# ── Mobile sheet: counters ────────────────────────────────────────────────────
between("  // ── Archana counter ──", "  // ── Close sheet ──", '''  // ── Archana counter ───────────────────────────────────────────────────────
  var issueArch = function() {
    if (isClosed) return;
    var at = s.archanaTickets||{};
    if (!at.orderPay) return showToast("Choose Cash, Card or Online first","error");
    var price = (at.dayType==="special") ? 5.00 : 3.00;
    var prefix = archanaiReg ? (archanaiReg.prefix||"A") : "A";
    var firstNum = at.firstNum || parseInt((at.start||"").replace(/\\D/g,"")+1)||1;
    var newCnt = (parseInt(at.ticketCount||0))+1;
    var newEnd = fmtRegNum(prefix, firstNum+newCnt-1);
    up({archanaTickets:{...at,ticketCount:newCnt,count:newCnt,end:newEnd,firstNum,...orderMoney(at,price,1)}});
    showToast("Issued "+newEnd+" · £"+price.toFixed(2)+" "+PAY_LABEL[at.orderPay]);
  };
  var undoArch = function() {
    if (isClosed) return;
    var at = s.archanaTickets||{};
    if (!(at.orderCount>0)) return showToast("Only tickets in the current order can be taken off","error");
    var price = (at.dayType==="special") ? 5.00 : 3.00;
    var prefix = archanaiReg ? (archanaiReg.prefix||"A") : "A";
    var firstNum = at.firstNum || parseInt((at.start||"").replace(/\\D/g,"")+1)||1;
    var newCnt = Math.max(0,(parseInt(at.ticketCount||0))-1);
    var newEnd = newCnt>0 ? fmtRegNum(prefix,firstNum+newCnt-1) : at.start;
    up({archanaTickets:{...at,ticketCount:newCnt,count:newCnt,end:newEnd,...orderMoney(at,price,-1)}});
    showToast("Undone");
  };

  // ── Donation counter ──────────────────────────────────────────────────────
  var incrDon = function() {
    if (isClosed) return;
    var db = s.donationBook||{};
    if (!db.orderPay) return showToast("Choose Cash, Card or Online first","error");
    var prefix = donationReg ? (donationReg.prefix||"D") : "D";
    var firstNum = db.firstNum || parseInt((db.start||"").replace(/\\D/g,"")+1)||1;
    var newCnt = (parseInt(db.count||0))+1;
    var newEnd = fmtRegNum(prefix,firstNum+newCnt-1);
    up({donationBook:{...db,count:newCnt,end:newEnd,firstNum,...orderMoney(db,parseFloat(db.perAmount||0),1)}});
  };
  var decrDon = function() {
    if (isClosed) return;
    var db = s.donationBook||{};
    if (!(db.orderCount>0)) return showToast("Only entries in the current order can be taken off","error");
    var prefix = donationReg ? (donationReg.prefix||"D") : "D";
    var newCnt = Math.max(0,(parseInt(db.count||0))-1);
    var firstNum = db.firstNum || parseInt((db.start||"").replace(/\\D/g,"")+1)||1;
    var newEnd = newCnt>0 ? fmtRegNum(prefix,firstNum+newCnt-1) : db.start;
    up({donationBook:{...db,count:newCnt,end:newEnd,...orderMoney(db,parseFloat(db.perAmount||0),-1)}});
  };

  // ── Expense counter ───────────────────────────────────────────────────────
  var incrExp = function() {
    if (isClosed) return;
    var ev = s.expenseVouchers||{};
    if (!ev.orderPay) return showToast("Choose Cash, Card or Online first","error");
    var prefix = expenseReg ? (expenseReg.prefix||"E") : "E";
    var firstNum = ev.firstNum || parseInt((ev.start||"").replace(/\\D/g,"")+1)||1;
    var newCnt = (parseInt(ev.count||0))+1;
    var newEnd = fmtRegNum(prefix,firstNum+newCnt-1);
    up({expenseVouchers:{...ev,count:newCnt,end:newEnd,firstNum,...orderMoney(ev,parseFloat(ev.perAmount||0),1)}});
  };
  var decrExp = function() {
    if (isClosed) return;
    var ev = s.expenseVouchers||{};
    if (!(ev.orderCount>0)) return showToast("Only entries in the current order can be taken off","error");
    var prefix = expenseReg ? (expenseReg.prefix||"E") : "E";
    var newCnt = Math.max(0,(parseInt(ev.count||0))-1);
    var firstNum = ev.firstNum || parseInt((ev.start||"").replace(/\\D/g,"")+1)||1;
    var newEnd = newCnt>0 ? fmtRegNum(prefix,firstNum+newCnt-1) : ev.start;
    up({expenseVouchers:{...ev,count:newCnt,end:newEnd,...orderMoney(ev,parseFloat(ev.perAmount||0),-1)}});
  };

''')

# ── Mobile sheet: the register card ───────────────────────────────────────────
swap('''        payType=props.payType||"cash", perAmt=props.perAmt||"",''',
     '''        orderPay=props.orderPay||"", orderCount=parseInt(props.orderCount||0), perAmt=props.perAmt||"",''')
swap('''        onIncr=props.onIncr, onDecr=props.onDecr, onPayType=props.onPayType,
        onPerAmt=props.onPerAmt;''',
     '''        onIncr=props.onIncr, onDecr=props.onDecr, onPayType=props.onPayType,
        onPerAmt=props.onPerAmt, onTaken=props.onTaken, priceNow=parseFloat(props.price||0);
    var open = orderCount > 0;''')

between('''        {/* Per-amount field */}''', '''        {/* Totals by payment */}''', '''        {/* Per-amount field (not for archana, which uses the Normal/Special price) */}
        {onPerAmt && (
          <div className="px-4 pb-2 flex items-center gap-2">
            <span className="text-xs text-slate-500 w-20 flex-shrink-0">£ per entry</span>
            <input type="number" value={perAmt} onChange={function(e){onPerAmt(e.target.value);}}
              placeholder="0.00" disabled={isClosed||open}
              className="flex-1 border border-slate-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 bg-white disabled:bg-slate-100"/>
          </div>
        )}
        {/* 1. Payment type for this order — locked once something is added */}
        <div className="px-4 pb-1 text-xs font-semibold text-slate-500">{open ? "This order is paying by" : "1. How are they paying?"}</div>
        <div className="px-4 pb-3 flex gap-1.5">
          {PAY.map(function(p){var on=orderPay===p; return (
            <button key={p} onClick={function(){onPayType&&onPayType(p);}} disabled={isClosed||(open&&!on)}
              className={"flex-1 py-2 rounded-lg text-sm font-semibold border transition-colors disabled:opacity-40 "+(on?c.badge+" text-white border-transparent":"border-slate-200 text-slate-600 bg-white hover:bg-slate-50")}>
              {PAY_LABEL[p]}
            </button>
          );})}
        </div>
        {/* 2. +/- for this order */}
        <div className="px-4 pb-3 flex items-center gap-3">
          <button onClick={onDecr} disabled={isClosed||!open}
            className="w-12 h-12 rounded-xl bg-red-100 text-red-600 text-2xl font-black flex items-center justify-center disabled:opacity-30 active:scale-95 transition-transform">−</button>
          <div className="flex-1 text-center">
            <div className={"text-3xl font-black "+c.text}>{orderCount}</div>
            <div className="text-xs text-slate-400">{orderPay ? "in this order"+(open?" · £"+(orderCount*priceNow).toFixed(2):"") : "choose payment first"}</div>
          </div>
          <button onClick={onIncr} disabled={isClosed||!orderPay}
            className={"w-12 h-12 rounded-xl text-white text-2xl font-black flex items-center justify-center disabled:opacity-30 active:scale-95 transition-transform "+c.badge}>+</button>
        </div>
        {/* 3. Payment taken → ready for the next order */}
        {open && !isClosed && (
          <div className="px-4 pb-3">
            <button onClick={onTaken}
              className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm active:scale-[0.98] transition-transform">
              ✓ Payment taken — next order
            </button>
          </div>
        )}
        <div className="px-4 pb-2 text-xs text-slate-500">Today so far: <b>{count}</b> {startNum && endNum && count>0 ? "("+startNum+" → "+endNum+")" : ""}</div>
''')
swap('''              <div className="text-xs text-slate-400">📱 SumUp</div>''',
     '''              <div className="text-xs text-slate-400">💳 Card</div>''')

# Card props
swap('''        payType={at.payType||"cash"} perAmt=""''',
     '''        orderPay={at.orderPay} orderCount={at.orderCount} price={at.dayType==="special"?5:3}''')
swap('''        onPayType={function(p){up({archanaTickets:{...at,payType:p}});}}''',
     '''        onPayType={function(p){up({archanaTickets:{...at,orderPay:p}});}}
        onTaken={function(){up({archanaTickets:{...at,...NO_ORDER}});}}''')
swap('''        payType={db.payType||"cash"} perAmt={db.perAmount||""}''',
     '''        orderPay={db.orderPay} orderCount={db.orderCount} price={db.perAmount} perAmt={db.perAmount||""}''')
swap('''        onPayType={function(p){up({donationBook:{...db,payType:p}});}}''',
     '''        onPayType={function(p){up({donationBook:{...db,orderPay:p}});}}
        onTaken={function(){up({donationBook:{...db,...NO_ORDER}});}}''')
swap('''        payType={ev.payType||"cash"} perAmt={ev.perAmount||""}''',
     '''        orderPay={ev.orderPay} orderCount={ev.orderCount} price={ev.perAmount} perAmt={ev.perAmount||""}''')
swap('''        cash={ev.cashAmount||"0.00"} sumup="0.00" online={ev.onlineAmount||"0.00"}''',
     '''        cash={ev.cashAmount||"0.00"} sumup={ev.sumupAmount||"0.00"} online={ev.onlineAmount||"0.00"}''')
swap('''        onPayType={function(p){up({expenseVouchers:{...ev,payType:p}});}}''',
     '''        onPayType={function(p){up({expenseVouchers:{...ev,orderPay:p}});}}
        onTaken={function(){up({expenseVouchers:{...ev,...NO_ORDER}});}}''')
# Normal/Special can't change mid-order
swap('''<button key={pair[0]} onClick={function(){up({archanaTickets:{...at,dayType:pair[0]}});}} disabled={isClosed}''',
     '''<button key={pair[0]} onClick={function(){up({archanaTickets:{...at,dayType:pair[0]}});}} disabled={isClosed||at.orderCount>0}''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
