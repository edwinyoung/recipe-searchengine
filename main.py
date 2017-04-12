import time
from utils.webscraper.allrecipe import AllrecipeWebscraper
from utils.webscraper.bigoven import BigOvenWebscraper
from utils.webscraper.epicurious import EpicuriousWebscraper

if __name__ == '__main__':
  ar_webscraper = AllrecipeWebscraper()
  bo_webscraper = BigOvenWebscraper()
  ep_webscraper = EpicuriousWebscraper()

  ar_webscraper.has_additional_results = True
  bo_webscraper.has_additional_results = True
  ep_webscraper.has_additional_results = True

  processed_recipes, ar_recipes, bo_recipes, ep_recipes = [], [], [], []

  for i in range(1, 6):
    last_timer = time.time()

    if ar_webscraper.has_additional_results:
      ar_recipes = ar_webscraper.fetch_recipes('beef tenderloin', i)

    if bo_webscraper.has_additional_results:
      bo_recipes = bo_webscraper.fetch_recipes('beef tenderloin', i)

    if ep_webscraper.has_additional_results:
      ep_recipes = ep_webscraper.fetch_recipes('beef tenderloin', i)

    print 'Processing', len(ar_recipes) + len(bo_recipes) + len(ep_recipes), 'recipes...'
    while len(ar_recipes) + len(bo_recipes) + len(ep_recipes) > 0:
      if time.time() - last_timer < 5:
        continue
      last_timer = time.time()

      if len(ar_recipes) > 0:
        processed_recipes.append(ar_webscraper.fetch_recipe(ar_recipes.pop(0)))
        print len(processed_recipes), '|', processed_recipes[-1]

      if len(bo_recipes) > 0:
        processed_recipes.append(bo_webscraper.fetch_recipe(bo_recipes.pop(0)))
        print len(processed_recipes), '|', processed_recipes[-1]

      if len(ep_recipes) > 0:
        processed_recipes.append(ep_webscraper.fetch_recipe(ep_recipes.pop(0)))
        print len(processed_recipes), '|', processed_recipes[-1]
