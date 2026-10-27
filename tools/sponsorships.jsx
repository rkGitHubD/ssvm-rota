// ─── Sponsorships ────────────────────────────────────────────────────────────
// Data (unchanged): sponsorships = [{ id, name, notes, serviceId?, donations:[{ id, donor, contact, amount,
//   frequency, rotaDates[], startDate, endDate, customWeeks, notes }] }]. Each "area" is an item people
// sponsor (Milk, Flowers, a service…); rotaDates are the days the sponsor shows on the Rota Sheet.
const SPONSOR_ITEM_IDEAS = ["Milk","Pooja items","Flowers","Fruits","Coconuts","Prasadham","Oil / ghee"];
// The days a sponsorship covers, from its frequency, start/end and number of weeks
function sponsorDates(d) {
  if (d.frequency === "one-off") return (d.rotaDates||[]).slice().sort();
  if (!d.startDate) return [];
  const weeks = parseInt(d.customWeeks) || null;
  const step = d.frequency === "weekly" ? 7 : d.frequency === "monthly" ? 28 : d.frequency === "quarterly" ? 91 : 7;
  const end = d.endDate ? new Date(d.endDate+"T12:00:00") : null;
  const out = [];
  for (let cur = new Date(d.startDate+"T12:00:00"); out.length < 200; cur = new Date(cur.getTime() + step*86400000)) {
    if (end && cur > end) break;
    if (weeks && out.length >= weeks) break;
    if (!end && !weeks && out.length >= 52) break;
    out.push(cur.toISOString().slice(0,10));
  }
  return out;
}
// Past / active / upcoming, and how many of its days are done
function sponsorStatus(dates) {
  const today = new Date().toISOString().slice(0,10);
  const done = dates.filter(x => x < today).length;
  const next = dates.find(x => x >= today) || "";
  const status = !dates.length ? "No dates" : done === dates.length ? "Completed" : done === 0 ? "Upcoming" : "Active";
  return { done, next, status, first: dates[0] || "", last: dates[dates.length-1] || "" };
}
const SP_STATUS_CLS = { Completed:"bg-slate-100 text-slate-600", Active:"bg-emerald-100 text-emerald-700", Upcoming:"bg-indigo-100 text-indigo-700", "No dates":"bg-amber-100 text-amber-700" };
const shortDay = x => x ? new Date(x+"T12:00:00").toLocaleDateString("en-GB",{day:"numeric",month:"short",year:"2-digit"}) : "—";

// New / edit form — defined at the top level so typing never loses focus
function SponsorshipForm({ initial, items, sevas, onSave, onCancel, showToast }) {
  const [f, setF] = useState(initial);
  const [oneDate, setOneDate] = useState("");
  const ic = "w-full border border-slate-200 rounded-lg px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-indigo-300";
  const lbl = "text-xs font-semibold text-slate-600";
  const dates = sponsorDates(f);
  const save = () => {
    if (!f.donor.trim()) return showToast("Enter the donor's name","error");
    if (!f.itemKey) return showToast("Choose what they are sponsoring","error");
    if (f.itemKey === "new" && !f.newItem.trim()) return showToast("Type the new item's name","error");
    if (!(parseFloat(f.amount) >= 0) || f.amount === "") return showToast("Enter the amount paid","error");
    if (!dates.length) return showToast(f.frequency === "one-off" ? "Add at least one date" : "Choose a start date","error");
    onSave({ ...f, amount: parseFloat(f.amount).toFixed(2), rotaDates: dates });
  };
  return (
    <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 grid sm:grid-cols-2 gap-3">
      <label className={lbl}>Donor name *<input value={f.donor} onChange={e=>setF({...f,donor:e.target.value})} placeholder="e.g. Ravi family" className={ic}/></label>
      <label className={lbl}>Phone or email<input value={f.contact||""} onChange={e=>setF({...f,contact:e.target.value})} placeholder="Optional" className={ic}/></label>
      <label className={lbl}>Sponsoring *
        <select value={f.itemKey} onChange={e=>setF({...f,itemKey:e.target.value})} className={ic}>
          <option value="">Choose…</option>
          {items.length > 0 && <optgroup label="Items">{items.map(a => <option key={a.id} value={"a:"+a.id}>{a.name}</option>)}</optgroup>}
          {sevas.length > 0 && <optgroup label="Services">{sevas.filter(sv => !items.some(a => a.name.toLowerCase() === (sv.name||"").toLowerCase())).map(sv => <option key={sv.id} value={"s:"+sv.id}>{sv.name}{sv.charge ? " — £"+sv.charge : ""}</option>)}</optgroup>}
          <option value="new">+ New item…</option>
        </select></label>
      {f.itemKey === "new"
        ? <label className={lbl}>New item name *<input value={f.newItem||""} onChange={e=>setF({...f,newItem:e.target.value})} list="sp-ideas" placeholder="e.g. Milk" className={ic}/>
            <datalist id="sp-ideas">{SPONSOR_ITEM_IDEAS.map(x => <option key={x} value={x}/>)}</datalist></label>
        : <label className={lbl}>Amount paid £ *<input type="number" min="0" step="0.01" value={f.amount} onChange={e=>setF({...f,amount:e.target.value})} placeholder="e.g. 51.00" className={ic}/></label>}
      {f.itemKey === "new" && <label className={lbl}>Amount paid £ *<input type="number" min="0" step="0.01" value={f.amount} onChange={e=>setF({...f,amount:e.target.value})} placeholder="e.g. 51.00" className={ic}/></label>}
      <label className={lbl}>How often
        <select value={f.frequency} onChange={e=>setF({...f,frequency:e.target.value})} className={ic}>
          {FREQ_OPTIONS.map(x => <option key={x} value={x}>{x.charAt(0).toUpperCase()+x.slice(1)}</option>)}
        </select></label>
      {f.frequency === "one-off" ? (
        <div className="sm:col-span-2">
          <div className={lbl+" mb-1"}>Date(s) *</div>
          <div className="flex gap-2 flex-wrap items-center">
            {(f.rotaDates||[]).slice().sort().map(d => (
              <span key={d} className="inline-flex items-center gap-1 bg-white border border-indigo-200 text-indigo-700 text-xs px-2 py-1 rounded-full">{shortDay(d)}
                <button onClick={()=>setF({...f,rotaDates:f.rotaDates.filter(x=>x!==d)})} className="font-bold text-indigo-400 hover:text-indigo-700">×</button></span>
            ))}
            <input type="date" value={oneDate} onChange={e=>setOneDate(e.target.value)} className="border border-slate-200 rounded-lg px-2 py-1 text-sm bg-white"/>
            <button onClick={()=>{ if (oneDate && !(f.rotaDates||[]).includes(oneDate)) setF({...f,rotaDates:[...(f.rotaDates||[]),oneDate]}); setOneDate(""); }}
              className="text-xs bg-indigo-600 text-white px-3 py-1.5 rounded-lg font-semibold">Add date</button>
          </div>
        </div>
      ) : (<>
        <label className={lbl}>Start date *<input type="date" value={f.startDate||""} onChange={e=>setF({...f,startDate:e.target.value})} className={ic}/></label>
        {f.frequency === "custom (weeks)"
          ? <label className={lbl}>Number of weeks *<input type="number" min="1" value={f.customWeeks||""} onChange={e=>setF({...f,customWeeks:e.target.value})} className={ic}/></label>
          : <label className={lbl}>End date (optional — otherwise a year)<input type="date" value={f.endDate||""} onChange={e=>setF({...f,endDate:e.target.value})} className={ic}/></label>}
      </>)}
      <label className={lbl+" sm:col-span-2"}>Notes<input value={f.notes||""} onChange={e=>setF({...f,notes:e.target.value})} placeholder="Optional" className={ic}/></label>
      <div className="sm:col-span-2 text-xs text-slate-500">{dates.length ? "Covers " + dates.length + " day" + (dates.length>1?"s":"") + ": " + shortDay(dates[0]) + (dates.length > 1 ? " – " + shortDay(dates[dates.length-1]) : "") : "No dates yet"}</div>
      <div className="sm:col-span-2 flex gap-2">
        <button onClick={save} className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg py-2 text-sm font-bold">{initial.id ? "Save changes" : "Add sponsorship"}</button>
        <button onClick={onCancel} className="flex-1 bg-white border border-slate-200 text-slate-600 rounded-lg py-2 text-sm font-medium">Cancel</button>
      </div>
    </div>
  );
}

function MDSponsorships({ sponsorships=[], upSponsorships, showToast, sevas=[] }) {
  const blank = { donor:"", contact:"", itemKey:"", newItem:"", amount:"", frequency:"one-off", rotaDates:[], startDate:"", endDate:"", customWeeks:"", notes:"" };
  const [form, setForm]       = useState(null);    // null | { ...record, itemKey, areaId?(when editing) }
  const [search, setSearch]   = useState("");
  const [itemFilter, setItemFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [reportItem, setReportItem] = useState("");
  const [delKey, setDelKey]   = useState(null);
  const [newItem, setNewItem] = useState("");

  const items = sponsorships;
  const records = items.flatMap(a => (a.donations||[]).map(d => {
    const dates = (d.rotaDates && d.rotaDates.length ? d.rotaDates : sponsorDates(d)).slice().sort();
    return { ...d, areaId:a.id, item:a.name, dates, ...sponsorStatus(dates) };
  })).sort((x, y) => (y.first||"").localeCompare(x.first||""));
  const shown = records.filter(r => (!itemFilter || r.areaId === itemFilter) && (!statusFilter || r.status === statusFilter)
    && (!search || (r.donor + " " + (r.contact||"") + " " + r.item).toLowerCase().includes(search.toLowerCase())));

  // Save: find or create the item (an existing item, a service, or a new name), then add/update the record
  const saveRecord = rec => {
    let list = items.slice(), areaId;
    if (rec.itemKey.startsWith("a:")) areaId = rec.itemKey.slice(2);
    else {
      const sv = rec.itemKey.startsWith("s:") ? sevas.find(x => x.id === rec.itemKey.slice(2)) : null;
      const name = sv ? sv.name : rec.newItem.trim();
      const found = list.find(a => a.name.toLowerCase() === name.toLowerCase());
      if (found) areaId = found.id;
      else { areaId = uid(); list = [...list, { id:areaId, name, notes:"", donations:[], ...(sv ? { serviceId: sv.id } : {}) }]; }
    }
    const { itemKey, newItem: _n, areaId: oldArea, item, dates, done, next, status, first, last, ...clean } = rec;
    const entry = { ...clean, id: rec.id || uid() };
    list = list.map(a => {
      let ds = (a.donations||[]).filter(d => !(rec.id && a.id === oldArea && d.id === rec.id));   // moved or replaced
      if (a.id === areaId) ds = rec.id && a.id === oldArea ? (a.donations||[]).map(d => d.id === rec.id ? entry : d) : [...ds, entry];
      return { ...a, donations: ds };
    });
    upSponsorships(list); setForm(null);
    showToast(rec.id ? "Sponsorship updated" : "Sponsorship added");
  };
  const remove = r => { upSponsorships(items.map(a => a.id === r.areaId ? { ...a, donations:(a.donations||[]).filter(d => d.id !== r.id) } : a)); setDelKey(null); showToast("Sponsorship removed"); };
  const addItem = name => { const n = name.trim(); if (!n) return; if (items.some(a => a.name.toLowerCase() === n.toLowerCase())) return showToast("That item already exists","error");
    upSponsorships([...items, { id:uid(), name:n, notes:"", donations:[] }]); setNewItem(""); showToast(n+" added"); };
  const removeItem = a => { if ((a.donations||[]).length) return showToast("Remove its sponsorships first","error"); upSponsorships(items.filter(x => x.id !== a.id)); };

  const rep = records.filter(r => r.areaId === reportItem);
  const repArea = items.find(a => a.id === reportItem);
  const ic = "border border-slate-200 rounded-lg px-2 py-1.5 text-sm bg-white";
  const th = "text-left px-2 py-2 font-semibold text-slate-500 whitespace-nowrap";

  return (
    <div className="space-y-5">
      {/* New sponsorship */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 space-y-3">
        <div className="flex items-center gap-3">
          <h2 className="font-bold text-slate-800 flex-1">🤝 Sponsorships and donations</h2>
          {!form && <button onClick={()=>setForm(blank)} className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl text-sm font-bold">+ New sponsorship</button>}
        </div>
        {form && <SponsorshipForm key={form.id || "new"} initial={form} items={items} sevas={sevas} onSave={saveRecord} onCancel={()=>setForm(null)} showToast={showToast}/>}
      </div>

      {/* All records */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 space-y-3">
        <div className="flex gap-2 flex-wrap items-center">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex-1">All sponsorships ({records.length})</h3>
          <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search donor…" className={ic+" w-36"}/>
          <select value={itemFilter} onChange={e=>setItemFilter(e.target.value)} className={ic}><option value="">All items</option>{items.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}</select>
          <select value={statusFilter} onChange={e=>setStatusFilter(e.target.value)} className={ic}><option value="">Any status</option>{["Upcoming","Active","Completed"].map(x => <option key={x}>{x}</option>)}</select>
        </div>
        {shown.length === 0 ? <p className="text-sm text-slate-400 py-4 text-center">No sponsorships{records.length ? " match" : " yet"}.</p> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[720px]">
              <thead><tr className="border-b border-slate-200 bg-slate-50"><th className={th}>Donor</th><th className={th}>Item</th><th className={th+" text-right"}>Paid £</th><th className={th}>How often</th><th className={th}>From – to</th><th className={th+" text-right"}>Days</th><th className={th}>Status</th><th className={th}></th></tr></thead>
              <tbody>
                {shown.map(r => (
                  <tr key={r.areaId+r.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-2 py-2"><div className="font-medium text-slate-800">{r.donor}</div>{r.contact && <div className="text-xs text-slate-400">{r.contact}</div>}</td>
                    <td className="px-2 py-2">{r.item}</td>
                    <td className="px-2 py-2 text-right font-semibold">{parseFloat(r.amount||0).toFixed(2)}</td>
                    <td className="px-2 py-2 capitalize">{r.frequency}</td>
                    <td className="px-2 py-2 whitespace-nowrap">{shortDay(r.first)}{r.dates.length > 1 ? " – "+shortDay(r.last) : ""}</td>
                    <td className="px-2 py-2 text-right">{r.done}/{r.dates.length}</td>
                    <td className="px-2 py-2"><span className={"text-xs font-semibold px-2 py-0.5 rounded-full "+SP_STATUS_CLS[r.status]}>{r.status}</span></td>
                    <td className="px-2 py-2 whitespace-nowrap text-right">
                      {delKey === r.areaId+r.id
                        ? <><button onClick={()=>remove(r)} className="text-xs bg-red-600 text-white px-2 py-1 rounded">Remove</button> <button onClick={()=>setDelKey(null)} className="text-xs text-slate-500">Keep</button></>
                        : <><button onClick={()=>setForm({ ...r, itemKey:"a:"+r.areaId, newItem:"" })} className="text-xs text-indigo-600 mr-2">Edit</button><button onClick={()=>setDelKey(r.areaId+r.id)} className="text-xs text-red-500">Remove</button></>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Item-wise report */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-4 space-y-3">
        <div className="flex gap-2 flex-wrap items-center">
          <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex-1">📊 Item report</h3>
          <select value={reportItem} onChange={e=>setReportItem(e.target.value)} className={ic}><option value="">Choose an item…</option>{items.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}</select>
        </div>
        {repArea && (<>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {[["Sponsors", new Set(rep.map(r=>r.donor.toLowerCase())).size], ["Total paid", "£"+rep.reduce((t,r)=>t+parseFloat(r.amount||0),0).toFixed(2)],
              ["Days covered", rep.reduce((t,r)=>t+r.dates.length,0)], ["Days still to come", rep.reduce((t,r)=>t+(r.dates.length-r.done),0)]].map(([l,v]) => (
              <div key={l} className="bg-slate-50 rounded-xl p-3"><div className="text-xs text-slate-500">{l}</div><div className="text-lg font-black text-slate-800">{v}</div></div>
            ))}
          </div>
          {rep.length === 0 ? <p className="text-sm text-slate-400">No sponsors for {repArea.name} yet.</p> : (
            <div className="overflow-x-auto"><table className="w-full text-sm min-w-[640px]">
              <thead><tr className="border-b border-slate-200 bg-slate-50"><th className={th}>Donor</th><th className={th+" text-right"}>Paid £</th><th className={th}>How often</th><th className={th}>From – to</th><th className={th+" text-right"}>Weeks done</th><th className={th+" text-right"}>To come</th><th className={th}>Next</th><th className={th}>Status</th></tr></thead>
              <tbody>{rep.slice().sort((x,y)=>(x.first||"").localeCompare(y.first||"")).map(r => (
                <tr key={r.id} className="border-b border-slate-100">
                  <td className="px-2 py-2 font-medium">{r.donor}</td><td className="px-2 py-2 text-right">{parseFloat(r.amount||0).toFixed(2)}</td>
                  <td className="px-2 py-2 capitalize">{r.frequency}</td><td className="px-2 py-2 whitespace-nowrap">{shortDay(r.first)}{r.dates.length>1?" – "+shortDay(r.last):""}</td>
                  <td className="px-2 py-2 text-right">{r.done}</td><td className="px-2 py-2 text-right">{r.dates.length - r.done}</td>
                  <td className="px-2 py-2 whitespace-nowrap">{shortDay(r.next)}</td>
                  <td className="px-2 py-2"><span className={"text-xs font-semibold px-2 py-0.5 rounded-full "+SP_STATUS_CLS[r.status]}>{r.status}</span></td>
                </tr>))}</tbody>
            </table></div>
          )}
        </>)}
      </div>

      {/* Items people can sponsor */}
      <Foldable icon="📋" title="Items that can be sponsored" note={items.length ? items.map(a=>a.name).join(" · ") : "None yet"}>
        <div className="space-y-2">
          {items.map(a => (
            <div key={a.id} className="flex items-center gap-2 text-sm">
              <span className="flex-1">{a.name} <span className="text-xs text-slate-400">({(a.donations||[]).length} record{(a.donations||[]).length!==1?"s":""})</span></span>
              <button onClick={()=>removeItem(a)} className="text-xs text-red-500" title="Only items with no records can be removed">Remove</button>
            </div>
          ))}
          <div className="flex gap-2">
            <input value={newItem} onChange={e=>setNewItem(e.target.value)} list="sp-ideas2" placeholder="New item, e.g. Milk" className={ic+" flex-1"}/>
            <datalist id="sp-ideas2">{SPONSOR_ITEM_IDEAS.map(x => <option key={x} value={x}/>)}</datalist>
            <button onClick={()=>addItem(newItem)} className="text-sm bg-indigo-600 text-white px-3 py-1.5 rounded-lg font-semibold">Add item</button>
          </div>
        </div>
      </Foldable>
    </div>
  );
}

