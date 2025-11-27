import re, csv, os

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
MAPPING = {}

def load_mapping():
    global MAPPING
    if MAPPING:
        return MAPPING
    path = os.path.join(BASE, 'data', 'ingredient_mappings.csv')
    if not os.path.exists(path):
        return {}
    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            key = r['canonical_name'].strip().lower()
            MAPPING[key] = {
                'aliases': [a.strip().lower() for a in r['aliases'].split(';') if a.strip()],
                'grams_per_cup': float(r.get('grams_per_cup') or 0),
                'grams_per_tbsp': float(r.get('grams_per_tbsp') or 0),
                'grams_per_tsp': float(r.get('grams_per_tsp') or 0)
            }
    return MAPPING

def canonicalize(name):
    if not name: return name
    n = name.strip().lower()
    mp = load_mapping()
    # exact match
    if n in mp:
        return n
    # alias match
    for key, val in mp.items():
        if any(alias == n for alias in val['aliases']):
            return key
    # fallback: return raw lowercased
    return n

_qty_re = re.compile(r'(?P<num>[\d./]+)\s*(?P<unit>cup|cups|tbsp|tablespoon|tablespoons|tsp|teaspoon|teaspoons)?', re.I)

def qty_to_grams(item_name, qty_str):
    """
    Parse simple quantities like:
      '1 cup', '1/2 cup', '2 tbsp', '1 tsp'
    Returns approximate grams (float) or None if parsing failed.
    """
    if not qty_str: return None
    m = _qty_re.search(qty_str)
    if not m:
        return None
    num = m.group('num')
    unit = (m.group('unit') or '').lower()
    # convert fraction like '1/2' to float
    try:
        if '/' in num:
            a,b = num.split('/')
            value = float(a)/float(b)
        else:
            value = float(num)
    except:
        return None
    key = canonicalize(item_name)
    mp = load_mapping().get(key)
    if not mp:
        return None
    if unit.startswith('cup'):
        g = mp.get('grams_per_cup') * value
    elif unit.startswith('tbsp') or unit in ('tablespoon','tablespoons'):
        g = mp.get('grams_per_tbsp') * value
    elif unit.startswith('tsp') or unit in ('teaspoon','teaspoons'):
        g = mp.get('grams_per_tsp') * value
    else:
        # if no unit given, treat number as 'count' not grams
        return None
    return g