"""Donations for a service can't be less than the service price; printout shows the
numbers actually issued and a full Cash / Card / Online breakdown (£0.00 where unused).

Usage: python3 tools/print-fixes-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def swap(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


# ── Service donations: amount at least the service price ──────────────────────
swap('''const partyReady = r => parseFloat((r||{}).perAmount||0) > 0 && !!((r||{}).orderName||"").trim() && validContact((r||{}).orderContact);''',
     '''const partyReady = r => parseFloat((r||{}).perAmount||0) > 0 && !!((r||{}).orderName||"").trim() && validContact((r||{}).orderContact)
  && parseFloat((r||{}).perAmount||0) >= parseFloat((r||{}).orderServiceCharge||0);''')
swap('''const NO_DONATION = { ...NO_ORDER, perAmount:"", orderName:"", orderContact:"", orderServiceId:"", orderServiceName:"", orderDate:"" };''',
     '''const NO_DONATION = { ...NO_ORDER, perAmount:"", orderName:"", orderContact:"", orderServiceId:"", orderServiceName:"", orderServiceCharge:"", orderDate:"" };''')
for old in ['''orderServiceId:sv?sv.id:"",orderServiceName:sv?sv.name:"",perAmount:sv?sv.charge:db.perAmount''']:
    swap(old, '''orderServiceId:sv?sv.id:"",orderServiceName:sv?sv.name:"",orderServiceCharge:sv?sv.charge:"",perAmount:sv?sv.charge:db.perAmount''', 2)
swap('''  var ready = !donor || (expense ? expenseReady : partyReady)({perAmount:perAmt, orderName:donor.name, orderContact:donor.contact,
    orderPurpose:expense&&expense.purpose, orderDate:expense&&expense.date});''',
     '''  var ready = !donor || (expense ? expenseReady : partyReady)({perAmount:perAmt, orderName:donor.name, orderContact:donor.contact,
    orderPurpose:expense&&expense.purpose, orderDate:expense&&expense.date, orderServiceCharge:props.serviceCharge});
  var minAmt = parseFloat(props.serviceCharge||0);
  var belowMin = minAmt > 0 && perAmt !== "" && parseFloat(perAmt||0) < minAmt;''')
swap('''          <input type="number" value={perAmt} onChange={function(e){onPerAmt(e.target.value);}}
            placeholder="0.00" disabled={isClosed||open}
            className="flex-1 border border-slate-200 rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 bg-white disabled:bg-slate-100"/>
        </div>
      )}''',
     '''          <input type="number" value={perAmt} onChange={function(e){onPerAmt(e.target.value);}}
            placeholder="0.00" disabled={isClosed||open} min={minAmt||undefined}
            className={"flex-1 border rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-300 bg-white disabled:bg-slate-100 "+(belowMin?"border-red-400":"border-slate-200")}/>
        </div>
      )}
      {minAmt > 0 && !open && (
        <div className={"px-4 pb-2 -mt-1 text-xs "+(belowMin?"text-red-600 font-semibold":"text-slate-400")}>Minimum £{minAmt.toFixed(2)} for this service</div>
      )}''')
# Pass the chosen service's price to the cards (phone and laptop)
swap('''services={sevas} serviceId={db.orderServiceId}''', '''services={sevas} serviceId={db.orderServiceId} serviceCharge={db.orderServiceCharge}''')
swap('''services={sevas||[]} serviceId={db.orderServiceId}''', '''services={sevas||[]} serviceId={db.orderServiceId} serviceCharge={db.orderServiceCharge}''')
# Server-side style guard in the counters too
swap('''    if (!donationReady(db)) return showToast("Enter the amount, donor name and email or phone first", "error");''',
     '''    if (!donationReady(db)) return showToast(parseFloat(db.perAmount||0) < parseFloat(db.orderServiceCharge||0) ? "Amount can't be less than £"+db.orderServiceCharge+" for "+db.orderServiceName : "Enter the amount, donor name and email or phone first", "error");''')
swap('''    if (!donationReady(db)) return showToast("Enter the amount, donor name and email or phone first","error");''',
     '''    if (!donationReady(db)) return showToast(parseFloat(db.perAmount||0) < parseFloat(db.orderServiceCharge||0) ? "Amount can't be less than £"+db.orderServiceCharge+" for "+db.orderServiceName : "Enter the amount, donor name and email or phone first","error");''')

# ── Printout: numbers actually issued ─────────────────────────────────────────
swap('''  const range = (r, n) => (parseInt(n) || 0) > 0 ? esc(r.start) + " – " + esc(r.end) : "—";''',
     '''  // First and last numbers issued today: the last is r.end, the first is (count − 1) before it
  const range = (r, n) => {
    n = parseInt(n) || 0;
    const m = String(r.end || "").match(/^(.*?)(\\d+)$/);
    if (!n || !m) return "—";
    const first = fmtRegNum(m[1], parseInt(m[2], 10) - n + 1);
    return n === 1 ? esc(r.end) : esc(first) + " – " + esc(r.end);
  };''')

# ── Printout: Cash / Card / Online everywhere, £0.00 where unused ─────────────
swap('''    + "<tr><td><b>Hundi</b></td><td>—</td><td></td><td class='n'>" + gbp(hundi) + "</td><td></td><td></td><td class='n'><b>" + gbp(hundi) + "</b></td></tr>"
    + regRow("Expenses (out)", ev, ev.count)
    + "<tr class='t'><td colspan='6'>Net revenue (income " + gbp(income) + " − expenses " + gbp(ev.amount) + ")</td><td class='n'>" + gbp(net) + "</td></tr></table>";''',
     '''    + "<tr><td><b>Hundi</b></td><td>—</td><td class='n'>—</td><td class='n'>" + gbp(hundi) + "</td><td class='n'>£0.00</td><td class='n'>£0.00</td><td class='n'><b>" + gbp(hundi) + "</b></td></tr>"
    + "<tr class='t'><td colspan='3'>Income</td><td class='n'>" + gbp(cashIn) + "</td><td class='n'>" + gbp(inBy.sumup) + "</td><td class='n'>" + gbp(inBy.online) + "</td><td class='n'>" + gbp(income) + "</td></tr>"
    + regRow("Expenses (out)", ev, ev.count)
    + "<tr class='t'><td colspan='3'>Net (income − expenses)</td><td class='n'>" + gbp(cashIn - cashOut) + "</td><td class='n'>" + gbp(card) + "</td><td class='n'>" + gbp(online) + "</td><td class='n'>" + gbp(net) + "</td></tr></table>";''')
swap('''  const donors = db.donors || [], payees = ev.payees || [];''',
     '''  const donors = db.donors || [], payees = ev.payees || [];
  const inBy = { sumup: parseFloat(at.sumupAmount || 0) + parseFloat(db.sumupAmount || 0), online: parseFloat(at.onlineAmount || 0) + parseFloat(db.onlineAmount || 0) };
  // "Cash £x · Card £y · Online £z" for a list of donations or expenses
  const split = list => ["cash", "sumup", "online"].map(k => pay(k) + " " + gbp(list.filter(d => d.pay === k).reduce((t, d) => t + parseFloat(d.amount || 0), 0))).join(" · ");''')
swap('''      + donors.map(d => "<tr><td>" + esc(d.no) + "</td><td>" + esc(d.name) + "</td><td>" + esc(d.purpose || "General") + "</td><td>" + day(d.date) + "</td><td>" + pay(d.pay) + "</td><td class='n'>" + gbp(d.amount) + "</td></tr>").join("")
      + "</table>"''',
     '''      + donors.map(d => "<tr><td>" + esc(d.no) + "</td><td>" + esc(d.name) + "</td><td>" + esc(d.purpose || "General") + "</td><td>" + day(d.date) + "</td><td>" + pay(d.pay) + "</td><td class='n'>" + gbp(d.amount) + "</td></tr>").join("")
      + "<tr class='t'><td colspan='5'>" + split(donors) + "</td><td class='n'>" + gbp(donors.reduce((t, d) => t + parseFloat(d.amount || 0), 0)) + "</td></tr>"
      + "</table>"''')
swap('''        + (d.sig ? "<img src='" + d.sig + "' style='height:16px'/>" : "<span class='bad'>missing</span>") + "</td></tr>").join("")
      + "</table>"''',
     '''        + (d.sig ? "<img src='" + d.sig + "' style='height:16px'/>" : "<span class='bad'>missing</span>") + "</td></tr>").join("")
      + "<tr class='t'><td colspan='5'>" + split(payees) + "</td><td class='n'>" + gbp(payees.reduce((t, d) => t + parseFloat(d.amount || 0), 0)) + "</td><td></td></tr>"
      + "</table>"''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
