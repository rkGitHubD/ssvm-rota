#!/usr/bin/env python3
"""One-off patch: single member login, admin as a member flag, role-based tabs.
Usage: python3 tools/roles-patch.py path/to/file  (app.jsx or the master Index.html)
Every replacement must match exactly once, otherwise nothing is written."""
import re, sys

path = sys.argv[1]
s = open(path, encoding="utf-8").read()

def sub(old, new):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit(f"expected 1 match, found {n}:\n{old[:200]}")
    s = s.replace(old, new)

def cut(start, end):
    """Remove from `start` up to (not including) `end`; both must be unique."""
    global s
    i, j = s.find(start), s.find(end)
    if s.count(start) != 1 or s.count(end) != 1 or j < i:
        sys.exit(f"cut markers not unique/ordered:\n{start[:120]}")
    s = s[:i] + s[j:]

# ── Nav tables per role ─────────────────────────────────────────────────────
sub('''  const TOP_TABS = isAdmin ? ["Admin","Rota","Volunteer"]
               : (isRotaLead||isSecondary) ? ["Rota"]
               : ["Volunteer"];
  const volunteerTabs = isApproved
    ? ["Pooja Itinerary","Services","Requests"]
    : ["Requests"];
  const rotaTabs = (isAdmin || isRotaLead)
    ? ["Rota Calendar","Rota Sheet","Requests","Services","Pooja Itinerary"]
    : ["Rota Calendar","Requests","Services","Pooja Itinerary"];''',
'''  // Admin: everything · Rota Lead: Rota + Volunteer · Secondary/Volunteer: Volunteer only
  const TOP_TABS = isAdmin ? ["Admin","Rota","Volunteer"]
               : isRotaLead ? ["Rota","Volunteer"]
               : ["Volunteer"];
  const volunteerTabs = isApproved
    ? ["Pooja Itinerary","Services","My Requests"]
    : ["My Requests"];
  const rotaTabs = ["Rota Calendar","Rota Sheet","Requests"];''')

# ── Login: role comes from the member record; admin is a flag on a member ──
sub('''          if (!user) {
            setUserRole("admin"); setTopTab("Admin"); setSubTab("Dashboard");
          } else {
            setCurrentUser(user);
            const role = user.memberRole === "primary" ? "rota-lead"
                       : user.memberRole === "secondary" ? "secondary"
                       : "volunteer";
            setUserRole(role);
            if (role === "rota-lead" || role === "secondary") { setTopTab("Rota"); setSubTab("Rota Calendar"); }
            else {
              setTopTab("Volunteer");
              const approved = user.memberRole === "primary" || user.memberRole === "secondary" || user.approved !== false;
              setSubTab(approved ? "Pooja Itinerary" : "Requests");
            }
          }''',
'''          setCurrentUser(user);
          const role = user.isAdmin ? "admin"
                     : user.memberRole === "primary" ? "rota-lead"
                     : user.memberRole === "secondary" ? "secondary"
                     : "volunteer";
          setUserRole(role);
          if (role === "admin") { setTopTab("Admin"); setSubTab("Dashboard"); }
          else if (role === "rota-lead") { setTopTab("Rota"); setSubTab("Rota Calendar"); }
          else {
            setTopTab("Volunteer");
            const approved = user.memberRole === "secondary" || user.approved !== false;
            setSubTab(approved ? "Pooja Itinerary" : "My Requests");
          }''')
sub('''        config={config} adminPin={config.adminPin||"1234"}\n''', '''        config={config}\n''')

# ── Header name, tab badges, sub-tab rendering ─────────────────────────────
sub('''{roleBadge.icon} {isAdmin ? "Admin" : currentUser?.name}''', '''{roleBadge.icon} {currentUser?.name || "Admin"}''')
old_top_badge = '''const badge = t==="Volunteer" && canManage && totalPendingRequests>0 ? totalPendingRequests
                          : t==="Volunteer" && !canManage && (newRequestsForMe+myPendingClarify)>0 ? (newRequestsForMe+myPendingClarify) : 0;'''
new_top_badge = '''const badge = t==="Rota" && canManage && totalPendingRequests>0 ? totalPendingRequests
                          : t==="Volunteer" && (newRequestsForMe+myPendingClarify)>0 ? (newRequestsForMe+myPendingClarify) : 0;'''
sub(old_top_badge, new_top_badge)
sub(old_top_badge.replace("\n                          ", "\n                        "),
    new_top_badge.replace("\n                          ", "\n                        "))
sub('''"Requests":"📥",''', '''"Requests":"📥","My Requests":"📥",''')
sub('''const badge = s==="Requests" && canManage && totalPendingRequests>0 ? totalPendingRequests
                          : s==="Requests" && !canManage && (newRequestsForMe+myPendingClarify)>0''',
    '''const badge = s==="Requests" && canManage && totalPendingRequests>0 ? totalPendingRequests
                          : s==="My Requests" && (newRequestsForMe+myPendingClarify)>0''')
sub('''{subTab==="Requests"     && !canManage && <VolunteerRequests''', '''{subTab==="My Requests"  && <VolunteerRequests''')

# ── Sign-in screen: members only, no admin PIN ──────────────────────────────
sub('''// onLogin(user): user=null → admin; user={name,email,memberId,memberRole} → member
function AuthScreen({ authMode, setAuthMode, members, upMembers, config, adminPin, onLogin, showToast }) {''',
    '''// onLogin(user): user={name,email,memberId,memberRole,isAdmin}
function AuthScreen({ authMode, setAuthMode, members, upMembers, config, onLogin, showToast }) {''')
sub('''  var [aPin,    setAPin]    = useState("");
  var [aPinErr, setAPinErr] = useState("");
''', '')
sub('''memberRole: res.member.role, approved: true });''', '''memberRole: res.member.role, isAdmin: !!res.member.isAdmin, approved: true });''')
sub('''memberRole: found.role, approved: true });''', '''memberRole: found.role, isAdmin: !!found.isAdmin, approved: true });''')
cut('''  var handleAdminPin = function() {''', '''  var ic  = "w-full border''')
i =s.find('''            <div className="flex items-center gap-3 text-slate-300 text-xs pt-1">
              <div className="flex-1 h-px bg-slate-200"/>or<div className="flex-1 h-px bg-slate-200"/>''')
j = s.find('''                <div className="text-xs font-normal text-slate-400 mt-0.5">Full access — PIN required</div>
              </div>
            </button>
''')
if i < 0 or j < i: sys.exit("admin button block not found")
s = s[:i] + s[j + len('''                <div className="text-xs font-normal text-slate-400 mt-0.5">Full access — PIN required</div>
              </div>
            </button>
'''):]
i = s.find('''        {authMode === "admin-pin" && (''')
j = s.find('''Login as Admin →</button>
          </div>
        )}
''')
if i < 0 or j < i: sys.exit("admin-pin block not found")
s = s[:i] + s[j + len('''Login as Admin →</button>
          </div>
        )}
'''):]
s = re.sub(r"\n\n+(      </div>\n    </div>\n  \);\n}\n\n\n// ─── Rota Calendar with Organisation)", r"\n\n\1", s)

# ── Settings: no admin PIN any more ────────────────────────────────────────
sub('''  const save = ()=>{
    if (form.adminPin && form.adminPin.length < 6) return showToast("Admin PIN must be at least 6 characters","error");
    const next = { ...form };
    if (!next.adminPin) { if (config.adminPin) next.adminPin = config.adminPin; else delete next.adminPin; }
    upConfig(next); setForm({ ...form, adminPin: "" }); showToast("Settings saved");
  };''', '''  const save = ()=>{
    const { adminPin, ...next } = form;
    upConfig(next); showToast("Settings saved");
  };''')
sub('''          <div className="border-t border-slate-100 pt-4">
            <Field label="🔐 Change Admin PIN" type="password" value={form.adminPin||""} onChange={v=>setForm({...form,adminPin:v})} placeholder="Leave blank to keep current PIN"/>
            <p className="text-xs text-slate-400 mt-1">At least 6 characters. Admins enter this on the login screen.</p>
          </div>
''', '')
sub('''  adminPin: "1234",\n''', '')

# ── Master Data → Members: Admin tick-box ──────────────────────────────────
sub('''const blank = {name:"",email:"",phone:"",pin:"",area:"",city:"",role:"primary",notes:""};''',
    '''const blank = {name:"",email:"",phone:"",pin:"",area:"",city:"",role:"primary",isAdmin:false,notes:""};''')
sub('''setForm({name:m.name,email:m.email||"",phone:m.phone||"",pin:"",role:m.role,notes:m.notes||""}); };''',
    '''setForm({name:m.name,email:m.email||"",phone:m.phone||"",pin:"",role:m.role,isAdmin:!!m.isAdmin,notes:m.notes||""}); };''')
sub('''          <div>
            <label className="text-xs font-semibold text-slate-500 mb-1 block">Notes</label>
            <textarea value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})}
              rows={2} placeholder="Any notes about this member…"''',
    '''          <label className="flex items-start gap-2 p-3 rounded-lg border border-amber-200 bg-amber-50 cursor-pointer">
            <input type="checkbox" checked={!!form.isAdmin} onChange={e=>setForm({...form,isAdmin:e.target.checked})} className="mt-0.5"/>
            <span className="text-xs text-amber-800"><b>⚙️ Admin</b> — full access to everything (Admin, Rota and Volunteer). Keeps their rota role above.</span>
          </label>
          <div>
            <label className="text-xs font-semibold text-slate-500 mb-1 block">Notes</label>
            <textarea value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})}
              rows={2} placeholder="Any notes about this member…"''')
sub('''                {m.approved==="rejected" && <span className="text-xs bg-red-100 text-red-600 border border-red-200 px-2 py-0.5 rounded-full font-bold flex-shrink-0">✗ Declined</span>}
                <span className={`text-xs px-2.5 py-1''',
    '''                {m.approved==="rejected" && <span className="text-xs bg-red-100 text-red-600 border border-red-200 px-2 py-0.5 rounded-full font-bold flex-shrink-0">✗ Declined</span>}
                {m.isAdmin && <span className="text-xs bg-amber-100 text-amber-700 border border-amber-200 px-2 py-0.5 rounded-full font-bold flex-shrink-0">⚙️ Admin</span>}
                <span className={`text-xs px-2.5 py-1''')

open(path, "w", encoding="utf-8").write(s)
print("patched", path)
