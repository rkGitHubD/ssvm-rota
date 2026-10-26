// ─── Pooja bookings ──────────────────────────────────────────────────────────
// A member asks for a pooja on a date; the admin accepts or declines, and can
// confirm with the devotee on WhatsApp. Stored with the offers (rota-offers), which
// every member may save:
//   { id, type:"booking", memberId, name, phone, email, date, occasion, item:{kind,id,name,charge},
//     gothram, nakshatram, notes, status:"pending"|"accepted"|"declined"|"cancelled",
//     createdAt, resolvedAt, adminNote }
const isBooking = o => o && o.type === "booking";
const OCCASIONS = ["Birthday","Wedding anniversary","House warming","New vehicle","Exam / new job","In memory of a loved one","Festival","Other"];
const bookingDate = d => new Date(d+"T12:00:00").toLocaleDateString("en-GB",{weekday:"long",day:"numeric",month:"long",year:"numeric"});
// A UK number written for WhatsApp links (07700 900123 → 447700900123)
const waNumber = p => { let d = String(p||"").replace(/\D/g,""); if (d.startsWith("00")) d = d.slice(2); else if (d.startsWith("0")) d = "44" + d.slice(1); return d; };

function BookPooja({ sevas=[], sponsorships=[], members=[], generalOffers=[], upGeneralOffers, currentUser, config={}, showToast }) {
  const me = members.find(m => m.id === currentUser.memberId) || {};
  const blank = { itemKey:"", date:"", occasion:"", occasionOther:"", name: me.name || currentUser.name || "", phone: me.phone || "", email: me.email || "", gothram:"", nakshatram:"", notes:"" };
  const [f, setF] = useState(blank);
  const [review, setReview] = useState(false);
  const today = new Date().toISOString().slice(0,10);
  // What can be booked: the services (with their suggested donation) and the sponsorship areas
  const items = [
    ...sevas.map(sv => ({ key:"s:"+sv.id, kind:"service", id:sv.id, name:sv.name, charge:sv.charge })),
    ...sponsorships.filter(a => a.name).map(a => ({ key:"p:"+a.id, kind:"sponsorship", id:a.id, name:a.name, charge:"" })),
  ];
  const item = items.find(i => i.key === f.itemKey);
  const occasion = f.occasion === "Other" ? f.occasionOther.trim() : f.occasion;
  const problem = !item ? "Choose a service or sponsorship" : !f.date ? "Choose the date" : f.date < today ? "The date has passed"
    : !occasion ? "Tell us the occasion" : !f.name.trim() ? "Enter your name" : (f.phone.replace(/\D/g,"").length < 7) ? "Enter a phone number"
    : !/^\S+@\S+\.\S+$/.test(f.email.trim()) ? "Enter a valid email" : "";
  const send = () => {
    upGeneralOffers([...(generalOffers||[]), { id:uid(), type:"booking", memberId:currentUser.memberId, name:f.name.trim(), phone:f.phone.trim(), email:f.email.trim(),
      date:f.date, occasion, item:{ kind:item.kind, id:item.id, name:item.name, charge:item.charge||"" }, gothram:f.gothram.trim(), nakshatram:f.nakshatram.trim(),
      notes:f.notes.trim(), status:"pending", createdAt:new Date().toISOString() }]);
    setF(blank); setReview(false);
    showToast("Booking request sent — the temple will confirm");
  };
  const mine = (generalOffers||[]).filter(o => isBooking(o) && o.memberId === currentUser.memberId).slice().reverse();
  const cancel = id => upGeneralOffers((generalOffers||[]).map(o => o.id === id ? { ...o, status:"cancelled", resolvedAt:new Date().toISOString() } : o));
  const ic = "w-full border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-orange-300";
  const lbl = "text-xs font-semibold text-slate-600";
  const STATUS = { pending:["⏳ Waiting for the temple","bg-amber-100 text-amber-700"], accepted:["✅ Confirmed","bg-emerald-100 text-emerald-700"],
                   declined:["❌ Not possible","bg-red-100 text-red-600"], cancelled:["Cancelled","bg-slate-100 text-slate-500"] };
  return (
    <div className="space-y-5 max-w-2xl">
      <div>
        <h2 className="text-xl font-bold text-slate-800">🪔 Book a Pooja</h2>
        <p className="text-sm text-slate-500 mt-0.5">Ask for a pooja or sponsorship on a special day. The temple will confirm your booking.</p>
      </div>
      {items.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center text-slate-400">No services are set up for booking yet.</div>
      ) : !review ? (
        <div className="bg-white rounded-2xl border border-orange-200 shadow-sm p-5 grid sm:grid-cols-2 gap-3">
          <label className={lbl+" sm:col-span-2"}>Service or sponsorship *
            <select value={f.itemKey} onChange={e=>setF({...f,itemKey:e.target.value})} className={ic}>
              <option value="">Choose…</option>
              {sevas.length > 0 && <optgroup label="Services">{items.filter(i=>i.kind==="service").map(i => <option key={i.key} value={i.key}>{i.name}{i.charge ? " — £"+i.charge : ""}</option>)}</optgroup>}
              {items.some(i=>i.kind==="sponsorship") && <optgroup label="Sponsorships">{items.filter(i=>i.kind==="sponsorship").map(i => <option key={i.key} value={i.key}>{i.name}</option>)}</optgroup>}
            </select></label>
          {item && item.charge && <div className="sm:col-span-2 text-sm bg-orange-50 border border-orange-200 rounded-lg px-3 py-2 text-orange-800">Suggested donation: <b>£{item.charge}</b> — paid at the temple on the day.</div>}
          <label className={lbl}>Date *<input type="date" min={today} value={f.date} onChange={e=>setF({...f,date:e.target.value})} className={ic}/></label>
          <label className={lbl}>Occasion *
            <select value={f.occasion} onChange={e=>setF({...f,occasion:e.target.value})} className={ic}>
              <option value="">Choose…</option>{OCCASIONS.map(o => <option key={o}>{o}</option>)}
            </select></label>
          {f.occasion === "Other" && <label className={lbl+" sm:col-span-2"}>Your occasion *<input value={f.occasionOther} onChange={e=>setF({...f,occasionOther:e.target.value})} placeholder="e.g. Child's first birthday" className={ic}/></label>}
          <label className={lbl}>Name *<input value={f.name} onChange={e=>setF({...f,name:e.target.value})} className={ic}/></label>
          <label className={lbl}>Phone *<input value={f.phone} onChange={e=>setF({...f,phone:e.target.value})} inputMode="tel" placeholder="07700 900123" className={ic}/></label>
          <label className={lbl+" sm:col-span-2"}>Email *<input value={f.email} onChange={e=>setF({...f,email:e.target.value})} inputMode="email" className={ic}/></label>
          <label className={lbl}>Gothram (optional)<input value={f.gothram} onChange={e=>setF({...f,gothram:e.target.value})} className={ic}/></label>
          <label className={lbl}>Nakshatram (optional)<input value={f.nakshatram} onChange={e=>setF({...f,nakshatram:e.target.value})} className={ic}/></label>
          <label className={lbl+" sm:col-span-2"}>Anything else (optional)<textarea rows={2} value={f.notes} onChange={e=>setF({...f,notes:e.target.value})} placeholder="Names to include in the sankalpam, timing…" className={ic+" resize-none"}/></label>
          <div className="sm:col-span-2">
            {problem && <p className="text-xs text-slate-500 mb-2">{problem}</p>}
            <button onClick={()=>setReview(true)} disabled={!!problem} className="w-full bg-orange-500 hover:bg-orange-600 text-white rounded-xl py-2.5 text-sm font-bold disabled:opacity-40">Review booking</button>
          </div>
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-orange-300 shadow-sm p-5 space-y-3">
          <h3 className="font-bold text-slate-800">Please check your booking</h3>
          <div className="text-sm space-y-1">
            <div><b>{item.name}</b>{item.charge ? " — suggested donation £"+item.charge : ""}</div>
            <div>{bookingDate(f.date)} · {occasion}</div>
            <div>{f.name} · {f.phone} · {f.email}</div>
            {(f.gothram || f.nakshatram) && <div>{f.gothram && "Gothram: "+f.gothram}{f.gothram && f.nakshatram && " · "}{f.nakshatram && "Nakshatram: "+f.nakshatram}</div>}
            {f.notes && <div className="text-slate-500 italic">"{f.notes}"</div>}
          </div>
          <div className="flex gap-2">
            <button onClick={send} className="flex-1 bg-orange-500 hover:bg-orange-600 text-white rounded-xl py-2.5 text-sm font-bold">✓ Confirm and send</button>
            <button onClick={()=>setReview(false)} className="flex-1 bg-white border border-slate-200 text-slate-600 rounded-xl py-2.5 text-sm font-medium">Change</button>
          </div>
        </div>
      )}
      {mine.length > 0 && (
        <div className="space-y-2">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">My bookings</div>
          {mine.map(o => (
            <div key={o.id} className="bg-white border border-slate-200 rounded-xl px-3 py-2 text-sm flex items-start gap-2">
              <div className="flex-1 min-w-0">
                <div className="font-semibold text-slate-700">{o.item.name} · {bookingDate(o.date)}</div>
                <div className="text-xs text-slate-500">{o.occasion}</div>
                {o.adminNote && <div className="text-xs text-slate-600 mt-0.5">Temple: {o.adminNote}</div>}
              </div>
              <span className={"text-xs font-semibold px-2 py-0.5 rounded-full whitespace-nowrap "+(STATUS[o.status]||STATUS.pending)[1]}>{(STATUS[o.status]||STATUS.pending)[0]}</span>
              {o.status === "pending" && <button onClick={()=>cancel(o.id)} className="text-xs text-slate-400 underline">Cancel</button>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Admin: booking requests ───────────────────────────────────────────────────
function MDBookings({ generalOffers=[], upGeneralOffers, config={}, showToast }) {
  const [filter, setFilter] = useState("pending");
  const [noteFor, setNoteFor] = useState(null);   // { id, action }
  const [note, setNote] = useState("");
  const all = (generalOffers||[]).filter(isBooking).slice().sort((a, b) => a.date.localeCompare(b.date));
  const shown = filter === "all" ? all : all.filter(o => o.status === filter);
  const org = config.fullName || config.orgName || "the temple";
  const setStatus = (o, status) => {
    upGeneralOffers((generalOffers||[]).map(x => x.id === o.id ? { ...x, status, adminNote: note.trim(), resolvedAt: new Date().toISOString() } : x));
    setNoteFor(null); setNote("");
    showToast(status === "accepted" ? "Booking accepted — confirm with them on WhatsApp" : "Booking declined");
  };
  const waText = o => o.status === "declined"
    ? "🙏 Namaste " + o.name + ", thank you for your booking request at " + org + " for " + o.item.name + " on " + bookingDate(o.date) + ". Unfortunately we can't accommodate it" + (o.adminNote ? ": " + o.adminNote : ".") + " Please contact us to arrange another date."
    : "🙏 Namaste " + o.name + ", your booking at " + org + " is confirmed: " + o.item.name + " on " + bookingDate(o.date) + " (" + o.occasion + ")."
      + (o.item.charge ? " Suggested donation £" + o.item.charge + ", paid at the temple." : "") + (o.adminNote ? " " + o.adminNote.trim().replace(/([^.!?])$/, "$1.") : "") + " We look forward to seeing you.";
  const STATUS = { pending:"bg-amber-100 text-amber-700", accepted:"bg-emerald-100 text-emerald-700", declined:"bg-red-100 text-red-600", cancelled:"bg-slate-100 text-slate-500" };
  const LABEL = { pending:"Pending", accepted:"Accepted", declined:"Declined", cancelled:"Cancelled by them" };
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 flex-wrap">
        <h2 className="text-lg font-bold text-slate-800 flex-1">🪔 Pooja bookings</h2>
        {[["pending","Pending"],["accepted","Accepted"],["declined","Declined"],["all","All"]].map(([k, l]) => (
          <button key={k} onClick={()=>setFilter(k)} className={"text-xs px-3 py-1.5 rounded-full font-semibold border "+(filter===k?"bg-indigo-600 text-white border-indigo-600":"bg-white text-slate-600 border-slate-200")}>
            {l} {k !== "all" && <span className="opacity-75">({all.filter(o=>o.status===k).length})</span>}</button>
        ))}
      </div>
      {shown.length === 0 ? <div className="bg-white rounded-2xl border border-slate-200 p-10 text-center text-slate-400 text-sm">No {filter === "all" ? "" : LABEL[filter].toLowerCase()+" "}bookings.</div> : shown.map(o => (
        <div key={o.id} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 space-y-2">
          <div className="flex items-start gap-2 flex-wrap">
            <div className="flex-1 min-w-0">
              <div className="font-bold text-slate-800">{o.item.name}{o.item.charge ? <span className="font-normal text-slate-500"> · £{o.item.charge}</span> : ""}</div>
              <div className="text-sm text-slate-600">{bookingDate(o.date)} · {o.occasion}</div>
            </div>
            <span className={"text-xs font-semibold px-2 py-0.5 rounded-full "+STATUS[o.status]}>{LABEL[o.status]}</span>
          </div>
          <div className="text-sm text-slate-600">{o.name} · <a href={"tel:"+o.phone} className="text-indigo-600">{o.phone}</a> · <a href={"mailto:"+o.email} className="text-indigo-600">{o.email}</a></div>
          {(o.gothram || o.nakshatram) && <div className="text-xs text-slate-500">{o.gothram && "Gothram: "+o.gothram}{o.gothram && o.nakshatram && " · "}{o.nakshatram && "Nakshatram: "+o.nakshatram}</div>}
          {o.notes && <div className="text-xs text-slate-500 italic">"{o.notes}"</div>}
          {o.adminNote && o.status !== "pending" && <div className="text-xs text-slate-600">Your note: {o.adminNote}</div>}
          {noteFor && noteFor.id === o.id ? (
            <div className="flex gap-2 flex-wrap">
              <input value={note} onChange={e=>setNote(e.target.value)} autoFocus placeholder={noteFor.action === "accepted" ? "Note for them (optional), e.g. arrive by 6pm" : "Reason (shown to them)"}
                className="flex-1 min-w-0 border border-slate-200 rounded-lg px-2 py-1.5 text-sm"/>
              <button onClick={()=>setStatus(o, noteFor.action)} className={"text-xs text-white px-3 py-1.5 rounded-lg font-bold "+(noteFor.action==="accepted"?"bg-emerald-600":"bg-red-600")}>{noteFor.action === "accepted" ? "Accept" : "Decline"}</button>
              <button onClick={()=>setNoteFor(null)} className="text-xs text-slate-500">Cancel</button>
            </div>
          ) : (
            <div className="flex gap-2 flex-wrap">
              {o.status === "pending" && <>
                <button onClick={()=>{ setNoteFor({ id:o.id, action:"accepted" }); setNote(""); }} className="text-xs bg-emerald-600 text-white px-3 py-1.5 rounded-lg font-bold">✓ Accept</button>
                <button onClick={()=>{ setNoteFor({ id:o.id, action:"declined" }); setNote(""); }} className="text-xs bg-red-50 border border-red-200 text-red-600 px-3 py-1.5 rounded-lg font-semibold">Decline</button>
              </>}
              {(o.status === "accepted" || o.status === "declined") && (
                <a href={"https://wa.me/" + waNumber(o.phone) + "?text=" + encodeURIComponent(waText(o))} target="_blank" rel="noopener"
                  className="text-xs bg-[#25D366] hover:bg-[#1EBE5A] text-white px-3 py-1.5 rounded-lg font-bold flex items-center gap-1.5"><WhatsAppIcon className="w-4 h-4"/> Send on WhatsApp</a>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

