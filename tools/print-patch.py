"""Rota Sheet: one-page A4 printout, equal-height donation/expense cards, admin reset.

Usage: python3 tools/print-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def swap(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


def cut(start, end):
    global s
    assert s.count(start) == 1, start
    i = s.index(start)
    j = s.index(end, i)
    s = s[:i] + s[j:]


# ── One-page printout (shared by the sheet list and the open sheet) ───────────
PRINT = r'''// ─── Rota Sheet printout: one A4 page, scaled down to fit when the day is busy ──
function printRotaSheet(s, { config = {}, rotaSheets = [], sponsorships = [] } = {}) {
  const esc = v => String(v == null ? "" : v).replace(/[&<>"']/g, c => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[c]));
  const gbp = v => "£" + parseFloat(v || 0).toFixed(2);
  const dash = v => (v == null || v === "") ? "—" : esc(v);
  const day = d => d ? new Date(d).toLocaleDateString("en-GB", { day:"numeric", month:"short", year:"numeric" }) : "—";
  const pay = p => ({ cash:"Cash", sumup:"Card", online:"Online" }[p] || "—");
  const at = s.archanaTickets || {}, db = s.donationBook || {}, ev = s.expenseVouchers || {};
  const closed = s.status === "closed";
  const denoms = s.denomClose || Object.fromEntries(DENOMS.map(d => [d.label, (s.denoms && s.denoms[d.label] && s.denoms[d.label].count) || ""]));
  const counted = DENOMS.reduce((t, d) => t + parseFloat(denoms[d.label] || 0) * d.val, 0);
  const hundi = parseFloat((s.hundi && s.hundi.amount) || 0);
  const cashIn = parseFloat(at.cashAmount || 0) + parseFloat(db.cashAmount || 0) + hundi;
  const cashOut = parseFloat(ev.cashAmount || 0);
  const expected = parseFloat(s.openingBalance || 0) + cashIn - cashOut;
  const diff = counted - expected;
  const card = parseFloat(at.sumupAmount || 0) + parseFloat(db.sumupAmount || 0) - parseFloat(ev.sumupAmount || 0);
  const online = parseFloat(at.onlineAmount || 0) + parseFloat(db.onlineAmount || 0) - parseFloat(ev.onlineAmount || 0);
  const income = parseFloat(at.amount || 0) + parseFloat(db.amount || 0) + hundi;
  const net = income - parseFloat(ev.amount || 0);
  const range = (r, n) => (parseInt(n) || 0) > 0 ? esc(r.start) + " – " + esc(r.end) : "—";
  const sponsors = [].concat(
    (sponsorships || []).flatMap(a => (a.donations || []).filter(d => (d.rotaDates || []).includes(s.date)).map(d => esc(d.donor) + " <i>(" + esc(a.name) + ")</i>")),
    servicePaidOn(rotaSheets, s.date).map(d => esc(d.donor) + " <i>(" + esc(d.area) + ")</i>"),
    s.sponsors ? [esc(s.sponsors)] : []);
  const regRow = (name, r, n) => "<tr><td><b>" + name + "</b></td><td>" + range(r, n) + "</td><td class='n'>" + (parseInt(n) || 0) + "</td><td class='n'>" + gbp(r.cashAmount) + "</td><td class='n'>" + gbp(r.sumupAmount) + "</td><td class='n'>" + gbp(r.onlineAmount) + "</td><td class='n'><b>" + gbp(r.amount) + "</b></td></tr>";
  const donors = db.donors || [], payees = ev.payees || [];
  const sig = s.signature ? "<img src='" + s.signature + "' style='height:34px'/>" : s.rotaLeadSig ? "<div style='font-size:13px;font-style:italic;padding-top:10px'>" + esc(s.rotaLeadSig) + "</div>" : "";

  let h = "<!DOCTYPE html><html><head><meta charset='utf-8'/><title>Rota Sheet " + esc(s.date) + "</title><style>"
    + "@page{size:A4;margin:10mm}*{box-sizing:border-box;margin:0;padding:0}"
    + "body{width:190mm;font-family:Arial,Helvetica,sans-serif;font-size:9px;color:#1e293b;background:#fff}"
    + ".hd{display:flex;align-items:center;gap:8px;border-bottom:2px solid #3730a3;padding-bottom:5px;margin-bottom:6px}"
    + ".hd img{height:38px;width:38px;object-fit:contain}.org{font-size:13px;font-weight:900;color:#1e1b4b}.sub{font-size:8px;color:#64748b}"
    + ".badge{margin-left:auto;text-align:right}.badge span{display:inline-block;padding:2px 8px;border-radius:4px;font-weight:bold;font-size:9px}"
    + ".grid{display:grid;gap:4px;margin-bottom:6px}.box{border:1px solid #e2e8f0;border-radius:4px;padding:3px 5px}"
    + ".l{font-size:7px;color:#64748b;text-transform:uppercase;letter-spacing:.03em}.v{font-weight:bold;font-size:9.5px}"
    + "h2{font-size:9.5px;color:#3730a3;margin:6px 0 2px;border-bottom:1px solid #c7d2fe;padding-bottom:1px}"
    + "table{width:100%;border-collapse:collapse}th{background:#eef2ff;color:#3730a3;font-size:7.5px;text-align:left;padding:2px 3px}"
    + "td{padding:1.5px 3px;border-bottom:1px solid #f1f5f9;font-size:8.5px;vertical-align:middle}.n{text-align:right;white-space:nowrap}"
    + "tr.t td{font-weight:bold;background:#f8fafc;border-top:1px solid #cbd5e1}.none{color:#94a3b8;font-style:italic;padding:2px 3px}"
    + ".dg{display:grid;grid-template-columns:repeat(10,1fr);gap:2px}.dc{border:1px solid #e2e8f0;border-radius:3px;text-align:center;padding:1px}"
    + ".ok{color:#166534}.bad{color:#b91c1c}@media print{.noprint{display:none!important}}"
    + "</style></head><body>";

  // Header
  h += "<div class='hd'>" + (config.logo ? "<img src='" + config.logo + "'/>" : "")
    + "<div><div class='org'>" + esc(config.fullName || config.orgName || "") + "</div>"
    + "<div class='sub'>" + (config.charityNo ? "Registered Charity No. " + esc(config.charityNo) + " · " : "") + "Rota Sheet · "
    + new Date(s.date).toLocaleDateString("en-GB", { weekday:"long", day:"numeric", month:"long", year:"numeric" }) + "</div></div>"
    + "<div class='badge'><span style='" + (closed ? "background:#dcfce7;color:#166534" : "background:#fef3c7;color:#92400e") + "'>" + (closed ? "CLOSED" : "OPEN — DRAFT") + "</span>"
    + "<div class='sub' style='margin-top:2px'>Open " + dash(s.openingTime) + " · Close " + dash(s.closingTime) + "</div></div></div>";

  // People
  h += "<div class='grid' style='grid-template-columns:repeat(5,1fr)'>"
    + [["Rota Lead", s.rotaLead], ["Rota Support", s.rotaSupport], ["Treasury", s.treasury], ["Priest", s.priest], ["Prasadham", s.prasadhamProvider]]
      .map(([l, v]) => "<div class='box'><div class='l'>" + l + "</div><div class='v'>" + dash(v) + "</div></div>").join("") + "</div>";
  if (sponsors.length) h += "<div class='box' style='margin-bottom:6px'><div class='l'>Sponsors</div><div>" + sponsors.join(", ") + "</div></div>";

  // Money summary
  h += "<h2>Money taken</h2><table><tr><th>Register</th><th>Numbers</th><th class='n'>Count</th><th class='n'>Cash</th><th class='n'>Card</th><th class='n'>Online</th><th class='n'>Total</th></tr>"
    + regRow("Archana" + (at.dayType === "special" ? " (£5)" : " (£3)"), at, at.ticketCount)
    + regRow("Donations", db, db.count)
    + "<tr><td><b>Hundi</b></td><td>—</td><td></td><td class='n'>" + gbp(hundi) + "</td><td></td><td></td><td class='n'><b>" + gbp(hundi) + "</b></td></tr>"
    + regRow("Expenses (out)", ev, ev.count)
    + "<tr class='t'><td colspan='6'>Net revenue (income " + gbp(income) + " − expenses " + gbp(ev.amount) + ")</td><td class='n'>" + gbp(net) + "</td></tr></table>";

  // Donations and expenses, side by side
  h += "<div class='grid' style='grid-template-columns:1fr 1fr;margin-top:2px'>";
  h += "<div><h2>Donations (" + donors.length + ")</h2>" + (donors.length
    ? "<table><tr><th>No.</th><th>Donor</th><th>For</th><th>Date</th><th>Pay</th><th class='n'>£</th></tr>"
      + donors.map(d => "<tr><td>" + esc(d.no) + "</td><td>" + esc(d.name) + "</td><td>" + esc(d.purpose || "General") + "</td><td>" + day(d.date) + "</td><td>" + pay(d.pay) + "</td><td class='n'>" + gbp(d.amount) + "</td></tr>").join("")
      + "</table>"
    : "<div class='none'>No donations</div>") + "</div>";
  h += "<div><h2>Expenses (" + payees.length + ")</h2>" + (payees.length
    ? "<table><tr><th>No.</th><th>Paid to</th><th>For</th><th>Date</th><th>Pay</th><th class='n'>£</th><th>Signed</th></tr>"
      + payees.map(d => "<tr><td>" + esc(d.no) + "</td><td>" + esc(d.name) + "<div class='sub'>" + esc(d.contact) + "</div></td><td>" + esc(d.purpose) + "</td><td>" + day(d.date) + "</td><td>" + pay(d.pay) + "</td><td class='n'>" + gbp(d.amount) + "</td><td>"
        + (d.sig ? "<img src='" + d.sig + "' style='height:16px'/>" : "<span class='bad'>missing</span>") + "</td></tr>").join("")
      + "</table>"
    : "<div class='none'>No expenses</div>") + "</div></div>";

  // Cash check + card/online
  h += "<div class='grid' style='grid-template-columns:2fr 1fr 1fr;margin-top:4px'>"
    + "<div class='box'><div class='l'>Cash check</div><table>"
    + "<tr><td>Opening balance</td><td class='n'>" + gbp(s.openingBalance) + "</td></tr>"
    + "<tr><td>+ Cash in (Archana, Donations, Hundi)</td><td class='n'>" + gbp(cashIn) + "</td></tr>"
    + "<tr><td>− Cash expenses</td><td class='n'>" + gbp(cashOut) + "</td></tr>"
    + "<tr class='t'><td>Expected cash</td><td class='n'>" + gbp(expected) + "</td></tr>"
    + "<tr><td>Counted (denominations)</td><td class='n'>" + gbp(counted) + "</td></tr>"
    + "<tr><td><b>Difference</b></td><td class='n " + (Math.abs(diff) < 0.01 ? "ok'><b>✓ matched" : "bad'><b>" + (diff > 0 ? "+" : "−") + gbp(Math.abs(diff)) + (diff > 0 ? " over" : " short")) + "</b></td></tr></table></div>"
    + "<div class='box'><div class='l'>Card total</div><div class='v' style='font-size:12px'>" + gbp(card) + "</div><div class='l' style='margin-top:4px'>Online total</div><div class='v' style='font-size:12px'>" + gbp(online) + "</div></div>"
    + "<div class='box'><div class='l'>Closing balance</div><div class='v' style='font-size:12px'>" + gbp(s.closingBalance || counted) + "</div><div class='l' style='margin-top:4px'>Head count</div><div class='v' style='font-size:12px'>" + dash(s.headcount || s.headCount) + "</div></div></div>";

  // Denominations
  h += "<h2>Denomination count — " + gbp(counted) + "</h2><div class='dg'>"
    + DENOMS.map(d => { const c = parseFloat(denoms[d.label] || 0); return "<div class='dc'><div class='l'>" + d.label + "</div><div class='v'>" + (c || 0) + "</div><div class='sub'>" + (c ? gbp(c * d.val) : "&nbsp;") + "</div></div>"; }).join("") + "</div>";

  // Notes and signature
  h += "<div class='grid' style='grid-template-columns:1fr 1fr 1fr;margin-top:6px'>"
    + [["Volunteers", s.volunteers], ["To buy", s.toBuy], ["Notes", s.notes]].map(([l, v]) => "<div class='box'><div class='l'>" + l + "</div><div style='white-space:pre-wrap'>" + dash(v) + "</div></div>").join("") + "</div>";
  h += "<div class='grid' style='grid-template-columns:2fr 1fr'><div class='box'><div class='l'>Rota Lead signature — " + dash(s.rotaLead) + "</div><div style='height:36px'>" + sig + "</div></div>"
    + "<div class='box'><div class='l'>Printed</div><div class='v'>" + new Date().toLocaleString("en-GB", { day:"numeric", month:"short", year:"numeric", hour:"2-digit", minute:"2-digit" }) + "</div></div></div>";

  // Shrink to one A4 page (277mm of printable height at 96dpi ≈ 1046px)
  h += "<button class='noprint' onclick='window.print()' style='position:fixed;bottom:16px;right:16px;background:#3730a3;color:#fff;border:0;padding:8px 20px;border-radius:8px;font-size:12px;font-weight:bold;cursor:pointer'>Print / Save as PDF</button>"
    + "<script>window.onload=function(){var h=document.body.scrollHeight,max=1040;if(h>max)document.body.style.zoom=(max/h).toFixed(3);setTimeout(function(){window.print();},300);};<\/script>"
    + "</body></html>";

  const w = window.open("", "_blank");
  if (!w) return false;
  w.document.write(h); w.document.close();
  return true;
}

'''
swap("function RotaSheetTab(", PRINT + "function RotaSheetTab(")
# old printout (sheet list): from its first line to the closing "    };" that ends it
_i = s.index("    const printSheet = function(s) {")
_j = s.index("\n    };\n", _i) + len("\n    };\n")
assert s.count("    const printSheet = function(s) {") == 1 and "w.print()" in s[_i:_j] and "return (" not in s[_i:_j]
s = s[:_i] + s[_j:]
swap('''printSheet(s);''', '''printRotaSheet(s, { config, rotaSheets, sponsorships });''')
# Print from the open sheet as well (laptop form)
swap('''          {onPhoneView && <button onClick={onPhoneView} className="text-sm text-indigo-600 hover:underline font-medium">📱 Phone view</button>}''',
     '''          {onPhoneView && <button onClick={onPhoneView} className="text-sm text-indigo-600 hover:underline font-medium">📱 Phone view</button>}
          <button onClick={()=>{ if (!printRotaSheet(s, { config, rotaSheets, sponsorships })) showToast("Allow pop-ups to print","error"); }}
            className="text-sm bg-indigo-50 border border-indigo-200 text-indigo-700 px-3 py-1.5 rounded-lg hover:bg-indigo-100 font-semibold">🖨 Print / PDF</button>''')

# ── Equal-height cards on the laptop, more room before the bottom boxes ───────
swap('''              <div className="grid md:grid-cols-2 gap-4 mt-4 items-start">''',
     '''              <div className="grid md:grid-cols-2 gap-4 mt-4 mb-6 items-stretch">''')
swap('''    <div className={"rounded-2xl border-2 "+c.border+" "+c.bg+" overflow-hidden"}>''',
     '''    <div className={"rounded-2xl border-2 "+c.border+" "+c.bg+" overflow-hidden h-full flex flex-col"}>''')
swap('''      {(props.donors||[]).length > 0 && (''', '''      <div className="flex-1"/>
      {(props.donors||[]).length > 0 && (''')

# ── Admin: reset a register on an open sheet (to clear test or wrong entries) ─
swap('''// The next receipt number a register will issue''',
     '''// Admin correction: empty a register on an open sheet and start its numbering again
const resetRegister = (r, clear) => ({ ...r, count:0, ticketCount:0, end:r.start, amount:"0.00",
  cashAmount:"0.00", sumupAmount:"0.00", onlineAmount:"0.00", donors:[], payees:[], ...clear });
// The next receipt number a register will issue''')
swap('''      <div className="px-4 pb-2 text-xs text-slate-500">Today so far: <b>{count}</b></div>''',
     '''      <div className="px-4 pb-2 text-xs text-slate-500 flex items-center gap-2">
        <span>Today so far: <b>{count}</b></span>
        {props.onReset && !isClosed && (count > 0 || parseFloat(total) > 0) && (
          <span className="ml-auto"><TypedConfirm word="RESET" label="Reset…" onConfirm={props.onReset}
            warning={"Removes every "+label.toLowerCase()+" entry on this sheet and sets the total back to £0. Use only to clear mistakes."}
            className="text-xs text-red-500 underline"/></span>
        )}
      </div>''')
# Phone cards (admin only)
swap('''        onTaken={function(){up({archanaTickets:{...at,...NO_ORDER}});}}''',
     '''        onTaken={function(){up({archanaTickets:{...at,...NO_ORDER}});}}
        onReset={isAdmin ? function(){up({archanaTickets:resetRegister(at,NO_ORDER)});} : null}''')
swap('''        onTaken={function(){up({donationBook:{...db,...NO_DONATION}});}}''',
     '''        onTaken={function(){up({donationBook:{...db,...NO_DONATION}});}}
        onReset={isAdmin ? function(){up({donationBook:resetRegister(db,NO_DONATION)});} : null}''')
swap('''        onTaken={function(){up({expenseVouchers:takeExpense(ev)});}}''',
     '''        onTaken={function(){up({expenseVouchers:takeExpense(ev)});}}
        onReset={isAdmin ? function(){up({expenseVouchers:resetRegister(ev,NO_EXPENSE)});} : null}''')
# Laptop cards (the laptop form is admin-only)
swap('''                  onTaken={()=>up({donationBook:{...db,...NO_DONATION}})}''',
     '''                  onTaken={()=>up({donationBook:{...db,...NO_DONATION}})}
                  onReset={()=>up({donationBook:resetRegister(db,NO_DONATION)})}''')
swap('''                  onTaken={()=>up({expenseVouchers:takeExpense(ev)})}''',
     '''                  onTaken={()=>up({expenseVouchers:takeExpense(ev)})}
                  onReset={()=>up({expenseVouchers:resetRegister(ev,NO_EXPENSE)})}''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
