import json, os, random, datetime

REGIONS = {
    "North": ["Paneer Butter Masala", "Rajma Chawal", "Aloo Paratha", "Dal Makhani", "Chole Bhature", "Kadhi Pakora", "Baingan Bharta"],
    "South": ["Masala Dosa", "Idli Sambar", "Pesarattu", "Curd Rice", "Upma", "Lemon Rice", "Vegetable Kurma"],
    "East": ["Fish Curry", "Aloo Posto", "Litti Chokha", "Macher Jhol", "Ghugni", "Chhena Poda"],
    "West": ["Vada Pav", "Thepla", "Undhiyu", "Misal Pav", "Dal Dhokli", "Goan Fish Curry"]
}

DIETS = {
    "veg": ["paneer", "potato", "tomato", "onion", "rice", "dal"],
    "nonveg": ["chicken", "fish", "egg", "mutton"],
    "vegan": ["tofu", "vegetables", "lentils", "rice"],
    "eggetarian": ["egg", "onion", "tomato"]
}

ING_TEMPLATE = [
    ("salt", "1 tsp"),
    ("oil", "1 tbsp"),
    ("onion", "1/2 cup"),
]

def create_recipe(rid, title, region, diet):
    base_ing = ING_TEMPLATE.copy()
    
    # add 1–2 diet-specific ingredients
    diet_choices = random.sample(DIETS[diet], k=2)
    for d in diet_choices:
        base_ing.append((d, random.choice(["1 cup", "1/2 cup", "1 tbsp"])))

    ingredients = [{"item": i, "qty": q} for i, q in base_ing]

    recipe = {
        "id": f"r{rid:03d}",
        "title": title,
        "region": region,
        "diet": diet,
        "tags": ["indian", region.lower(), diet],
        "cook_time_min": random.choice([15, 20, 25, 30, 40]),
        "servings": 2,
        "spice_level": random.choice(["low", "medium", "high"]),
        "ingredients": ingredients,
        "steps": ["Prep ingredients", "Cook on medium flame", "Serve hot"],
        "one_line_summary": f"{title} — classic {region} Indian dish.",
        "source_url": "synthesized",
        "license": "synthesized",
        "curation_status": "synthesized",
        "created_at": datetime.datetime.utcnow().isoformat()
    }

    return recipe


def main():
    out_dir = "data/recipes"
    os.makedirs(out_dir, exist_ok=True)

    rid = 50  # start after existing recipes
    all_recipes = []

    for region, titles in REGIONS.items():
        for title in titles:
            for diet in DIETS.keys():
                if len(all_recipes) >= 50:
                    break
                recipe = create_recipe(rid, title, region, diet)
                out_path = os.path.join(out_dir, f"r{rid:03d}.json")
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(recipe, f, indent=2)
                rid += 1
                all_recipes.append(recipe)

    print(f"Generated {len(all_recipes)} recipes into data/recipes/")

if __name__ == "__main__":
    main()
