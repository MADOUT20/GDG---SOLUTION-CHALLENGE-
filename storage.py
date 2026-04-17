from __future__ import annotations

import json
import os
import warnings
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "ngo_state.json"
SUPABASE_KEY_ENV_NAMES = ("SUPABASE_SECRET_KEY", "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_KEY")


class StorageError(RuntimeError):
    pass


def _load_seed_state() -> dict[str, Any]:
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


class JsonStore:
    mode = "json"
    mode_label = "Local JSON"

    def __init__(self, data_file: Path) -> None:
        self.data_file = data_file

    def read_state(self) -> dict[str, Any]:
        with self.data_file.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _write_state(self, state: dict[str, Any]) -> None:
        with self.data_file.open("w", encoding="utf-8") as file:
            json.dump(state, file, indent=2)

    def _find_region(self, state: dict[str, Any], region_name: str) -> dict[str, Any]:
        normalized = region_name.strip().lower()
        for region in state["regions"]:
            if region["name"].lower() == normalized:
                return region
        raise ValueError(f"Unknown region: {region_name}")

    def _add_activity(self, state: dict[str, Any], title: str, detail: str, activity_type: str, created_at: str) -> None:
        state["activities"].insert(
            0,
            {
                "title": title,
                "detail": detail,
                "type": activity_type,
                "created_at": created_at,
            },
        )
        state["activities"] = state["activities"][:12]

    def create_report(
        self,
        *,
        region_name: str,
        category: str,
        priority: str,
        description: str,
        people_affected: int,
        created_at: str,
        needs_increase: int,
        activity_title: str,
        activity_detail: str,
        activity_type: str,
    ) -> None:
        state = self.read_state()
        region = self._find_region(state, region_name)
        state["reports"].insert(
            0,
            {
                "region": region["name"],
                "category": category,
                "priority": priority,
                "description": description,
                "people_affected": people_affected,
                "created_at": created_at,
            },
        )
        region["needs"] += needs_increase
        self._add_activity(state, activity_title, activity_detail, activity_type, created_at)
        self._write_state(state)

    def create_donation(
        self,
        *,
        donor_name: str,
        region_name: str,
        category: str,
        quantity: int,
        notes: str,
        created_at: str,
        needs_after: int,
        activity_title: str,
        activity_detail: str,
        activity_type: str,
    ) -> None:
        state = self.read_state()
        region = self._find_region(state, region_name)
        state["donations"].insert(
            0,
            {
                "donor_name": donor_name,
                "region": region["name"],
                "category": category,
                "quantity": quantity,
                "notes": notes,
                "created_at": created_at,
            },
        )
        region["needs"] = needs_after
        self._add_activity(state, activity_title, activity_detail, activity_type, created_at)
        self._write_state(state)

    def create_deployment(
        self,
        *,
        region_name: str,
        volunteers: int,
        note: str,
        created_at: str,
        volunteers_after: int,
        activity_title: str,
        activity_detail: str,
        activity_type: str,
    ) -> None:
        state = self.read_state()
        region = self._find_region(state, region_name)
        state["deployments"].insert(
            0,
            {
                "region": region["name"],
                "volunteers": volunteers,
                "note": note,
                "created_at": created_at,
            },
        )
        region["volunteers"] = volunteers_after
        self._add_activity(state, activity_title, activity_detail, activity_type, created_at)
        self._write_state(state)

    def create_source(
        self,
        *,
        name: str,
        description: str,
        records: int,
        created_at: str,
        activity_title: str,
        activity_detail: str,
        activity_type: str,
    ) -> None:
        state = self.read_state()
        state["sources"].append(
            {
                "name": name,
                "description": description,
                "records": records,
                "created_at": created_at,
            },
        )
        self._add_activity(state, activity_title, activity_detail, activity_type, created_at)
        self._write_state(state)


class SupabaseStore:
    mode = "supabase"
    mode_label = "Supabase"

    def __init__(self, url: str, key: str, seed_state: dict[str, Any]) -> None:
        try:
            from supabase import create_client
        except ImportError as exc:
            raise StorageError(
                "Supabase is configured, but the Python client is not installed. Run `python3 -m pip install -r requirements.txt`."
            ) from exc

        self.client = create_client(url, key)
        self.seed_state = seed_state

    def _run(self, query: Any, action: str) -> Any:
        try:
            return query.execute()
        except Exception as exc:
            raise StorageError(
                f"Supabase {action} failed. Run `supabase/schema.sql`, then verify SUPABASE_URL and your server-side key."
            ) from exc

    def _select_all(self, table: str, *, order_by: str | None = None, desc: bool = False) -> list[dict[str, Any]]:
        query = self.client.table(table).select("*")
        if order_by:
            query = query.order(order_by, desc=desc)
        response = self._run(query, f"read on `{table}`")
        return list(response.data or [])

    def _get_region(self, region_name: str) -> dict[str, Any]:
        response = self._run(
            self.client.table("regions").select("*").ilike("name", region_name.strip()).limit(1),
            "region lookup",
        )
        data = list(response.data or [])
        if not data:
            raise ValueError(f"Unknown region: {region_name}")
        return data[0]

    def read_state(self) -> dict[str, Any]:
        baseline_rows = self._select_all("baseline", order_by="id")
        benefits = self._select_all("benefits", order_by="id") or self.seed_state["benefits"]
        return {
            "baseline": baseline_rows[0] if baseline_rows else self.seed_state["baseline"],
            "benefits": benefits,
            "sources": self._select_all("sources", order_by="records", desc=True),
            "regions": self._select_all("regions", order_by="name"),
            "activities": self._select_all("activities", order_by="created_at", desc=True),
            "reports": self._select_all("reports", order_by="created_at", desc=True),
            "donations": self._select_all("donations", order_by="created_at", desc=True),
            "deployments": self._select_all("deployments", order_by="created_at", desc=True),
        }

    def create_report(
        self,
        *,
        region_name: str,
        category: str,
        priority: str,
        description: str,
        people_affected: int,
        created_at: str,
        needs_increase: int,
        activity_title: str,
        activity_detail: str,
        activity_type: str,
    ) -> None:
        region = self._get_region(region_name)
        self._run(
            self.client.table("reports").insert(
                {
                    "region": region["name"],
                    "category": category,
                    "priority": priority,
                    "description": description,
                    "people_affected": people_affected,
                    "created_at": created_at,
                }
            ),
            "report insert",
        )
        self._run(
            self.client.table("regions").update({"needs": region["needs"] + needs_increase}).eq("id", region["id"]),
            "region update",
        )
        self._run(
            self.client.table("activities").insert(
                {
                    "title": activity_title,
                    "detail": activity_detail,
                    "type": activity_type,
                    "created_at": created_at,
                }
            ),
            "activity insert",
        )

    def create_donation(
        self,
        *,
        donor_name: str,
        region_name: str,
        category: str,
        quantity: int,
        notes: str,
        created_at: str,
        needs_after: int,
        activity_title: str,
        activity_detail: str,
        activity_type: str,
    ) -> None:
        region = self._get_region(region_name)
        self._run(
            self.client.table("donations").insert(
                {
                    "donor_name": donor_name,
                    "region": region["name"],
                    "category": category,
                    "quantity": quantity,
                    "notes": notes,
                    "created_at": created_at,
                }
            ),
            "donation insert",
        )
        self._run(
            self.client.table("regions").update({"needs": needs_after}).eq("id", region["id"]),
            "region update",
        )
        self._run(
            self.client.table("activities").insert(
                {
                    "title": activity_title,
                    "detail": activity_detail,
                    "type": activity_type,
                    "created_at": created_at,
                }
            ),
            "activity insert",
        )

    def create_deployment(
        self,
        *,
        region_name: str,
        volunteers: int,
        note: str,
        created_at: str,
        volunteers_after: int,
        activity_title: str,
        activity_detail: str,
        activity_type: str,
    ) -> None:
        region = self._get_region(region_name)
        self._run(
            self.client.table("deployments").insert(
                {
                    "region": region["name"],
                    "volunteers": volunteers,
                    "note": note,
                    "created_at": created_at,
                }
            ),
            "deployment insert",
        )
        self._run(
            self.client.table("regions").update({"volunteers": volunteers_after}).eq("id", region["id"]),
            "region update",
        )
        self._run(
            self.client.table("activities").insert(
                {
                    "title": activity_title,
                    "detail": activity_detail,
                    "type": activity_type,
                    "created_at": created_at,
                }
            ),
            "activity insert",
        )

    def create_source(
        self,
        *,
        name: str,
        description: str,
        records: int,
        created_at: str,
        activity_title: str,
        activity_detail: str,
        activity_type: str,
    ) -> None:
        self._run(
            self.client.table("sources").insert(
                {
                    "name": name,
                    "description": description,
                    "records": records,
                    "created_at": created_at,
                }
            ),
            "source insert",
        )
        self._run(
            self.client.table("activities").insert(
                {
                    "title": activity_title,
                    "detail": activity_detail,
                    "type": activity_type,
                    "created_at": created_at,
                }
            ),
            "activity insert",
        )


def create_store() -> JsonStore | SupabaseStore:
    seed_state = _load_seed_state()
    url = os.getenv("SUPABASE_URL", "").strip()
    key = next((value for name in SUPABASE_KEY_ENV_NAMES if (value := os.getenv(name, "").strip())), "")

    if not url and not key:
        return JsonStore(DATA_FILE)

    if not url or not key:
        warnings.warn("Incomplete Supabase configuration detected. Falling back to the local JSON store.", stacklevel=2)
        return JsonStore(DATA_FILE)

    try:
        return SupabaseStore(url, key, seed_state)
    except StorageError as error:
        warnings.warn(f"{error} Falling back to the local JSON store.", stacklevel=2)
        return JsonStore(DATA_FILE)
