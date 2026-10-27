"""General donations and UK Gift Aid.
- Book Pooja: a "General donation" entry (no service; any amount; date/occasion optional)
- Gift Aid declaration (UK taxpayer, house name/number + postcode) on general donations,
  on the Rota Sheet and on Book Pooja; Gift Aid isn't offered on payments for a service
- Finance: Gift Aid donations listed with a CSV in HMRC's schedule columns

Usage: python3 tools/giftaid-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def swap(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


# ── Shared Gift Aid pieces ────────────────────────────────────────────────────
GA = r'''// ─── UK Gift Aid ────────────────────────────────────────────────────────────
// Offered on general donations only (a payment for a service usually can't be Gift Aided).
// HMRC needs the donor's name, house name or number and postcode, and their declaration.
const UK_POSTCODE = /^[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}$/i;
const gaOk = (on, house, postcode) => !on || (!!(house||"").trim() && UK_POSTCODE.test((postcode||"").trim()));
const giftAidText = org => "I want to Gift Aid my donation and any donations I make in the future or have made in the past 4 years to "
  + (org || "this charity") + ". I am a UK taxpayer and understand that if I pay less Income Tax and/or Capital Gains Tax than the amount of Gift Aid claimed on all my donations in that tax year it is my responsibility to pay any difference.";
function GiftAidFields({ on, house, postcode, amount, org, disabled, onChange }) {
  const extra = parseFloat(amount||0) * 0.25;
  const ic = "w-full border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-300 disabled:bg-slate-100";
  return (
    <div className={"rounded-lg border p-2 space-y-1.5 "+(on ? "border-emerald-300 bg-emerald-50" : "border-slate-200 bg-white")}>
      <label className="flex items-start gap-2 text-sm cursor-pointer">
        <input type="checkbox" checked={!!on} disabled={disabled} onChange={e=>onChange("orderGiftAid", e.target.checked)} className="mt-0.5 accent-emerald-600"/>
        <span><b>Gift Aid it</b>{extra > 0 ? " — adds £"+extra.toFixed(2)+" at no cost to the donor" : " — adds 25% at no cost to the donor"}. UK taxpayers only.</span>
      </label>
      {on && <>
        <p className="text-xs text-slate-600 leading-snug">{giftAidText(org)}</p>
        <div className="grid grid-cols-2 gap-1.5">
          <input value={house||""} onChange={e=>onChange("orderGaHouse", e.target.value)} disabled={disabled} placeholder="House name or number *" className={ic}/>
          <input value={postcode||""} onChange={e=>onChange("orderGaPostcode", e.target.value.toUpperCase())} disabled={disabled} placeholder="Postcode *"
            className={ic+(postcode && !UK_POSTCODE.test(postcode.trim()) ? " border-red-300" : "")}/>
        </div>
      </>}
    </div>
  );
}

'''
swap("const isBooking = o => o && o.type === \"booking\";", GA + "const isBooking = o => o && o.type === \"booking\";")

# ── Rota Sheet donations ──────────────────────────────────────────────────────
swap('''const NO_DONATION = { ...NO_ORDER, perAmount:"", orderName:"", orderContact:"", orderServiceId:"", orderServiceName:"", orderServiceCharge:"", orderDate:"" };''',
     '''const NO_DONATION = { ...NO_ORDER, perAmount:"", orderName:"", orderContact:"", orderServiceId:"", orderServiceName:"", orderServiceCharge:"", orderDate:"",
  orderGiftAid:false, orderGaHouse:"", orderGaPostcode:"" };''')
swap('''  .map((p, i, all) => i === all.length-1 ? { ...p, purpose: db.orderServiceName || "General", serviceId: db.orderServiceId || "", date: db.orderDate || sheetDate } : p);''',
     '''  .map((p, i, all) => i === all.length-1 ? { ...p, purpose: db.orderServiceName || "General", serviceId: db.orderServiceId || "", date: db.orderDate || sheetDate,
    ...(db.orderGiftAid && !db.orderServiceId ? { giftAid: true, gaHouse: (db.orderGaHouse||"").trim(), gaPostcode: (db.orderGaPostcode||"").trim().toUpperCase() } : {}) } : p);''')
swap('''  && parseFloat((r||{}).perAmount||0) >= parseFloat((r||{}).orderServiceCharge||0);''',
     '''  && parseFloat((r||{}).perAmount||0) >= parseFloat((r||{}).orderServiceCharge||0)
  && (!!(r||{}).orderServiceId || gaOk((r||{}).orderGiftAid, (r||{}).orderGaHouse, (r||{}).orderGaPostcode));''')
swap('''    orderPurpose:expense&&expense.purpose, orderDate:expense&&expense.date, orderServiceCharge:props.serviceCharge});''',
     '''    orderPurpose:expense&&expense.purpose, orderDate:expense&&expense.date, orderServiceCharge:props.serviceCharge, orderServiceId:props.serviceId,
    orderGiftAid:props.giftAid&&props.giftAid.on, orderGaHouse:props.giftAid&&props.giftAid.house, orderGaPostcode:props.giftAid&&props.giftAid.postcode});''')
swap('''          {props.donationDate !== undefined && (''',
     '''          {props.giftAid && !props.serviceId && (
            <GiftAidFields on={props.giftAid.on} house={props.giftAid.house} postcode={props.giftAid.postcode} amount={perAmt}
              org={props.orgName} disabled={isClosed||open} onChange={onDonor}/>
          )}
          {props.donationDate !== undefined && (''')
# both donation cards (phone and laptop)
swap('''        services={sevas} serviceId={db.orderServiceId} serviceCharge={db.orderServiceCharge} donationDate={db.orderDate||s.date}''',
     '''        services={sevas} serviceId={db.orderServiceId} serviceCharge={db.orderServiceCharge} donationDate={db.orderDate||s.date}
        giftAid={{on:db.orderGiftAid, house:db.orderGaHouse, postcode:db.orderGaPostcode}} orgName={orgName}''')
swap('''                  services={sevas||[]} serviceId={db.orderServiceId} serviceCharge={db.orderServiceCharge} donationDate={db.orderDate||s.date}''',
     '''                  services={sevas||[]} serviceId={db.orderServiceId} serviceCharge={db.orderServiceCharge} donationDate={db.orderDate||s.date}
                  giftAid={{on:db.orderGiftAid, house:db.orderGaHouse, postcode:db.orderGaPostcode}} orgName={config.fullName||config.orgName}''')
# the phone sheet needs the organisation's name for the declaration
swap('''function RotaSheetMobile({ sheet, upSheet, onBack, archanaiReg, donationReg, expenseReg, upRegs, registers, showToast, cashInHand, upCashInHand, isAdmin, onFullForm, sevas=[] }) {''',
     '''function RotaSheetMobile({ sheet, upSheet, onBack, archanaiReg, donationReg, expenseReg, upRegs, registers, showToast, cashInHand, upCashInHand, isAdmin, onFullForm, sevas=[], orgName="" }) {''')
swap('''<RotaSheetMobile sevas={sevas||[]} sheet={currentSheet}''', '''<RotaSheetMobile orgName={(config||{}).fullName||(config||{}).orgName||""} sevas={sevas||[]} sheet={currentSheet}''')
# donor list on the card and on the printout mark Gift Aid
swap('''<span className="flex-1 truncate">{d.name}{d.purpose &&''', '''<span className="flex-1 truncate">{d.name}{d.giftAid && <span className="text-emerald-600 font-semibold"> · Gift Aid</span>}{d.purpose &&''')
swap('''donors.map(d => "<tr><td>" + esc(d.no) + "</td><td>" + esc(d.name) + "</td>''', '''donors.map(d => "<tr><td>" + esc(d.no) + "</td><td>" + esc(d.name) + (d.giftAid ? " <b>(GA)</b>" : "") + "</td>''')

# ── Finance: Gift Aid donations and the HMRC schedule CSV ─────────────────────
GAP = r'''// Gift Aid report: every donation flagged for Gift Aid — taken on closed Rota Sheets, and
// pledged through accepted Book Pooja requests (whose payment the admin should check) —
// with a CSV in HMRC's schedule columns for the claim
function GiftAidPanel({ sheets, bookings=[] }) {
  const [withBookings, setWithBookings] = useState(false);
  const all = sheets.flatMap(sh => ((sh.donationBook||{}).donors||[]).filter(d => d.giftAid).map(d => ({ ...d, sheetDate: sh.date, source:"Rota Sheet " + (d.no||"") })))
    .concat(bookings.filter(o => o.giftAid && o.status === "accepted" && parseFloat(o.amount) > 0)
      .map(o => ({ name:o.name, gaHouse:o.gaHouse, gaPostcode:o.gaPostcode, amount:o.amount, sheetDate:o.date, source:"Book Pooja", booking:true })))
    .sort((a, b) => (a.sheetDate||"").localeCompare(b.sheetDate||""));
  const rows = withBookings ? all : all.filter(d => !d.booking);   // what the CSV and totals cover
  const total = rows.reduce((t, d) => t + parseFloat(d.amount||0), 0);
  const ddmmyy = d => { const x = new Date((d||"").slice(0,10)+"T12:00:00"); return String(x.getDate()).padStart(2,"0")+"/"+String(x.getMonth()+1).padStart(2,"0")+"/"+String(x.getFullYear()).slice(2); };
  const csv = () => {
    const q = v => '"' + String(v==null?"":v).replace(/"/g,'""') + '"';
    const lines = [["Title","First name","Last name","House name or number","Postcode","Aggregated donations","Sponsored event","Donation date","Amount"].map(q).join(",")]
      .concat(rows.map(d => { const parts = (d.name||"").trim().split(/\s+/); const last = parts.length > 1 ? parts.pop() : "";
        return ["", parts.join(" "), last, d.gaHouse, d.gaPostcode, "", "", ddmmyy(d.sheetDate), parseFloat(d.amount||0).toFixed(2)].map(q).join(","); }));
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([lines.join("\r\n")], { type:"text/csv" }));
    a.download = "gift-aid-donations.csv"; a.click();
  };
  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-3">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex-1">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">🇬🇧 Gift Aid report</h3>
          <p className="text-xs text-slate-400 mt-0.5">Every donation with a Gift Aid declaration in this period. The claim is 25% of the total.</p>
          {all.some(d => d.booking) && <label className="flex items-center gap-1.5 text-xs text-slate-600 mt-1">
            <input type="checkbox" checked={withBookings} onChange={e=>setWithBookings(e.target.checked)}/> Include Book Pooja donations (check the money arrived first)</label>}
        </div>
        <div className="text-right"><div className="text-xs text-slate-400">{rows.length} donation{rows.length!==1?"s":""} · £{total.toFixed(2)}</div><div className="text-lg font-black text-emerald-700">Claim £{(total*0.25).toFixed(2)}</div></div>
        {rows.length > 0 && <button onClick={csv} className="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-2 rounded-xl text-xs font-bold">⬇ CSV for HMRC</button>}
      </div>
      {all.length === 0 ? <p className="text-sm text-slate-400">No Gift Aid donations in this period.</p> : (
        <div className="overflow-x-auto"><table className="w-full text-xs">
          <thead><tr className="text-slate-500 border-b border-slate-100"><th className="text-left py-1.5">Date</th><th className="text-left">Donor</th><th className="text-left">House</th><th className="text-left">Postcode</th><th className="text-left">From</th><th className="text-right">£</th></tr></thead>
          <tbody>{all.map((d, i) => <tr key={i} className={"border-b border-slate-50 "+(d.booking && !withBookings ? "text-slate-400" : "")}><td className="py-1.5 whitespace-nowrap">{ddmmyy(d.sheetDate)}</td><td>{d.name}</td><td>{d.gaHouse}</td><td>{d.gaPostcode}</td><td className="whitespace-nowrap">{d.source}</td><td className="text-right font-semibold">{parseFloat(d.amount||0).toFixed(2)}</td></tr>)}</tbody>
        </table></div>
      )}
    </div>
  );
}

'''
swap("// ─── Hundi collections: the collection box, counted now and then", GAP + "// ─── Hundi collections: the collection box, counted now and then")
swap('''      {hundiPanel}

      {/* KPI summary */}''', '''      {hundiPanel}
      <GiftAidPanel sheets={sorted} bookings={(generalOffers||[]).filter(function(o){ return isBooking(o) && (filterMonth==="all" || (o.date||"").slice(0,7)===filterMonth); })}/>

      {/* KPI summary */}''')

# ── Book Pooja: General donation (any amount) with Gift Aid ───────────────────
swap('''  const items = [
    ...sevas.map(sv => ({ key:"s:"+sv.id, kind:"service", id:sv.id, name:sv.name, charge:sv.charge })),''',
     '''  const items = [
    { key:"g:general", kind:"general", id:"general", name:"General donation", charge:"" },
    ...sevas.map(sv => ({ key:"s:"+sv.id, kind:"service", id:sv.id, name:sv.name, charge:sv.charge })),''')
swap('''  const blank = { itemKey:"", date:"", occasion:"", occasionOther:"", name: me.name || currentUser.name || "",''',
     '''  const blank = { itemKey:"", date:"", occasion:"", occasionOther:"", amount:"", orderGiftAid:false, orderGaHouse:"", orderGaPostcode:"", name: me.name || currentUser.name || "",''')
swap('''  const problem = !item ? "Choose a service or sponsorship" : !f.date ? "Choose the date" : f.date < today ? "The date has passed"
    : !occasion ? "Tell us the occasion" :''',
     '''  const general = item && item.kind === "general";   // just a donation: date and occasion are optional
  const problem = !item ? "Choose a service or sponsorship" : (!f.date && !general) ? "Choose the date" : (f.date && f.date < today) ? "The date has passed"
    : (!occasion && !general) ? "Tell us the occasion" : (general && f.orderGiftAid && !(parseFloat(f.amount) > 0)) ? "Enter the amount for Gift Aid"
    : !gaOk(general && f.orderGiftAid, f.orderGaHouse, f.orderGaPostcode) ? "Enter your house name or number and a UK postcode for Gift Aid" :''')
swap('''      date:f.date, occasion, item:{ kind:item.kind, id:item.id, name:item.name, charge:item.charge||"" }, gothram:f.gothram.trim(), nakshatram:f.nakshatram.trim(),''',
     '''      date:f.date || today, occasion: occasion || (general ? "Donation" : ""), item:{ kind:item.kind, id:item.id, name:item.name, charge:item.charge||"" },
      amount: general && parseFloat(f.amount) > 0 ? parseFloat(f.amount).toFixed(2) : "",
      ...(general && f.orderGiftAid ? { giftAid:true, gaHouse:f.orderGaHouse.trim(), gaPostcode:f.orderGaPostcode.trim().toUpperCase() } : {}),
      gothram:f.gothram.trim(), nakshatram:f.nakshatram.trim(),''')
swap('''              {sevas.length > 0 && <optgroup label="Services">''', '''              <option value="g:general">🙏 General donation (any amount)</option>
              {sevas.length > 0 && <optgroup label="Services">''')
swap('''          {item && item.charge && <div className="sm:col-span-2 text-sm bg-orange-50 border border-orange-200 rounded-lg px-3 py-2 text-orange-800">Suggested donation: <b>£{item.charge}</b> — paid at the temple on the day.</div>}''',
     '''          {item && item.charge && <div className="sm:col-span-2 text-sm bg-orange-50 border border-orange-200 rounded-lg px-3 py-2 text-orange-800">Suggested donation: <b>£{item.charge}</b> — paid at the temple on the day.</div>}
          {general && <>
            <label className={lbl}>Amount £ (optional)<input type="number" min="0" step="0.01" value={f.amount} onChange={e=>setF({...f,amount:e.target.value})} placeholder="Any amount" className={ic}/></label>
            <div className="sm:col-span-2"><GiftAidFields on={f.orderGiftAid} house={f.orderGaHouse} postcode={f.orderGaPostcode} amount={f.amount}
              org={config.fullName||config.orgName} onChange={(k,v)=>setF(prev=>({...prev,[k]:v}))}/></div>
          </>}''')
swap('''          <label className={lbl}>Date *<input type="date" min={today}''', '''          <label className={lbl}>Date {general ? "(optional)" : "*"}<input type="date" min={today}''')
swap('''          <label className={lbl}>Occasion *''', '''          <label className={lbl}>Occasion {general ? "(optional)" : "*"}''')
# review and lists show amount and Gift Aid
swap('''            <div><b>{item.name}</b>{item.charge ? " — suggested donation £"+item.charge : ""}</div>
            <div>{bookingDate(f.date)} · {occasion}</div>''',
     '''            <div><b>{item.name}</b>{item.charge ? " — suggested donation £"+item.charge : ""}{general && parseFloat(f.amount) > 0 ? " — £"+parseFloat(f.amount).toFixed(2) : ""}</div>
            <div>{bookingDate(f.date || today)}{occasion ? " · "+occasion : ""}</div>
            {general && f.orderGiftAid && <div className="text-emerald-700">🇬🇧 Gift Aid declared · {f.orderGaHouse}, {f.orderGaPostcode}</div>}''')
swap('''              <div className="font-bold text-slate-800">{o.item.name}{o.item.charge ? <span className="font-normal text-slate-500"> · £{o.item.charge}</span> : ""}</div>''',
     '''              <div className="font-bold text-slate-800">{o.item.name}{o.item.charge ? <span className="font-normal text-slate-500"> · £{o.item.charge}</span> : ""}{o.amount ? <span className="font-normal text-slate-500"> · £{o.amount}</span> : ""}</div>
              {o.giftAid && <div className="text-xs text-emerald-700 font-semibold">🇬🇧 Gift Aid declared · {o.gaHouse}, {o.gaPostcode}</div>}''')


# Finance gets the bookings (for Gift Aid from Book Pooja)
swap('''function MDFinance({ rotaSheets=[], hundi=[], upHundi, showToast }) {''', '''function MDFinance({ rotaSheets=[], hundi=[], upHundi, showToast, generalOffers=[] }) {''')
swap('''<MDFinance      rotaSheets={rotaSheets} hundi={hundi} upHundi={upHundi} showToast={showToast}/>}''', '''<MDFinance      rotaSheets={rotaSheets} hundi={hundi} upHundi={upHundi} showToast={showToast} generalOffers={generalOffers}/>}''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
