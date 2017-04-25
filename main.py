import time
from utils.webscraper.allrecipe import AllrecipeWebscraper
from utils.webscraper.bigoven import BigOvenWebscraper
from utils.webscraper.epicurious import EpicuriousWebscraper
from utils.database import DB_CONN_WEBSCRAPER

if __name__ == '__main__':
  ar_webscraper = AllrecipeWebscraper()
  bo_webscraper = BigOvenWebscraper()
  ep_webscraper = EpicuriousWebscraper()

  ar_webscraper.has_additional_results = True
  bo_webscraper.has_additional_results = True
  ep_webscraper.has_additional_results = True

  processed_recipes, ar_recipes, bo_recipes, ep_recipes = [], [], [], []
  recipe_urls, image_urls = [], []
  i = 0
  ingredient_tokens = []

  while (ar_webscraper.has_additional_results or bo_webscraper.has_additional_results \
      or ep_webscraper.has_additional_results) and len(processed_recipes) < 40:
    i += 1
    last_timer = time.time()

    if ar_webscraper.has_additional_results:
      ar_recipes = ar_webscraper.fetch_recipes('chicken provencal', i)

    if bo_webscraper.has_additional_results:
      bo_recipes = bo_webscraper.fetch_recipes('chicken provencal', i)

    if ep_webscraper.has_additional_results:
      ep_recipes = ep_webscraper.fetch_recipes('chicken provencal', i)

    print 'Processing', len(ar_recipes) + len(bo_recipes) + len(ep_recipes), 'recipes...'
    while len(ar_recipes) + len(bo_recipes) + len(ep_recipes) > 0 and len(processed_recipes) < 40:
      if time.time() - last_timer < 5:
        continue
      last_timer = time.time()

      if len(ar_recipes) > 0:
        processed_recipes.append(ar_webscraper.fetch_recipe(ar_recipes.pop(0)))
        recipe = processed_recipes[-1]
        recipe_urls.append(len(recipe.source_url))
        if recipe.image_url is not None:
          image_urls.append(len(recipe.image_url))
        print len(processed_recipes), '|', processed_recipes[-1]
        for ingredient in recipe.ingredients:
          ingredient_tokens += ingredient.split()

      if len(bo_recipes) > 0:
        processed_recipes.append(bo_webscraper.fetch_recipe(bo_recipes.pop(0)))
        recipe = processed_recipes[-1]
        recipe_urls.append(len(recipe.source_url))
        if recipe.image_url is not None:
          image_urls.append(len(recipe.image_url))
        print len(processed_recipes), '|', processed_recipes[-1]
        for ingredient in recipe.ingredients:
          ingredient_tokens += ingredient.split()

      if len(ep_recipes) > 0:
        processed_recipes.append(ep_webscraper.fetch_recipe(ep_recipes.pop(0)))
        recipe = processed_recipes[-1]
        recipe_urls.append(len(recipe.source_url))
        if recipe.image_url is not None:
          image_urls.append(len(recipe.image_url))
        print len(processed_recipes), '|', processed_recipes[-1]
        for ingredient in recipe.ingredients:
          ingredient_tokens += ingredient.split()

  print max(recipe_urls), max(image_urls)
