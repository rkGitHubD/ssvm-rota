"""Rota schedule: send the PDF on WhatsApp (phone share sheet; on a computer, save + open WhatsApp).

Usage: python3 tools/schedule-whatsapp-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def swap(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


# The schedule's page can also be returned as HTML, for turning into a PDF file
swap('''function printRotaSchedule(year, { rotas = {}, members = [], specials = [], config = {} } = {}) {''',
     '''function printRotaSchedule(year, opts = {}) {
  const { rotas = {}, members = [], specials = [], config = {} } = opts;''')
swap('''  h += "<button class='noprint' onclick='window.print()' style='position:fixed;bottom:16px;right:16px;background:#3730a3;color:#fff;border:0;padding:8px 20px;border-radius:8px;font-size:12px;font-weight:bold;cursor:pointer'>Print / Save as PDF</button>"
    + "<script>window.onload=function(){setTimeout(function(){window.print();},300);};<\\/script>"
    + "</body></html>";
  const w = window.open("", "_blank");
  if (!w) return false;
  w.document.write(h); w.document.close();
  return true;
}''',
     '''  if (opts.htmlOnly) return h + "</body></html>";
  h += "<button class='noprint' onclick='window.print()' style='position:fixed;bottom:16px;right:16px;background:#3730a3;color:#fff;border:0;padding:8px 20px;border-radius:8px;font-size:12px;font-weight:bold;cursor:pointer'>Print / Save as PDF</button>"
    + "<script>window.onload=function(){setTimeout(function(){window.print();},300);};<\\/script>"
    + "</body></html>";
  const w = window.open("", "_blank");
  if (!w) return false;
  w.document.write(h); w.document.close();
  return true;
}

// ─── The rota schedule as a PDF file, for sharing ───────────────────────────
// Each page of the printable schedule is drawn to an image and placed on an A4 page.
// The two libraries are only loaded when someone shares.
const loadScriptOnce = (src, ready) => ready() ? Promise.resolve() : new Promise((ok, fail) => {
  const el = document.createElement("script"); el.src = src;
  el.onload = () => ok(); el.onerror = () => fail(new Error("Couldn't load the PDF maker — check the internet connection"));
  document.head.appendChild(el);
});
async function rotaSchedulePdf(year, opts) {
  await loadScriptOnce("https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js", () => window.html2canvas);
  await loadScriptOnce("https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js", () => window.jspdf);
  const frame = document.createElement("iframe");
  frame.style.cssText = "position:fixed;left:-10000px;top:0;width:900px;height:1300px;border:0";
  document.body.appendChild(frame);
  try {
    const doc = frame.contentDocument;
    doc.open(); doc.write(printRotaSchedule(year, { ...opts, htmlOnly: true })); doc.close();
    await new Promise(r => setTimeout(r, 300));
    doc.body.style.background = "#fff"; doc.body.style.padding = "0";
    const pdf = new window.jspdf.jsPDF({ unit: "mm", format: "a4" });
    const pages = [...doc.querySelectorAll(".page")];
    for (let i = 0; i < pages.length; i++) {
      pages[i].style.boxShadow = "none"; pages[i].style.margin = "0";
      const canvas = await window.html2canvas(pages[i], { scale: 2, backgroundColor: "#ffffff" });
      if (i) pdf.addPage();
      pdf.addImage(canvas.toDataURL("image/jpeg", 0.92), "JPEG", 0, 0, 210, canvas.height * 210 / canvas.width);
    }
    return new File([pdf.output("blob")], "Rota schedule " + year + ".pdf", { type: "application/pdf" });
  } finally { frame.remove(); }
}''')

# ── Assignments: WhatsApp button (two taps: make the PDF, then send it) ───────
swap('''  const [schedYear, setSchedYear] = useState(config.year || new Date().getFullYear());''',
     '''  const [schedYear, setSchedYear] = useState(config.year || new Date().getFullYear());
  // Sharing needs a fresh tap, so the PDF is made on the first tap and sent on the second
  const [waFile, setWaFile] = useState(null);
  const [waBusy, setWaBusy] = useState(false);
  const waText = (config.fullName || config.orgName || "") + " — rota schedule " + schedYear
    + ". Need to swap your week? Log in to the app and request a swap from Volunteer → My Requests: " + window.location.origin + window.location.pathname;
  const makeWaPdf = async () => {
    setWaBusy(true);
    try { setWaFile(await rotaSchedulePdf(schedYear, { rotas, members, specials, config })); }
    catch (e) { showToast(e.message || "Couldn't make the PDF","error"); }
    setWaBusy(false);
  };
  const sendWaPdf = async () => {
    try {
      if (navigator.canShare && navigator.canShare({ files: [waFile] })) {
        await navigator.share({ files: [waFile], title: waFile.name, text: waText });   // pick WhatsApp in the share menu
      } else {
        // Computers usually can't share files: save the PDF and open WhatsApp with the message
        const a = document.createElement("a"); a.href = URL.createObjectURL(waFile); a.download = waFile.name; a.click();
        window.open("https://wa.me/?text=" + encodeURIComponent(waText), "_blank");
        showToast("PDF saved to Downloads — in WhatsApp tap 📎 and choose the file");
      }
      setWaFile(null);
    } catch (e) { if (e.name !== "AbortError") showToast(e.message || "Couldn't share the PDF","error"); }
  };''')
swap('''      <select value={schedYear} onChange={e=>setSchedYear(parseInt(e.target.value))}''',
     '''      <select value={schedYear} onChange={e=>{ setSchedYear(parseInt(e.target.value)); setWaFile(null); }}''')
swap('''        className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl text-sm font-bold">Print / PDF</button>
    </div>''',
     '''        className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-xl text-sm font-bold">Print / PDF</button>
      {waFile ? (
        <button onClick={sendWaPdf} className="bg-[#25D366] hover:bg-[#1EBE5A] text-white px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2 animate-pulse">
          <WhatsAppIcon className="w-5 h-5"/> Send PDF on WhatsApp</button>
      ) : (
        <button onClick={makeWaPdf} disabled={waBusy} className="bg-[#25D366] hover:bg-[#1EBE5A] text-white px-4 py-2 rounded-xl text-sm font-bold flex items-center gap-2 disabled:opacity-60">
          <WhatsAppIcon className="w-5 h-5"/> {waBusy ? "Making PDF…" : "WhatsApp"}</button>
      )}
    </div>''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
