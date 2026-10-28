"""Members screen: drop the import's boilerplate notes ("no contact information",
"imported from the rota schedule"), stop showing "No contact info", and show the
phone number (tap to call) and email once a member has them.

Usage: python3 tools/member-notes-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def swap(old, rep, n=1):
    global s
    assert s.count(old) == n, (s.count(old), old[:80])
    s = s.replace(old, rep)


swap('''function MDMembers({ members, upMembers, showToast }) {''',
     '''// Sentences the one-off member import put in notes; they aren't real notes
const IMPORT_NOTE = /imported from|contact (info|information|details)/i;
const cleanNotes = t => ((t || "").match(/[^.!?\\n]+[.!?]*/g) || []).map(x => x.trim()).filter(x => x && !IMPORT_NOTE.test(x)).join(" ");
function MDMembers({ members, upMembers, showToast }) {
  // Clear the import's notes from the saved members, once
  useEffect(() => {
    if (members.some(m => m.notes && cleanNotes(m.notes) !== m.notes.trim()))
      upMembers(members.map(m => m.notes && cleanNotes(m.notes) !== m.notes.trim() ? { ...m, notes: cleanNotes(m.notes) } : m));
  }, [members]);''')
swap('''                  <div className="text-xs text-slate-400 truncate">{[m.email,m.phone].filter(Boolean).join(" · ")||"No contact info"}</div>
                  {m.notes&&<div className="text-xs text-slate-400 italic truncate mt-0.5">"{m.notes}"</div>}''',
     '''                  {(m.phone || m.email) && <div className="text-xs text-slate-500 truncate">
                    {m.phone && <a href={"tel:" + m.phone.replace(/\\s+/g, "")} className="text-indigo-600 font-medium">📱 {m.phone}</a>}
                    {m.phone && m.email && " · "}{m.email}</div>}
                  {cleanNotes(m.notes) && <div className="text-xs text-slate-400 italic truncate mt-0.5">"{cleanNotes(m.notes)}"</div>}''')
swap('''setForm({name:m.name,email:m.email||"",phone:m.phone||"",pin:"",role:m.role,isAdmin:!!m.isAdmin,notes:m.notes||""}); };''',
     '''setForm({name:m.name,email:m.email||"",phone:m.phone||"",pin:"",role:m.role,isAdmin:!!m.isAdmin,notes:cleanNotes(m.notes)}); };''')
open(p, "w", encoding="utf-8").write(s)
print("patched", p)
