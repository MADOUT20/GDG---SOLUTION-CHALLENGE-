from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from threading import Lock
from urllib.parse import quote

from flask import Flask, jsonify, redirect, render_template, request, session

from storage import StorageError, create_store

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv() -> bool:
        return False


load_dotenv()

STORE_LOCK = Lock()
app = Flask(__name__)
app.secret_key = "ngo-hub-secret-key-2026"
store = create_store()

ROLE_PROFILES = {
    "admin": {
        "username": "ADMIN-SRAS-2026",
        "display_name": "Admin Control Desk",
        "landing": "/dashboard#heatmap",
    },
    "user": {
        "username": "USER-NGO-2026",
        "display_name": "NGO Partner User",
        "landing": "/dashboard",
    },
}
DEFAULT_ROLE = "user"
USER_PORTAL_PROFILE = {
    "ngo_name": "Sahyog Relief Foundation",
    "registration_id": "NGO-MH-2026-0148",
    "focus_area": "Emergency health outreach, nutrition support, and family relief coordination.",
    "district": "Mumbai",
    "status": "Active Partner",
    "contact_email": "coordination@sahyog-relief.org",
    "contact_phone": "022-49150800",
}
USER_ACCOUNT_PROFILE = {
    "desk": "Community Response Desk",
    "district": "Mumbai",
    "status": "Profile Active",
    "contact_email": "field.user@sahyog-relief.org",
    "contact_phone": "022-49150800",
}
DONATION_FORM_URL = "https://docs.google.com/forms/u/0/"


def now_iso() -> str:
    return datetime.now().isoformat(timespec="minutes")


def today_prefix() -> str:
    return datetime.now().date().isoformat()


def title_case(value: str) -> str:
    return " ".join(part.capitalize() for part in value.replace("_", " ").split())


def classify_score(score: int) -> tuple[str, str]:
    if score >= 90:
        return "critical", "Critical"
    if score >= 75:
        return "high", "High"
    if score >= 50:
        return "medium", "Medium"
    return "low", "Emerging"


def find_region(state: dict, region_name: str) -> dict:
    normalized = region_name.strip().lower()
    for region in state["regions"]:
        if region["name"].lower() == normalized:
            return region
    raise ValueError(f"Unknown region: {region_name}")


def donation_impact(category: str, quantity: int) -> int:
    category_key = category.strip().lower()
    if category_key == "money":
        return min(150, max(20, quantity // 100))
    if category_key == "medical":
        return min(140, quantity * 3)
    if category_key == "food":
        return min(120, quantity * 2)
    return min(110, quantity * 2)


def region_view(region: dict) -> dict:
    score = min(100, round(region["needs"] / 10))
    severity_key, severity_label = classify_score(score)
    target = max(region["target_volunteers"], region["volunteers"])
    recommended = max(target - region["volunteers"], 0)
    deficit = region["volunteers"] - region["needs"]

    if recommended >= 70:
        action = f"CRITICAL - Deploy {recommended} more"
    elif recommended >= 35:
        action = f"HIGH - Deploy {recommended} more"
    elif recommended > 0:
        action = f"MEDIUM - Deploy {recommended} more"
    else:
        action = "Monitor current coverage"

    return {
        "name": region["name"],
        "needs": region["needs"],
        "volunteers": region["volunteers"],
        "deficit": deficit,
        "target_volunteers": target,
        "recommended_deploy": recommended,
        "score": score,
        "severity": severity_key,
        "severity_label": severity_label,
        "focus": region["focus"],
        "action_label": action,
    }


def build_impact_metrics(state: dict, regions: list[dict], summary: dict) -> list[dict]:
    baseline = state["baseline"]
    all_deployments = sum(entry["volunteers"] for entry in state["deployments"])
    all_reports = len(state["reports"])
    all_donations = len(state["donations"])

    communities_after = baseline["communities_reached"] + (all_deployments * 3) + (all_reports * 18) + (all_donations * 12)
    critical_after = min(100, baseline["critical_areas_served"] + (all_deployments // 8) + (all_donations * 2))
    waste_after = max(8, baseline["resource_waste"] - (all_deployments // 12) - (all_donations * 2))

    return [
        {
            "metric": "Volunteer Coverage",
            "before": f'{baseline["coverage"]}%',
            "after": f'{summary["current_coverage"]}%',
            "improvement": f'{summary["current_coverage"] - baseline["coverage"]:+} pts',
        },
        {
            "metric": "Communities Reached",
            "before": str(baseline["communities_reached"]),
            "after": str(communities_after),
            "improvement": f'+{communities_after - baseline["communities_reached"]}',
        },
        {
            "metric": "Critical Areas Served",
            "before": f'{baseline["critical_areas_served"]}%',
            "after": f"{critical_after}%",
            "improvement": f'+{critical_after - baseline["critical_areas_served"]} pts',
        },
        {
            "metric": "Resource Waste",
            "before": f'{baseline["resource_waste"]}%',
            "after": f"{waste_after}%",
            "improvement": f'-{baseline["resource_waste"] - waste_after} pts',
        },
    ]


def build_dashboard(state: dict | None = None) -> dict:
    current_state = deepcopy(state) if state is not None else store.read_state()
    regions = sorted((region_view(region) for region in current_state["regions"]), key=lambda item: item["score"], reverse=True)
    sources = sorted(current_state["sources"], key=lambda item: item["records"], reverse=True)

    total_needs = sum(region["needs"] for region in current_state["regions"])
    total_volunteers = sum(region["volunteers"] for region in current_state["regions"])
    current_coverage = int((total_volunteers / total_needs) * 100) if total_needs else 0
    today = today_prefix()

    summary = {
        "storage_backend": store.mode_label,
        "data_sources_connected": len(sources),
        "records_consolidated": sum(source["records"] for source in sources),
        "districts_mapped": len(current_state["regions"]),
        "total_needs": total_needs,
        "volunteers": total_volunteers,
        "current_coverage": current_coverage,
        "reports_today": sum(1 for report in current_state["reports"] if report["created_at"].startswith(today)),
        "donations_today": sum(1 for donation in current_state["donations"] if donation["created_at"].startswith(today)),
        "funds_committed": sum(donation["quantity"] for donation in current_state["donations"] if donation["category"].lower() == "money"),
        "resource_units": sum(donation["quantity"] for donation in current_state["donations"] if donation["category"].lower() != "money"),
        "deployed_today": sum(entry["volunteers"] for entry in current_state["deployments"] if entry["created_at"].startswith(today)),
    }

    activities = [
        {
            "title": activity["title"],
            "detail": activity["detail"],
            "type": title_case(activity["type"]),
            "display_time": activity["created_at"].replace("T", " "),
        }
        for activity in current_state["activities"][:8]
    ]

    return {
        "summary": summary,
        "sources": sources,
        "regions": regions,
        "allocations": regions,
        "benefits": current_state["benefits"],
        "activities": activities,
        "impact_metrics": build_impact_metrics(current_state, regions, summary),
    }


def parse_positive_int(payload: dict, field_name: str) -> int:
    raw_value = payload.get(field_name)
    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a whole number.") from exc
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")
    return value


def normalize_role(raw_role: str | None) -> str:
    role = str(raw_role or "").strip().lower()
    if role in ROLE_PROFILES:
        return role
    return DEFAULT_ROLE


def default_profile(role: str) -> dict:
    return ROLE_PROFILES[normalize_role(role)]


def donation_qr_url() -> str:
    encoded = quote(DONATION_FORM_URL, safe="")
    return f"https://api.qrserver.com/v1/create-qr-code/?size=540x540&data={encoded}"


def record_report(payload: dict) -> dict:
    required_fields = ["region", "category", "priority", "description"]
    for field in required_fields:
        if not str(payload.get(field, "")).strip():
            raise ValueError(f"{field} is required.")

    people_affected = parse_positive_int(payload, "people_affected")
    priority = str(payload["priority"]).strip().lower()
    priority_boost = {"low": 20, "medium": 50, "high": 100}
    if priority not in priority_boost:
        raise ValueError("priority must be Low, Medium, or High.")

    with STORE_LOCK:
        state = store.read_state()
        region = find_region(state, str(payload["region"]))
        category = str(payload["category"]).strip()
        created_at = now_iso()
        priority_label = priority.title()
        needs_increase = max(people_affected, priority_boost[priority])
        store.create_report(
            region_name=region["name"],
            category=category,
            priority=priority_label,
            description=str(payload["description"]).strip(),
            people_affected=people_affected,
            created_at=created_at,
            needs_increase=needs_increase,
            activity_title=f'Report logged for {region["name"]}',
            activity_detail=f"{priority_label} priority {category} report covering {people_affected} people.",
            activity_type="field_report",
        )
        return build_dashboard()


def login_page_context(
    *,
    error: str | None = None,
    selected_role: str = DEFAULT_ROLE,
    donation_success: str | None = None,
    donation_error: str | None = None,
) -> dict:
    preview = None
    preview_error = None
    role = normalize_role(selected_role)
    profile = default_profile(role)

    try:
        preview = build_dashboard()
    except StorageError as exc:
        preview_error = str(exc)

    return {
        "error": error,
        "preview": preview,
        "preview_error": preview_error,
        "role_profiles": ROLE_PROFILES,
        "selected_role": role,
        "selected_username": profile["username"],
        "donation_success": donation_success,
        "donation_error": donation_error,
        "donation_form_url": DONATION_FORM_URL,
        "donation_qr_url": donation_qr_url(),
    }


def emergency_page_context(
    *,
    error: str | None = None,
    success: str | None = None,
    selected_region: str = "",
) -> dict:
    dashboard = None
    preview_error = None

    try:
        dashboard = build_dashboard()
    except StorageError as exc:
        preview_error = str(exc)

    return {
        "error": error,
        "success": success,
        "dashboard": dashboard,
        "preview_error": preview_error,
        "selected_region": selected_region,
    }


def user_portal_context() -> dict:
    dashboard_payload = None
    dashboard_error = None

    try:
        dashboard_payload = build_dashboard()
    except StorageError as exc:
        dashboard_error = str(exc)

    return {
        "dashboard": dashboard_payload,
        "dashboard_error": dashboard_error,
        "profile_completion": 100,
        "user_profile": USER_PORTAL_PROFILE,
        "user_account": USER_ACCOUNT_PROFILE,
    }


@app.get("/")
def index() -> str:
    donation_state = request.args.get("donation", "").strip().lower()
    donation_success = None
    donation_error = None
    if donation_state == "success":
        donation_success = "Donation interest submitted successfully."
    elif donation_state == "error":
        donation_error = "Please complete the required donation fields before submitting."

    return render_template(
        "login.html",
        **login_page_context(donation_success=donation_success, donation_error=donation_error),
    )


@app.get("/dashboard")
def dashboard_page() -> str:
    role = normalize_role(session.get("role"))
    profile = default_profile(role)

    if role == "admin":
        return render_template(
            "index.html",
            demo_user=session.get("user", profile["display_name"]),
            demo_login=session.get("demo_username", profile["username"]),
            demo_role=role.title(),
            ngo_profile=USER_PORTAL_PROFILE,
        )

    return render_template(
        "user_dashboard.html",
        demo_user=session.get("user", profile["display_name"]),
        demo_login=session.get("demo_username", profile["username"]),
        demo_role=role.title(),
        **user_portal_context(),
    )


@app.get("/login")
def login_page() -> str:
    donation_state = request.args.get("donation", "").strip().lower()
    donation_success = None
    donation_error = None
    if donation_state == "success":
        donation_success = "Donation interest submitted successfully."
    elif donation_state == "error":
        donation_error = "Please complete the required donation fields before submitting."

    return render_template(
        "login.html",
        **login_page_context(donation_success=donation_success, donation_error=donation_error),
    )


@app.post("/login")
def login_submit():
    role = normalize_role(request.form.get("role"))
    profile = default_profile(role)
    username = request.form.get("username", "").strip() or profile["username"]
    captcha = request.form.get("captcha", "").strip()

    if not captcha:
        return render_template(
            "login.html",
            **login_page_context(error="Please complete the captcha to continue.", selected_role=role),
        )

    session["role"] = role
    session["user"] = profile["display_name"]
    session["demo_username"] = username
    return redirect(profile["landing"])


@app.get("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.post("/donation-interest")
def donation_interest_submit():
    donor_name = request.form.get("donor_name", "").strip()
    donor_email = request.form.get("donor_email", "").strip()

    if not donor_name or not donor_email:
        return redirect("/?donation=error#donationSection")

    return redirect("/?donation=success#donationSection")


@app.get("/emergency")
def emergency_report_page() -> str:
    selected_region = request.args.get("region", "").strip()
    return render_template("emergency.html", **emergency_page_context(selected_region=selected_region))


@app.post("/emergency")
def emergency_report_submit() -> str:
    payload = request.form.to_dict()

    try:
        record_report(payload)
        success = "Emergency report submitted successfully. The response dashboard has been updated."
        selected_region = str(payload.get("region", "")).strip()
        return render_template(
            "emergency.html",
            **emergency_page_context(success=success, selected_region=selected_region),
        )
    except ValueError as error:
        return render_template(
            "emergency.html",
            **emergency_page_context(error=str(error), selected_region=str(payload.get("region", "")).strip()),
        )
    except StorageError as error:
        return render_template(
            "emergency.html",
            **emergency_page_context(error=str(error), selected_region=str(payload.get("region", "")).strip()),
        )


@app.get("/api/dashboard")
def dashboard() -> tuple:
    try:
        return jsonify(build_dashboard()), 200
    except StorageError as error:
        return jsonify({"error": str(error)}), 500


@app.post("/api/reports")
def create_report() -> tuple:
    payload = request.get_json(silent=True) or {}

    try:
        dashboard_payload = record_report(payload)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except StorageError as error:
        return jsonify({"error": str(error)}), 500

    return jsonify({"message": "Field report recorded.", "dashboard": dashboard_payload}), 201


@app.post("/api/donations")
def create_donation() -> tuple:
    payload = request.get_json(silent=True) or {}

    required_fields = ["donor_name", "region", "category"]
    for field in required_fields:
        if not str(payload.get(field, "")).strip():
            return jsonify({"error": f"{field} is required."}), 400

    try:
        quantity = parse_positive_int(payload, "quantity")
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    with STORE_LOCK:
        try:
            state = store.read_state()
            region = find_region(state, payload["region"])
            category = payload["category"].strip()
            donor_name = payload["donor_name"].strip()
            created_at = now_iso()
            store.create_donation(
                donor_name=donor_name,
                region_name=region["name"],
                category=category,
                quantity=quantity,
                notes=str(payload.get("notes", "")).strip(),
                created_at=created_at,
                needs_after=max(0, region["needs"] - donation_impact(category, quantity)),
                activity_title=f"{category} donation registered",
                activity_detail=f"{donor_name} supported {region['name']} with {quantity} units.",
                activity_type="donation",
            )
            dashboard_payload = build_dashboard()
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        except StorageError as error:
            return jsonify({"error": str(error)}), 500

    return jsonify({"message": "Donation saved and reflected on the dashboard.", "dashboard": dashboard_payload}), 201


@app.post("/api/deployments")
def create_deployment() -> tuple:
    payload = request.get_json(silent=True) or {}

    if not str(payload.get("region", "")).strip():
        return jsonify({"error": "region is required."}), 400

    try:
        volunteers = parse_positive_int(payload, "volunteers")
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    note = str(payload.get("note", "")).strip()

    with STORE_LOCK:
        try:
            state = store.read_state()
            region = find_region(state, payload["region"])
            store.create_deployment(
                region_name=region["name"],
                volunteers=volunteers,
                note=note,
                created_at=now_iso(),
                volunteers_after=region["volunteers"] + volunteers,
                activity_title=f'Team deployed to {region["name"]}',
                activity_detail=f'{volunteers} volunteers assigned. {note or "No extra deployment note."}',
                activity_type="deployment",
            )
            dashboard_payload = build_dashboard()
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        except StorageError as error:
            return jsonify({"error": str(error)}), 500

    return jsonify({"message": "Deployment updated.", "dashboard": dashboard_payload}), 201


@app.post("/api/sources")
def create_source() -> tuple:
    payload = request.get_json(silent=True) or {}

    if not str(payload.get("name", "")).strip():
        return jsonify({"error": "name is required."}), 400

    try:
        records = parse_positive_int(payload, "records")
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    description = str(payload.get("description", "")).strip() or "Uploaded through the NGO intake desk."

    with STORE_LOCK:
        try:
            source_name = payload["name"].strip()
            store.create_source(
                name=source_name,
                description=description,
                records=records,
                created_at=now_iso(),
                activity_title="Fresh data batch aggregated",
                activity_detail=f"{source_name} contributed {records} new records to the planning view.",
                activity_type="aggregation",
            )
            dashboard_payload = build_dashboard()
        except StorageError as error:
            return jsonify({"error": str(error)}), 500

    return jsonify({"message": "New data source connected.", "dashboard": dashboard_payload}), 201


if __name__ == "__main__":
    app.run(debug=True)
