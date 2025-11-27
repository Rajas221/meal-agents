from fastapi import FastAPI
from pydantic import BaseModel
import json, os, numpy as np
from sentence_transformers import SentenceTransformer
import faiss

app = FastAPI(title="RecipeAgent (FAISS)")

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
DATA_DIR = os.path.join(BASE, 'data', 'recipes')
INDEX_PATH = os.path.join(BASE, 'data', 'faiss_index.idx')
IDS_PATH = os.path.join(BASE, 'data', 'emb_ids.npy')

MODEL = None
INDEX = None
IDS = None

def ensure_resources():
    global MODEL, INDEX, IDS
    if MODEL is None:
        MODEL = SentenceTransformer('all-MiniLM-L6-v2')
    if INDEX is None:
        if not os.path.exists(INDEX_PATH) or not os.path.exists(IDS_PATH):
            raise RuntimeError("FAISS index or ids not found. Run scripts/build_embeddings.py")
        INDEX = faiss.read_index(INDEX_PATH)
        IDS = list(np.load(IDS_PATH, allow_pickle=True))
    return MODEL, INDEX, IDS

def load_recipe_by_id(rid):
    f = os.path.join(DATA_DIR, f"{rid}.json")
    if os.path.exists(f):
        with open(f,'r',encoding='utf-8') as fh:
            return json.load(fh)
    # fallback scan
    for fname in os.listdir(DATA_DIR):
        if fname.endswith('.json'):
            with open(os.path.join(DATA_DIR,fname),'r',encoding='utf-8') as fh:
                r = json.load(fh)
                if r.get('id') == rid:
                    return r
    return None

class RecipeQuery(BaseModel):
    query: str
    k: int = 5
    filters: dict = {}

@app.post('/a2a/get_recipes')
async def get_recipes(q: RecipeQuery):
    try:
        model, index, ids = ensure_resources()
    except Exception:
        return {'recipes': []}

    emb = model.encode([q.query], convert_to_numpy=True)
    D, I = index.search(emb, q.k*2)  # fetch extra candidates for fallback
    raw_candidates = []
    for idx in I[0]:
        if idx < 0 or idx >= len(ids): continue
        rid = ids[idx]
        r = load_recipe_by_id(rid)
        if r:
            raw_candidates.append(r)

    # first apply metadata filters (preserve behavior)
    filtered = []
    for r in raw_candidates:
        diet = q.filters.get('diet')
        region = q.filters.get('region')
        ok = True
        if diet and r.get('diet') and diet.lower() != r.get('diet').lower():
            ok = False
        if region and r.get('region') and region.lower() != r.get('region').lower():
            ok = False
        if ok:
            filtered.append(r)
        if len(filtered) >= q.k:
            break

    # SAFE FALLBACK: if filters removed all candidates, return top-k raw candidates instead
    if not filtered:
        # pick up to k unique raw candidates
        seen = set()
        fallback = []
        for c in raw_candidates:
            rid = c.get('id')
            if not rid or rid in seen: continue
            fallback.append(c)
            seen.add(rid)
            if len(fallback) >= q.k: break
        return {'recipes': fallback}

    return {'recipes': filtered}

@app.get('/health')
async def health():
    return {'status': 'ok'}