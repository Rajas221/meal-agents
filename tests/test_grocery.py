from agents.grocery_agent.app import aggregate_ingredients_from_plan, normalize_ingredient_name

def test_normalize():
    assert normalize_ingredient_name(' raw rice ') == 'rice'
    assert normalize_ingredient_name('MUNG DAL') == 'moong dal'

def test_aggregate_simple(tmp_path, monkeypatch):
    # create a temporary recipe and point DATA_DIR to tmp_path/data/recipes
    recipes = {
        'r001': {
            'id': 'r001',
            'ingredients': [{'item': 'Rice', 'qty': '1 cup'}, {'item': 'Moong Dal', 'qty': '1/2 cup'}]
        },
        'r002': {
            'id': 'r002',
            'ingredients': [{'item': 'Rice', 'qty': '2 cups'}]
        }
    }
    plan = [{'day': 1, 'meals': [{'meal_name': 'lunch', 'recipe_id': 'r001'}, {'meal_name': 'dinner', 'recipe_id': 'r002'}]}]
    agg = aggregate_ingredients_from_plan(plan, recipes)
    assert agg['rice']['count'] == 2
    assert agg['moong dal']['count'] == 1
