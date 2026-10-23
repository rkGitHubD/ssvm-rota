"""Rota Sheet expenses: "What was it for?" and "Date of expense" are also required.

Usage: python3 tools/expense-purpose-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def swap(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


# ── Helpers ───────────────────────────────────────────────────────────────────
swap('''const NO_EXPENSE = { ...NO_DONATION, orderSig:"" };''',
     '''const NO_EXPENSE = { ...NO_DONATION, orderSig:"", orderPurpose:"", orderDate:"" };
// Expenses also need what it was for and when it was spent
const expenseReady = ev => partyReady(ev) && !!((ev||{}).orderPurpose||"").trim() && !!(ev||{}).orderDate;
// Voucher record: payee, contact, amount and payment, plus purpose and date
const addPayee = (ev, no) => addDonor({ ...ev, donors: ev.payees }, no)
  .map((p, i, all) => i === all.length-1 ? { ...p, purpose: (ev.orderPurpose||"").trim(), date: ev.orderDate } : p);''')

# Expense checks use expenseReady
swap('''    if (!partyReady(ev)) return showToast("Enter the amount, paid to and email or phone first","error");''',
     '''    if (!expenseReady(ev)) return showToast("Fill in amount, paid to, email or phone, what it was for and the date first","error");''')
swap('''    if (!partyReady(ev)) return showToast("Enter the amount, paid to and email or phone first", "error");''',
     '''    if (!expenseReady(ev)) return showToast("Fill in amount, paid to, email or phone, what it was for and the date first", "error");''')
swap('''payees:addDonor({...ev,donors:ev.payees},newEnd)''', '''payees:addPayee(ev,newEnd)''')
swap('''payees: addDonor({ ...ev, donors: ev.payees }, newEnd)''', '''payees: addPayee(ev, newEnd)''')
swap('''disabled={!s.expenseVouchers?.orderPay||!partyReady(s.expenseVouchers)} title={!partyReady(s.expenseVouchers)?"Enter the amount, paid to and email or phone first"''',
     '''disabled={!s.expenseVouchers?.orderPay||!expenseReady(s.expenseVouchers)} title={!expenseReady(s.expenseVouchers)?"Fill in amount, paid to, email or phone, what it was for and the date first"''')
swap('''<select value={r.orderPay||""} disabled={open||!partyReady(r)} onChange={e=>up({expenseVouchers:''',
     '''<select value={r.orderPay||""} disabled={open||!expenseReady(r)} onChange={e=>up({expenseVouchers:''')

# ── Phone card ────────────────────────────────────────────────────────────────
swap('''      nameLabel=props.nameLabel||"Donor name *", sig=props.sig, onSig=props.onSig;''',
     '''      nameLabel=props.nameLabel||"Donor name *", sig=props.sig, onSig=props.onSig, expense=props.expense;''')
swap('''  var ready = !donor || partyReady({perAmount:perAmt, orderName:donor.name, orderContact:donor.contact});''',
     '''  var ready = !donor || (expense ? expenseReady : partyReady)({perAmount:perAmt, orderName:donor.name, orderContact:donor.contact,
    orderPurpose:expense&&expense.purpose, orderDate:expense&&expense.date});''')
swap('''            placeholder="Email or phone *" inputMode="email" className={"w-full border rounded-lg px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-300 disabled:bg-slate-100 "+(donor.contact&&!validContact(donor.contact)?"border-red-300":"border-slate-200")}/>
        </div>''',
     '''            placeholder="Email or phone *" inputMode="email" className={"w-full border rounded-lg px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-300 disabled:bg-slate-100 "+(donor.contact&&!validContact(donor.contact)?"border-red-300":"border-slate-200")}/>
          {expense && (
            <>
              <input value={expense.purpose||""} onChange={function(e){onDonor("orderPurpose",e.target.value);}} disabled={isClosed||open}
                placeholder="What was it for? *" className="w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-amber-300 disabled:bg-slate-100"/>
              <label className="flex items-center gap-2">
                <span className="text-xs text-slate-500 whitespace-nowrap flex-shrink-0">Date of expense *</span>
                <input type="date" value={expense.date||""} max={new Date().toISOString().slice(0,10)} onChange={function(e){onDonor("orderDate",e.target.value);}} disabled={isClosed||open}
                  className="flex-1 min-w-0 border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-amber-300 disabled:bg-slate-100"/>
              </label>
            </>
          )}
        </div>''')
swap('''!ready ? "Enter the amount, name and email or phone first" : "1. How are they paying?"}''',
     '''!ready ? (expense ? "Fill in all the details above first" : "Enter the amount, name and email or phone first") : "1. How are they paying?"}''')
swap('''<span className="flex-1 truncate">{d.name}</span>''',
     '''<span className="flex-1 truncate">{d.name}{d.purpose && <span className="text-slate-400"> · {d.purpose}{d.date ? " · "+new Date(d.date).toLocaleDateString("en-GB",{day:"numeric",month:"short"}) : ""}</span>}</span>''')
swap('''        donor={{name:ev.orderName, contact:ev.orderContact}}''',
     '''        donor={{name:ev.orderName, contact:ev.orderContact}}
        expense={{purpose:ev.orderPurpose, date:ev.orderDate}}''')

# ── Full form ─────────────────────────────────────────────────────────────────
swap('''                        <input value={ev.orderContact||""} disabled={locked} placeholder="Email or phone *"
                          onChange={e=>up({expenseVouchers:{...ev,orderContact:e.target.value}})} className={cls}/>''',
     '''                        <input value={ev.orderContact||""} disabled={locked} placeholder="Email or phone *"
                          onChange={e=>up({expenseVouchers:{...ev,orderContact:e.target.value}})} className={cls}/>
                        <input value={ev.orderPurpose||""} disabled={locked} placeholder="What was it for? *"
                          onChange={e=>up({expenseVouchers:{...ev,orderPurpose:e.target.value}})} className={cls}/>
                        <label className="flex items-center gap-1.5 text-xs text-slate-500">Date of expense *
                          <input type="date" value={ev.orderDate||""} disabled={locked} max={new Date().toISOString().slice(0,10)}
                            onChange={e=>up({expenseVouchers:{...ev,orderDate:e.target.value}})} className={cls+" flex-1"}/>
                        </label>''')
swap('''{d.no} · {d.name} · {d.contact} · £{d.amount} · {PAY_LABEL[d.pay]||d.pay}''',
     '''{d.no} · {d.name} · {d.contact} · {d.purpose} · {d.date && new Date(d.date).toLocaleDateString("en-GB")} · £{d.amount} · {PAY_LABEL[d.pay]||d.pay}''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
