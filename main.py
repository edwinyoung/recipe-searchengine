import time
from utils.webscraper.processor import AllrecipeProcessor

if __name__ == '__main__':
  last_timer = time.time()
  ar_processor = AllrecipeProcessor()
  recipes = ar_processor.fetch_recipes('chicken drumsticks')
  processed_recipes = []
  while len(recipes) > 0:
    if time.time() - last_timer < 10:
      continue
    last_timer = time.time()
    processed_recipes.append(ar_processor.fetch_recipe(recipes.pop(0)))
  print processed_recipes
