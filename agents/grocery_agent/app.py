from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json, os
from typing import List, Dict, Any
from src.utils.units import canonicalize, qty_to_grams, load_mapping

app = FastAPI(title="GroceryAgent")

DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'recipes')

class PlanInput(BaseModel):
    plan: List[Dict[str, Any]]

def load_all_recipes():
    recipes = {}
    if not os.path.isdir(DATA_DIR):
        return recipes
    for fname in os.listdir(DATA_DIR):
        if not fname.endswith('.json'):
            continue
        with open(os.path.join(DATA_DIR, fname), 'r', encoding='utf-8') as fh:
            r = json.load(fh)
            recipes[r['id']] = r
    return recipes

@app.post('/a2a/generate_grocery_list')
async def generate_grocery_list(payload: PlanInput):
    recipes = load_all_recipes()
    if not recipes:
        raise HTTPException(status_code=500, detail="No recipes found in data/recipes")
    agg = {}
    for day in payload.plan:
        for meal in day.get('meals', []):
            rid = meal.get('recipe_id')
            if not rid:
                continue
            r = recipes.get(rid)
            if not r:
                continue
            for ing in r.get('ingredients', []):
                raw = ing.get('item') or ''
                qty = ing.get('qty','')
                key = canonicalize(raw)
                grams = qty_to_grams(raw, qty)
                entry = agg.setdefault(key, {'grams':0.0, 'count':0, 'instances':[]})
                if grams:
                    entry['grams'] += grams
                else:
                    entry['count'] += 1
                entry['instances'].append({'recipe_id': rid, 'raw_qty': qty})
    # Format output: prefer grams when available
    out=[]
    for k, v in agg.items():
        out.append({'item': k, 'total_grams': round(v['grams'],2) if v['grams'] else None, 'count': v['count'], 'instances': v['instances']})
    out.sort(key=lambda x: x['item'])
    return {'grocery_list': out}

@app.get('/health')
async def health():
    return {'status':'ok'}