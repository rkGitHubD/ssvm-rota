"""Keep every signed-in device up to date: the app reloads the shared data when it comes
back into view and every 45 seconds while it's open, so a change made on the computer
(a sponsorship, a rota, a sheet) reaches the phone without signing in again.
Unchanged parts keep their identity, so open forms don't lose what's being typed, and a
refresh is skipped while this device is still saving.

Usage: python3 tools/sync-patch.py Index.html
"""
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8").read()


def swap(old, rep, n=1):
    global s
    assert s.count(old) == n, (s.count(old), old[:80])
    s = s.replace(old, rep)


# Count saves in flight, so a refresh never replaces something this device is still saving
swap('''const DB = {
  token: null,      // session token from rota_login''', '''const DB = {
  token: null,      // session token from rota_login
  pending: 0,       // saves in flight
  writes: 0,        // saves started, ever — a refresh is dropped if this moved while it loaded''')
swap('''    if (!DB.token) return;
    try {
      const res = await DB.rpc("rota_save", { p_token: DB.token, p_key: key, p_value: value });
      if (res.error) { console.error("DB.set error:", key, res.error); if (DB.onError) DB.onError(res.error); }
    } catch(e) { console.error("DB.set failed:", e); if (DB.onError) DB.onError(e.message); }
  },''', '''    if (!DB.token) return;
    DB.pending++; DB.writes++;
    try {
      const res = await DB.rpc("rota_save", { p_token: DB.token, p_key: key, p_value: value });
      if (res.error) { console.error("DB.set error:", key, res.error); if (DB.onError) DB.onError(res.error); }
    } catch(e) { console.error("DB.set failed:", e); if (DB.onError) DB.onError(e.message); }
    finally { DB.pending--; }
  },''')

swap('''        setPriests(g("rota-priests", []));
  };
''', '''        setPriests(g("rota-priests", []));
  };

  // ── Stay in sync with other devices ───────────────────────────────────────
  // Reload the shared data when the app comes back into view and every 45s while it's
  // showing. Only keys that came back are applied, and unchanged parts keep their old
  // objects so screens being edited aren't reset.
  useEffect(() => {
    if (!userRole || !isConfigured()) return;
    const setters = { "rota-acts":setActs, "rota-members":setMembers, "rota-rotas":setRotas, "rota-specials":setSpec,
      "rota-registers":setRegs, "rota-regentries":setRegEntries, "rota-sheets":setRotaSheets, "rota-offers":setGeneralOffers,
      "rota-cash":setCashInHand, "rota-sevas":setServices, "rota-sponsorships":setSponsorships, "rota-inventory":setInventory,
      "rota-itineraries":setItineraries, "rota-prasadham":setPrasadham, "rota-hundi":setHundi, "rota-budgets":setBudgets, "rota-priests":setPriests };
    let busy = false;
    const refresh = async () => {
      if (busy || document.visibilityState !== "visible" || DB.pending > 0 || !DB.token) return;
      busy = true;
      const before = DB.writes;
      try {
        const map = await DB.loadAll();
        if (!map || DB.pending > 0 || DB.writes !== before) return;   // saved meanwhile: try next time
        Object.entries(setters).forEach(([k, set]) => { if (k in map) set(prev => keepSame(prev, map[k])); });
        if ("rota-config" in map) setConfig(prev => keepSame(prev, { ...DEFAULT_CONFIG, ...map["rota-config"] }));
      } finally { busy = false; }
    };
    const onShow = () => { if (document.visibilityState === "visible") refresh(); };
    const t = setInterval(refresh, 45 * 1000);
    document.addEventListener("visibilitychange", onShow);
    window.addEventListener("focus", onShow);
    return () => { clearInterval(t); document.removeEventListener("visibilitychange", onShow); window.removeEventListener("focus", onShow); };
  }, [userRole]);
''')

# keepSame: the new value, reusing old objects wherever nothing changed
swap('''const DEFAULT_CONFIG = {''', '''// The fresh value, but reusing the old objects wherever nothing changed (by id in lists)
function keepSame(prev, next) {
  if (prev === next) return prev;
  if (JSON.stringify(prev) === JSON.stringify(next)) return prev;
  if (Array.isArray(prev) && Array.isArray(next)) {
    const byId = {}; prev.forEach(x => { if (x && x.id != null) byId[x.id] = x; });
    return next.map((x, i) => x && x.id != null && byId[x.id] !== undefined ? keepSame(byId[x.id], x) : keepSame(prev[i], x));
  }
  if (prev && next && typeof prev === "object" && typeof next === "object" && !Array.isArray(prev) && !Array.isArray(next) && !(prev instanceof Date)) {
    const out = {}; Object.keys(next).forEach(k => { out[k] = keepSame(prev[k], next[k]); });
    return out;
  }
  return next;
}

const DEFAULT_CONFIG = {''')
open(p, "w", encoding="utf-8").write(s)
print("patched", p)
