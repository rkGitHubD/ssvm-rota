"""Book a Pooja: members request a pooja/sponsorship on a date (Volunteer tab); the admin
accepts or declines in Master Data → Pooja Bookings and confirms on WhatsApp.

Usage: python3 tools/booking-patch.py Index.html
"""
import os
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()
components = open(os.path.join(os.path.dirname(__file__), "booking-components.jsx"), encoding="utf-8").read()


def swap(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:90])
    s = s.replace(old, new)


swap("function VolunteerServices(", components + "function VolunteerServices(")

# ── Volunteer tab: Book Pooja page ────────────────────────────────────────────
swap('''  const volunteerTabs = isApproved
    ? ["Pooja Itinerary","Services","My Requests"]
    : ["My Requests"];''',
     '''  const volunteerTabs = isApproved
    ? ["Pooja Itinerary","Services","Book Pooja","My Requests"]
    : ["Book Pooja","My Requests"];''')
swap('''"Services":"🙏","Pooja Itinerary":"🕉️"};''', '''"Services":"🙏","Pooja Itinerary":"🕉️","Book Pooja":"🪔"};''')
swap('''        {subTab==="Pooja Itinerary" && <VolunteerItinerary itineraries={itineraries}/>}''',
     '''        {subTab==="Pooja Itinerary" && <VolunteerItinerary itineraries={itineraries}/>}
        {subTab==="Book Pooja"      && <BookPooja sevas={sevas} sponsorships={sponsorships} members={members} generalOffers={generalOffers} upGeneralOffers={upGeneralOffers} currentUser={currentUser} config={config} showToast={showToast}/>}''')
# Four sub-tabs on a phone: let long names wrap rather than widen the page
swap('''className={"relative flex-1 md:flex-none flex flex-col md:block items-center gap-0.5 px-1 md:px-3 py-1.5 md:py-2 text-xs md:text-sm font-semibold md:font-medium whitespace-nowrap''',
     '''className={"relative flex-1 min-w-0 md:flex-none flex flex-col md:block items-center gap-0.5 px-1 md:px-3 py-1.5 md:py-2 text-xs md:text-sm font-semibold md:font-medium text-center leading-tight md:whitespace-nowrap''')

# ── Keep bookings out of availability offers and the Requests inbox ───────────
swap('''  const myOffers = generalOffers.filter(o => o.memberId === currentUser.memberId && !isSwap(o));''',
     '''  const myOffers = generalOffers.filter(o => o.memberId === currentUser.memberId && !isSwap(o) && !isBooking(o));''')
swap('''  (generalOffers||[]).filter(o => !isSwap(o)).forEach(offer => {''', '''  (generalOffers||[]).filter(o => !isSwap(o) && !isBooking(o)).forEach(offer => {''')
swap('''    + generalOffers.filter(x=>x.status==="pending" && !isSwap(x)).length''', '''    + generalOffers.filter(x=>x.status==="pending" && !isSwap(x) && !isBooking(x)).length''')

# ── Admin: Master Data → Temple Admin → Pooja Bookings, with badges ───────────
swap('''  const pendingSwaps = isAdmin ? generalOffers.filter(x=>isSwap(x) && x.status==="pending").length : 0;''',
     '''  const pendingSwaps = isAdmin ? generalOffers.filter(x=>(isSwap(x) || isBooking(x)) && x.status==="pending").length : 0;   // swaps + pooja bookings''')
swap('''  { key:"priests",      label:"🔔 Priests",         desc:"Priests & fees" },''',
     '''  { key:"priests",      label:"🔔 Priests",         desc:"Priests & fees" },
  { key:"bookings",     label:"🪔 Pooja Bookings",  desc:"Requests from devotees" },''')
swap('''keys:["finance","services","sponsorships","inventory","itinerary","prasadham","priests"] },''',
     '''keys:["bookings","finance","services","sponsorships","inventory","itinerary","prasadham","priests"] },''')
swap('''      {section==="priests"     && <MDPriests      priests={priests} upPriests={upPriests} showToast={showToast}/>}''',
     '''      {section==="priests"     && <MDPriests      priests={priests} upPriests={upPriests} showToast={showToast}/>}
      {section==="bookings"    && <MDBookings     generalOffers={generalOffers} upGeneralOffers={upGeneralOffers} config={config} showToast={showToast}/>}''')
swap('''                  {s.key==="assignments" && (generalOffers||[]).filter(o=>isSwap(o)&&o.status==="pending").length>0 && (
                    <span className="ml-1.5 bg-red-500 text-white text-xs font-bold px-1.5 rounded-full">{(generalOffers||[]).filter(o=>isSwap(o)&&o.status==="pending").length}</span>
                  )}''',
     '''                  {s.key==="assignments" && (generalOffers||[]).filter(o=>isSwap(o)&&o.status==="pending").length>0 && (
                    <span className="ml-1.5 bg-red-500 text-white text-xs font-bold px-1.5 rounded-full">{(generalOffers||[]).filter(o=>isSwap(o)&&o.status==="pending").length}</span>
                  )}
                  {s.key==="bookings" && (generalOffers||[]).filter(o=>isBooking(o)&&o.status==="pending").length>0 && (
                    <span className="ml-1.5 bg-red-500 text-white text-xs font-bold px-1.5 rounded-full">{(generalOffers||[]).filter(o=>isBooking(o)&&o.status==="pending").length}</span>
                  )}''')

open(p, "w", encoding="utf-8").write(s)
print("patched", p)
