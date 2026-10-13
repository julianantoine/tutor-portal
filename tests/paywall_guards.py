#!/usr/bin/env python3
"""Paywall guard table.

Start the app locally, then point this at it:

    PORT=8951 python3 backend/main.py &
    python3 tests/paywall_guards.py http://127.0.0.1:8951

It asserts the refusals and the allowances without touching Stripe: a locked
account, a comped account, the demo and its one-subject scope, a repeat demo, an
account with no payment, a webhook that cannot be verified, and a real
subscription row going active -> past_due -> canceled -> active again.
"""
import json
import sqlite3
import sys
import time
import urllib.error
import urllib.request

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8950").rstrip("/")
DB = sys.argv[2] if len(sys.argv) > 2 else "data/tutor.db"
fails = []


def call(method, path, body=None, token=None, expect=None, label=""):
    req = urllib.request.Request(BASE + path, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as r:
            code, payload = r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        code, raw = e.code, e.read()
        try:
            payload = json.loads(raw or b"null")
        except Exception:
            payload = {"raw": raw.decode("utf-8", "replace")[:160]}
    ok = expect is None or code == expect
    if not ok:
        fails.append(f"{label or method + ' ' + path}: got {code}, wanted {expect}")
    print(f"  [{'PASS' if ok else 'FAIL'}] {label or (method + ' ' + path)} -> {code}"
          + ("" if ok else f"   (wanted {expect})"))
    return code, payload


def detail(payload):
    d = (payload or {}).get("detail")
    return d if isinstance(d, dict) else {}


def token_of(payload):
    return (payload or {}).get("token")


def dbsql(sql, args=()):
    con = sqlite3.connect(DB, timeout=10)
    con.execute(sql, args)
    con.commit()
    con.close()


print("\n== an account with no subscription is refused ==")
c, student = call("POST", "/api/login", {"identifier": "student", "password": "student"},
                  expect=200, label="login as 'student'")
st = token_of(student)
c, me = call("GET", "/api/me", token=st, expect=200, label="/api/me works while locked out")
plan = (me or {}).get("plan") or {}
print(f"       plan = {plan.get('plan')!r}, entitled = {plan.get('entitled')!r}")
call("GET", "/api/courses", token=st, expect=402, label="GET /api/courses (content)")
call("GET", "/api/progress", token=st, expect=402, label="GET /api/progress")
call("GET", "/api/notes", token=st, expect=402, label="GET /api/notes")
c, pay = call("GET", "/api/courses", token=st, expect=402, label="the 402 body")
d = detail(pay)
print(f"       detail.error = {d.get('error')!r}, price = {d.get('price')!r}, "
      f"can_reactivate = {d.get('can_reactivate')!r}")
if d.get("error") != "subscription_required":
    fails.append("402 body did not identify itself as subscription_required")

print("\n== a comped login keeps full access (the owner is not locked out) ==")
c, tutor = call("POST", "/api/login", {"identifier": "tutor", "password": "tutor"},
                expect=200, label="login as 'tutor'")
tt = token_of(tutor)
call("GET", "/api/courses", token=tt, expect=200, label="GET /api/courses as tutor")
call("GET", "/api/admin/students", token=tt, expect=200, label="tutor dashboard")
c, mem = call("GET", "/api/me", token=tt, expect=200, label="/api/me as tutor")
print(f"       plan = {((mem or {}).get('plan') or {}).get('plan')!r}")

print("\n== the free demo still works, and only on its one subject ==")
email = f"guard+{int(time.time())}@example.com"
c, pl = call("GET", "/api/plan", label="/api/plan (public)")
codes = [x["code"] for x in (pl or {}).get("courses", [])]
demo_code, other = codes[0], codes[1]
c, dm = call("POST", "/api/demo", {"email": email, "course_code": demo_code},
             expect=200, label="start a free demo")
dt = token_of(dm)
call("GET", "/api/courses", token=dt, expect=200, label="demo: course list")
call("GET", f"/api/course/{other}", token=dt, expect=403, label="demo: another subject")
call("POST", "/api/demo", {"email": email, "course_code": demo_code}, expect=409,
     label="demo: second time on the same email")

print("\n== signup still refuses to create an account without payment ==")
call("POST", "/api/register", {"identifier": "nobody@example.com", "password": "longenough1"},
     expect=402, label="register with no session_id")

print("\n== webhook rejects anything it cannot verify ==")
# 503 when no whsec_ is configured on this deployment, 400 when one is set and the
# signature does not verify. Both mean "refused".
c, wh = call("POST", "/api/billing/webhook", {"type": "checkout.session.completed"},
             label="webhook with no signature")
if c not in (400, 503):
    fails.append(f"webhook: got {c}, wanted 400 or 503")
print(f"       -> {c}: {(wh or {}).get('detail')}")

print("\n== a real subscription, a lapse, and a reactivation ==")
con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
row = con.execute("SELECT user_id FROM demo_uses WHERE email=?", (email,)).fetchone()
uid = row["user_id"] if row else None
con.close()
print(f"       demo account id = {uid}")
sub_email = f"sub{int(time.time())}@example.com"
dbsql("UPDATE users SET demo_until=NULL, subscriber_email=? WHERE id=?", (sub_email, uid))
dbsql("INSERT OR REPLACE INTO subscribers(email, status, created_at, updated_at) "
      "VALUES(?,?,?,?)", (sub_email, "active", "2026-01-01T00:00:00+00:00",
                          "2026-01-01T00:00:00+00:00"))
c, me2 = call("GET", "/api/me", token=dt, expect=200, label="/api/me as subscriber")
print(f"       plan = {((me2 or {}).get('plan') or {}).get('plan')!r}")
call("GET", "/api/courses", token=dt, expect=200, label="subscriber: content opens")

dbsql("UPDATE subscribers SET status='past_due' WHERE email=?", (sub_email,))
c, me3 = call("GET", "/api/me", token=dt, expect=200, label="/api/me after a failed payment")
p3 = (me3 or {}).get("plan") or {}
print(f"       plan = {p3.get('plan')!r}, status = {p3.get('status')!r}")
call("GET", "/api/courses", token=dt, expect=402, label="past_due: content locks")
c, body3 = call("GET", "/api/courses", token=dt, expect=402, label="past_due 402 body")
if not detail(body3).get("can_reactivate"):
    fails.append("a lapsed subscriber was not offered reactivation")

dbsql("UPDATE subscribers SET status='canceled' WHERE email=?", (sub_email,))
call("GET", "/api/courses", token=dt, expect=402, label="canceled: content stays locked")

dbsql("UPDATE subscribers SET status='active' WHERE email=?", (sub_email,))
call("GET", "/api/courses", token=dt, expect=200, label="reactivated: content opens again")

print("\n== a demo that ran out is refused, not silently allowed ==")
dbsql("UPDATE users SET demo_until='2020-01-01T00:00:00+00:00' WHERE id=?", (uid,))
c, me4 = call("GET", "/api/me", token=dt, expect=200, label="/api/me for an expired demo")
p4 = (me4 or {}).get("plan") or {}
print(f"       plan = {p4.get('plan')!r}")
call("GET", "/api/courses", token=dt, expect=402, label="expired demo: content locks")

print("\n== billing routes stay reachable while locked out ==")
call("POST", "/api/billing/restart", token=dt, label="/api/billing/restart reaches Stripe")
call("POST", "/api/billing/portal", {"email": sub_email}, label="/api/billing/portal reaches Stripe")

print("\n" + ("ALL GUARDS PASSED" if not fails else f"{len(fails)} FAILURE(S):"))
for f in fails:
    print("   -", f)
sys.exit(1 if fails else 0)
