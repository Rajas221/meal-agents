# scripts/build_embeddings.py
import os, json, numpy as np
from sentence_transformers import SentenceTransformer
import faiss

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE, 'data', 'recipes')
OUT_DIR = os.path.join(BASE, 'data')
os.makedirs(OUT_DIR, exist_ok=True)

def load_texts():
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
    ids, texts = [], []
    for f in sorted(files):
        with open(os.path.join(DATA_DIR, f), 'r', encoding='utf-8') as fh:
            r = json.load(fh)
            txt = " ".join([
                r.get('title',''),
                r.get('one_line_summary',''),
                ",".join([i.get('item','') for i in r.get('ingredients',[])]),
                " ".join(r.get('tags',[]))
            ])
            ids.append(r['id'])
            texts.append(txt)
    return ids, texts

def main():
    ids, texts = load_texts()
    if not texts:
        print("No recipes found in data/recipes. Add recipe JSON files and retry.")
        return
    print(f"Encoding {len(texts)} recipes...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embs = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    dim = embs.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embs))
    faiss.write_index(index, os.path.join(OUT_DIR, 'faiss_index.idx'))
    np.save(os.path.join(OUT_DIR, 'emb_ids.npy'), np.array(ids, dtype=object))
    print("Saved data/faiss_index.idx and data/emb_ids.npy")

if __name__ == "__main__":
    main()
