"""End-to-end API smoke test against a running server on 127.0.0.1:8000."""

import json
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000/api"
FAILURES = []


def call(method, path, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode()
            return resp.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            return exc.code, json.loads(raw)
        except json.JSONDecodeError:
            return exc.code, raw


def check(label, ok, detail=""):
    print(f"{'OK  ' if ok else 'FAIL'} {label}" + (f" -> {detail}" if detail and not ok else ""))
    if not ok:
        FAILURES.append(label)


def login(email, password):
    status, data = call("POST", "/auth/token/", {"email": email, "password": password})
    check(f"login {email}", status == 200, f"{status} {data}")
    return data["access"] if status == 200 else None


print("=== 1. Registration ===")
new_email = f"newuser{int(time.time())}@test.com"
status, data = call(
    "POST",
    "/auth/register/",
    {"email": new_email, "password": "Str0ngPass!2026", "first_name": "New", "last_name": "User"},
)
check("register new student", status == 201, f"{status} {data}")

status, data = call("POST", "/auth/register/", {"email": new_email, "password": "Str0ngPass!2026"})
check("register rejects duplicate email", status == 400, f"{status} {data}")

status, data = call("POST", "/auth/register/", {"email": "weak@test.com", "password": "123"})
check("register rejects weak password", status == 400, f"{status} {data}")

new_token = login(new_email, "Str0ngPass!2026")
status, me = call("GET", "/auth/me/", token=new_token)
check(
    "new account is STUDENT with 0 credits",
    status == 200 and me["role"] == "STUDENT" and me["credit_balance"] == 0,
    f"{status} {me}",
)

print("\n=== 2. Catalog (anonymous) ===")
status, courses = call("GET", "/courses/")
items = courses["results"] if isinstance(courses, dict) else courses
check("public catalog", status == 200 and len(items) > 0, f"{status} {len(items) if items else 0}")

print("\n=== 3. Student flow ===")
student_token = login("guest@gmail.com", "Guest123!")
status, packs = call("GET", "/credit-packs/", token=student_token)
pack_items = packs["results"] if isinstance(packs, dict) else packs
check("credit packs", status == 200 and len(pack_items) > 0, f"{status} {packs}")

status, purchase = call(
    "POST",
    "/transactions/purchase/",
    {"pack_id": pack_items[0]["id"], "payment_method": "CARD"},
    token=student_token,
)
check("simulated purchase", status in (200, 201), f"{status} {purchase}")

status, enrollments = call("GET", "/enrollments/", token=student_token)
check("list enrollments", status == 200, f"{status} {enrollments}")

print("\n=== 4. Teacher flow (create / preview / update) ===")
teacher_token = login("teacher@platform.com", "Teacher123!")
payload = {
    "title": "Smoke Preview Course",
    "description": "Course used by the smoke test.",
    "price_credits": 40,
    "level": "BEGINNER",
    "category": "QA",
    "content_focus": "MIXED",
    "is_active": False,
    "modules": [
        {
            "title": "Intro video",
            "order": 1,
            "module_type": "VIDEO",
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "video_provider": "YOUTUBE",
        },
        {
            "title": "Handbook",
            "order": 2,
            "module_type": "PDF",
            "pdf_url": "example.com/handbook.pdf",
        },
    ],
}
status, course = call("POST", "/courses/", payload, token=teacher_token)
check("teacher creates course", status == 201, f"{status} {course}")
course_id = course["id"] if status == 201 else None

if course_id:
    status, detail = call("GET", f"/courses/{course_id}/", token=teacher_token)
    check(
        "preview: teacher reads own INACTIVE course with modules",
        status == 200 and detail["is_active"] is False and len(detail.get("modules", [])) == 2,
        f"{status} {detail}",
    )
    check(
        "preview: PDF url normalised to https",
        status == 200 and detail["modules"][1]["pdf_url"].startswith("https://"),
        detail["modules"][1]["pdf_url"] if status == 200 else "",
    )

    status, anon = call("GET", f"/courses/{course_id}/")
    check("inactive course hidden from students", status == 404, f"{status} {anon}")

    status, updated = call(
        "PATCH",
        f"/courses/{course_id}/",
        {"title": "Smoke Preview Course v2", "price_credits": 45, "modules": payload["modules"]},
        token=teacher_token,
    )
    check("teacher updates course", status == 200, f"{status} {updated}")

    status, students = call("GET", f"/courses/{course_id}/students/", token=teacher_token)
    check("teacher student list", status == 200, f"{status} {students}")

    status, _ = call("DELETE", f"/courses/{course_id}/", token=teacher_token)
    check("teacher deletes course", status == 204, str(status))

print("\n=== 5. Admin flow ===")
admin_token = login("admin@platform.com", "Admin123!")
status, stats = call("GET", "/admin/stats/", token=admin_token)
check(
    "admin stats",
    status == 200 and "users" in stats and "payments" in stats and "popular_courses" in stats,
    f"{status} {stats}",
)

status, users = call("GET", "/users/", token=admin_token)
user_items = users["results"] if isinstance(users, dict) else users
check("admin user list", status == 200 and len(user_items) > 0, f"{status} {users}")

status, forbidden = call("GET", "/admin/stats/", token=student_token)
check("student cannot read admin stats", status == 403, f"{status} {forbidden}")

print("\n=== 6. Chatbot ===")
status, reply = call("POST", "/chatbot/", {"message": "Comment acheter des credits ?"})
check("chatbot replies anonymously", status == 200 and reply.get("reply"), f"{status} {reply}")

print("\n=== 7. Schema ===")
req = urllib.request.Request("http://127.0.0.1:8000/api/schema/", method="GET")
try:
    with urllib.request.urlopen(req) as resp:
        check("OpenAPI schema", resp.status == 200, str(resp.status))
except urllib.error.HTTPError as exc:
    check("OpenAPI schema", False, str(exc.code))

print("\n" + ("ALL CHECKS PASSED" if not FAILURES else f"FAILURES: {FAILURES}"))
