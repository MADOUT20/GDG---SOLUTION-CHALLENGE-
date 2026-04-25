"""
RahatSetu — Supabase setup script.
Runs schema + seed via Management API, then verifies with supabase-py.
"""
from __future__ import annotations
import os, sys, json, requests
from pathlib import Path

BASE   = Path(__file__).resolve().parent
URL    = "https://scorquajwibcilceutnx.supabase.co"
KEY    = "sb_publishable_xLdUq8mudLRS96Vdjy4CZw_wxXlY3YB"
REF    = "scorquajwibcilceutnx"
MGMT   = f"https://api.supabase.com/v1/projects/{REF}/database/query"

SCHEMA = (BASE / "supabase" / "schema.sql").read_text()
SEED   = (BASE / "supabase" / "seed.sql").read_text()

HEADERS_REST = {
    "apikey":        KEY,
    "Authorization": f"Bearer {KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "return=minimal",
}

# ── 1. Try Management API ────────────────────────────────────────────────────
def run_mgmt_sql(sql: str, label: str) -> bool:
    try:
        r = requests.post(MGMT, headers={"Authorization": f"Bearer {KEY}",
                                          "Content-Type": "application/json"},
                          json={"query": sql}, timeout=20)
        if r.status_code in (200, 201):
            print(f"  [mgmt] {label} — OK")
            return True
        print(f"  [mgmt] {label} — {r.status_code}: {r.text[:120]}")
    except Exception as e:
        print(f"  [mgmt] {label} — error: {e}")
    return False

# ── 2. Try supabase-py insert (DML only, tables must exist) ─────────────────
def supabase_seed() -> bool:
    try:
        from supabase import create_client
        sb = create_client(URL, KEY)

        # check if regions already seeded
        rows = sb.table("regions").select("id").limit(1).execute().data
        if rows:
            print("  [supabase-py] Tables already seeded — skipping seed.")
            return True

        # baseline
        sb.table("baseline").insert({"coverage":11,"communities_reached":500,
                                      "critical_areas_served":30,"resource_waste":45}).execute()
        # benefits
        sb.table("benefits").insert([
            {"title":"Targeted allocation","description":"Move teams and supplies using actual district-level need instead of assumptions."},
            {"title":"Faster response","description":"Fresh reports and donations update the same operating picture used by coordinators."},
            {"title":"Measurable planning","description":"Coverage, gaps, and recent actions stay visible for every region in one place."},
        ]).execute()
        # sources
        sb.table("sources").insert([
            {"name":"Paper Surveys","description":"Field worker paper forms digitized into the shared hub.","records":452,"created_at":"2026-04-17T08:20"},
            {"name":"Excel Sheets","description":"Legacy spreadsheets consolidated from partner NGOs.","records":328,"created_at":"2026-04-17T08:20"},
            {"name":"Mobile App Data","description":"Volunteer check-ins collected from mobile outreach visits.","records":215,"created_at":"2026-04-17T08:20"},
            {"name":"Health Center Reports","description":"Clinic and community health updates from district partners.","records":189,"created_at":"2026-04-17T08:20"},
            {"name":"School Data","description":"Education and child welfare needs reported by schools.","records":267,"created_at":"2026-04-17T08:20"},
            {"name":"Government Surveys","description":"District survey snapshots shared by public agencies.","records":156,"created_at":"2026-04-17T08:20"},
        ]).execute()
        # regions
        sb.table("regions").insert([
            {"name":"Mumbai","needs":950,"volunteers":136,"target_volunteers":205,"focus":"Water access, medical support, and dense community outreach."},
            {"name":"Thane","needs":890,"volunteers":110,"target_volunteers":188,"focus":"Shelter support, health camp staffing, and flood preparedness."},
            {"name":"Pune","needs":780,"volunteers":95,"target_volunteers":150,"focus":"Education continuity, family ration kits, and senior care visits."},
            {"name":"Nagpur","needs":620,"volunteers":65,"target_volunteers":100,"focus":"Nutrition kits, adolescent health outreach, and local transport."},
            {"name":"Nashik","needs":540,"volunteers":55,"target_volunteers":75,"focus":"Water logistics, anganwadi support, and school meal coverage."},
            {"name":"Aurangabad","needs":450,"volunteers":45,"target_volunteers":45,"focus":"Monitor emerging needs and maintain standby volunteer readiness."},
        ]).execute()
        # activities
        sb.table("activities").insert([
            {"title":"Team deployed to Mumbai","detail":"16 volunteers assigned. No extra deployment note.","type":"deployment","created_at":"2026-04-17T01:08"},
            {"title":"District records consolidated","detail":"Six source streams were merged into one planning interface.","type":"aggregation","created_at":"2026-04-17T08:20"},
            {"title":"Priority heatmap refreshed","detail":"Mumbai and Thane stayed on top after the latest district review.","type":"analysis","created_at":"2026-04-17T08:45"},
            {"title":"Volunteer plan reviewed","detail":"Deployment shortlist prepared for Mumbai, Thane, and Pune first.","type":"deployment","created_at":"2026-04-17T09:10"},
        ]).execute()
        # deployments
        sb.table("deployments").insert({"region":"Mumbai","volunteers":16,"note":"","created_at":"2026-04-17T01:08"}).execute()

        print("  [supabase-py] Seed complete.")
        return True
    except Exception as e:
        print(f"  [supabase-py] seed error: {e}")
        return False

# ── 3. Verify ────────────────────────────────────────────────────────────────
def verify() -> bool:
    try:
        from supabase import create_client
        sb = create_client(URL, KEY)
        regions = sb.table("regions").select("name,needs").execute().data
        if regions:
            print(f"\n  ✅ Connected! {len(regions)} regions in Supabase:")
            for r in regions:
                print(f"     {r['name']}  needs={r['needs']}")
            return True
        else:
            print("  ⚠️  Connected but regions table is empty.")
            return False
    except Exception as e:
        print(f"  ❌ Verify failed: {e}")
        return False

# ── Main ─────────────────────────────────────────────────────────────────────
print("\n=== RahatSetu Supabase Setup ===\n")

# Step 1 — schema via Management API
print("Step 1: Creating tables via Management API ...")
schema_ok = run_mgmt_sql(SCHEMA, "schema.sql")

if not schema_ok:
    print("  Management API unavailable — assuming tables already exist in DB.\n")

# Step 2 — seed data via supabase-py client
print("\nStep 2: Seeding data via supabase-py ...")
supabase_seed()

# Step 3 — verify
print("\nStep 3: Verifying connection ...")
verify()

print("\n=== Done ===\n")
