# agents/planner_agent/app.py
# PlannerAgent: orchestrates RecipeAgent + GroceryAgent
# - receives a user profile
# - queries RecipeAgent for candidate recipes
# - builds a D-day plan (breakfast/lunch/dinner)
# - asks GroceryAgent to aggregate ingredients
# - returns plan + grocery list + trace_id

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import httpx
import uuid
import datetime
import random

app = FastAPI(title="PlannerAgent")

RECIPE_AGENT_URL = "http://localhost:8001/a2a/get_recipes"
GROCERY_AGENT_URL = "http://localhost:8002/a2a/generate_grocery_list"
HTTP_TIMEOUT = 15.0  # seconds


class Profile(BaseModel):
    diet: str = "veg"
    region: str = "All"
    allergies: List[str] = []
    days: int = 3
    servings: int = 2
    # optional: budget, spice_level, max_cook_time_min etc.
    budget: Optional[float] = None
    spice_level: Optional[str] = None


def safe_post_json(url: str, body: dict, timeout: float = HTTP_TIMEOUT) -> dict:
    """Send POST and return JSON or raise HTTPException."""
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(url, json=body)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream error calling {url}: {e}")


@app.post("/a2a/plan_meals")
def plan_meals(profile: Profile):
    trace_id = str(uuid.uuid4())
    # track used recipe ids across entire plan so we don't repeat
    used_recipe_ids = set()
    plan: List[Dict[str, Any]] = []

    for day in range(1, max(1, profile.days) + 1):
        day_meals: List[Dict[str, Any]] = []

        for meal_name in ["breakfast", "lunch", "dinner"]:
            req_body = {
                "query": f"{meal_name} {profile.region if profile.region and profile.region != 'All' else ''}".strip(),
                "k": 6,
                "filters": {
                    "diet": profile.diet,
                    "region": profile.region
                }
            }

            # call RecipeAgent (synchronous helper)
            try:
                resp = safe_post_json(RECIPE_AGENT_URL, req_body)
                candidates = resp.get("recipes", []) if isinstance(resp, dict) else []
            except HTTPException as e:
                # upstream failure: include a placeholder and continue
                day_meals.append({
                    "meal_name": meal_name,
                    "recipe_id": None,
                    "title": None,
                    "note": f"recipe service error: {e.detail}"
                })
                continue

            # choose a candidate not used yet (randomize for variety)
            chosen = None
            random.shuffle(candidates)
            for c in candidates:
                rid = c.get("id")
                if not rid:
                    continue
                if rid not in used_recipe_ids:
                    chosen = c
                    break

            # fallback: choose first candidate even if repeated (if any)
            if not chosen and candidates:
                chosen = candidates[0]

            if chosen:
                used_recipe_ids.add(chosen.get("id"))
                day_meals.append({
                    "meal_name": meal_name,
                    "recipe_id": chosen.get("id"),
                    "title": chosen.get("title"),
                    "cook_time_min": chosen.get("cook_time_min")
                })
            else:
                # no candidates found
                day_meals.append({
                    "meal_name": meal_name,
                    "recipe_id": None,
                    "title": None,
                    "note": "no recipe found"
                })

        plan.append({"day": day, "meals": day_meals})

    # call GroceryAgent to aggregate ingredients; proceed even if it fails
    grocery_list = []
    try:
        grocery_resp = safe_post_json(GROCERY_AGENT_URL, {"plan": plan})
        grocery_list = grocery_resp.get("grocery_list", [])
    except HTTPException:
        # don't block response — return plan with empty grocery and a note
        grocery_list = []

    return {
        "trace_id": trace_id,
        "plan": plan,
        "grocery": grocery_list,
        "generated_at": datetime.datetime.utcnow().isoformat()
    }


@app.get("/health")
def health():
    return {"status": "ok"}
