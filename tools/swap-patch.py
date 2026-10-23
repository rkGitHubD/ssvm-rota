"""Rota Lead / Secondary swaps: members ask from My Requests; the admin plans and
applies swaps (including chains of several weeks) on the Assignments screen.

Usage: python3 tools/swap-patch.py Index.html
"""
import os
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()
components = open(os.path.join(os.path.dirname(__file__), "swap-components.jsx"), encoding="utf-8").read()


def swap(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


# Components go just before the Assignments screen
swap("function MDAssignments(", components + "function MDAssignments(")

# ── Assignments screen: the swap planner at the top ───────────────────────────
swap('''function MDAssignments({ members, rotas, upRotas, allSlots, showToast, specials, upSpecials }) {''',
     '''function MDAssignments({ members, rotas, upRotas, allSlots, showToast, specials, upSpecials, generalOffers=[], upGeneralOffers }) {''')
swap('''    <SpecialOccasions specials={specials} upSpecials={upSpecials} showToast={showToast}/>''',
     '''    <SwapPlanner members={members} rotas={rotas} upRotas={upRotas} allSlots={allSlots} generalOffers={generalOffers} upGeneralOffers={upGeneralOffers} showToast={showToast}/>
    <SpecialOccasions specials={specials} upSpecials={upSpecials} showToast={showToast}/>''')
swap('''<MDAssignments members={members} rotas={rotas} upRotas={upRotas} allSlots={allSlots} showToast={showToast} specials={specials} upSpecials={upSpecials}/>''',
     '''<MDAssignments members={members} rotas={rotas} upRotas={upRotas} allSlots={allSlots} showToast={showToast} specials={specials} upSpecials={upSpecials} generalOffers={generalOffers} upGeneralOffers={upGeneralOffers}/>''')
swap('''function MasterData({ members, upMembers,''', '''function MasterData({ generalOffers=[], upGeneralOffers, members, upMembers,''')
swap('''{subTab==="Master Data"  && <MasterData members={members}''', '''{subTab==="Master Data"  && <MasterData generalOffers={generalOffers} upGeneralOffers={upGeneralOffers} members={members}''')
# Badge on the Assignments section button
swap('''            {s.label}
          </button>
        ))}''',
     '''            {s.label}
            {s.key==="assignments" && (generalOffers||[]).filter(o=>isSwap(o)&&o.status==="pending").length>0 && (
              <span className="ml-1.5 bg-red-500 text-white text-xs font-bold px-1.5 rounded-full">{(generalOffers||[]).filter(o=>isSwap(o)&&o.status==="pending").length}</span>
            )}
          </button>
        ))}''')

# ── Members: ask for a swap from My Requests ──────────────────────────────────
swap('''{subTab==="My Requests"  && <VolunteerRequests rotas={rotas}''', '''{subTab==="My Requests"  && <VolunteerRequests members={members} rotas={rotas}''')
swap('''function VolunteerRequests({ rotas, upRotas, allSlots, activities, generalOffers, upGeneralOffers, currentUser, showToast }) {''',
     '''function VolunteerRequests({ members=[], rotas, upRotas, allSlots, activities, generalOffers, upGeneralOffers, currentUser, showToast }) {''')
swap('''  const myOffers = generalOffers.filter(o => o.memberId === currentUser.memberId);''',
     '''  const myOffers = generalOffers.filter(o => o.memberId === currentUser.memberId && !isSwap(o));''')
swap('''      {/* General availability box */}''',
     '''      {/* Swap one of my Rota Lead / Secondary weeks */}
      <SwapRequestForm rotas={rotas} allSlots={allSlots} members={members} generalOffers={generalOffers} upGeneralOffers={upGeneralOffers} currentUser={currentUser} showToast={showToast}/>

      {/* General availability box */}''')

# Swap requests are not availability offers: keep them out of the Requests inbox
swap('''  (generalOffers||[]).forEach(offer => {
    allRequests.push({ type:"offer", offer });''',
     '''  (generalOffers||[]).filter(o => !isSwap(o)).forEach(offer => {
    allRequests.push({ type:"offer", offer });''')

# ── Badges: swap requests count for the admin ─────────────────────────────────
swap('''    + generalOffers.filter(x=>x.status==="pending").length
    + pendingApprovals;''',
     '''    + generalOffers.filter(x=>x.status==="pending" && !isSwap(x)).length
    + pendingApprovals;
  // For the admin: swap requests waiting on the Assignments screen
  const pendingSwaps = isAdmin ? generalOffers.filter(x=>isSwap(x) && x.status==="pending").length : 0;''')
swap('''              const badge = t==="Rota" && canManage && totalPendingRequests>0 ? totalPendingRequests''',
     '''              const badge = t==="Admin" && pendingSwaps>0 ? pendingSwaps
                          : t==="Rota" && canManage && totalPendingRequests>0 ? totalPendingRequests''')
swap('''            const badge = t==="Rota" && canManage && totalPendingRequests>0 ? totalPendingRequests''',
     '''            const badge = t==="Admin" && pendingSwaps>0 ? pendingSwaps
                        : t==="Rota" && canManage && totalPendingRequests>0 ? totalPendingRequests''')
swap('''              const badge = s==="Requests" && canManage && totalPendingRequests>0 ? totalPendingRequests''',
     '''              const badge = s==="Master Data" && pendingSwaps>0 ? pendingSwaps
                          : s==="Requests" && canManage && totalPendingRequests>0 ? totalPendingRequests''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
