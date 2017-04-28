# encoding=utf8
import os
import time
import codecs

from django.conf import settings
from django.core.management.base import BaseCommand

from searchengine.models import Ingredient
from searchengine.utils.scraper.allrecipe import AllrecipeWebscraper
from searchengine.utils.scraper.bigoven import BigOvenWebscraper
from searchengine.utils.scraper.epicurious import EpicuriousWebscraper


class Command(BaseCommand):
  help = 'Closes the specified poll for voting'

  def handle(self, *args, **options):
    ar_scraper = AllrecipeWebscraper()
    bo_scraper = BigOvenWebscraper()
    ep_scraper = EpicuriousWebscraper()

    ingredients = Ingredient.objects.all()

    # Import ingredients if we don't already have an ingredients list
    # Format of ingredients is "display name,stemmed/search name"
    if len(ingredients) < 1:
      with codecs.open(os.path.join(settings.BASE_DIR, 'searchengine/data/ingredients.txt'),
                       'r', 'utf-8') as ingredients_file:
        ingredients = map(unicode.strip, ingredients_file.readlines())
        ingredients = [i.split(u',') for i in ingredients if len(i) > 0]
      ingredients = [Ingredient.objects.create(display_name=i[0], search_name=i[1]) for i in ingredients
                     if len(i) >= 2 and isinstance(i, list)]

    # Check to make sure that we don't have any ingredients in
    # our ingredient list that we already completed our queries for
    completed_ingredients_filename = os.path.join(settings.BASE_DIR, 'searchengine/data/completed-ingredients.txt')
    if os.path.isfile(completed_ingredients_filename):
      with codecs.open(completed_ingredients_filename, 'r', 'utf-8') as completed_ingredients_file:
        ingredient_names = [i for i in map(unicode.strip, completed_ingredients_file.readlines()) if len(i) > 0]
      ingredients = [i for i in ingredients if i.search_name not in ingredient_names]

    # Setup our logfile and our initial timer
    previous_time = time.time()
    logfile_name = os.path.join(settings.BASE_DIR, time.strftime('searchengine/data/%Y%m%d-%H%M%S-scraping.log'))

    # We want to cap the total number of results for an initial run,
    # particularly if only one of our sources is returning results
    #
    # Worst case scenario, given 20 unique results/query from a single source,
    # this will take about 14 minutes with our self-imposed rate limit of 1 request/5 seconds
    max_recipe_requests = 150

    with codecs.open(logfile_name, 'w', 'utf-8') as logfile:
      for ingredient in ingredients:
        counter = 0  # Keeps track of the total number of unique recipes we have for our query

        logfile.write(u'Scraping for recipes containing "{0}"...\n'.format(ingredient.display_name))
        # Resetting this on every loop so that we can have what is effectively a do while loop
        ar_scraper.has_additional_results = True
        bo_scraper.has_additional_results = True
        ep_scraper.has_additional_results = True

        # Also reset the contents of our results cache
        ar_recipes = bo_recipes = ep_recipes = []

        # Initialize search page counter
        page = 0
        while (ar_scraper.has_additional_results or
               bo_scraper.has_additional_results or
               ep_scraper.has_additional_results) and counter < max_recipe_requests:

          # Artificially rate-limit our queries so we don't trip DDoS protections and get null-routed
          # Or worse, have Amazon pull the plug on our AWS instance and threaten to close our AWS account
          if time.time() - previous_time < 5:
            time.sleep(2)
            continue

          # Increment on each pass through
          page += 1

          if ar_scraper.has_additional_results:
            ar_recipes = ar_scraper.fetch_recipes(ingredient.display_name, page=page)

          if bo_scraper.has_additional_results:
            bo_recipes = bo_scraper.fetch_recipes(ingredient.display_name, page=page)

          if ep_scraper.has_additional_results:
            ep_recipes = ep_scraper.fetch_recipes(ingredient.display_name, page=page)

          recipe_count = len(ar_recipes + bo_recipes + ep_recipes)
          if recipe_count > 0:
            logfile.write(u'Retrieving {0} recipes...\n'.format(recipe_count))
          else:
            logfile.write(u'No new recipes found; continuing search.\n')
            continue

          # Reset request timer at the end to ensure we have a minimum of 5s between requests
          # Doing it immediately after the time check would include time required to process each page,
          # which doesn't accurately reflect when the actual request was issued
          previous_time = time.time()

          while ar_recipes or bo_recipes or ep_recipes and counter <= max_recipe_requests:
            if time.time() - previous_time < 5:
              time.sleep(2)
              continue

            if ar_recipes:
              recipe = ar_recipes.pop()
              logfile.write(u'AR | {0}\n'.format(unicode(recipe['name'])))
              ar_scraper.fetch_recipe(recipe)

            if bo_recipes:
              recipe = bo_recipes.pop()
              logfile.write(u'BO | {0}\n'.format(unicode(recipe['name'])))
              bo_scraper.fetch_recipe(recipe)

            if ep_recipes:
              recipe = ep_recipes.pop()
              logfile.write(u'EP | {0}\n'.format(unicode(recipe['name'])))
              ep_scraper.fetch_recipe(recipe)

            previous_time = time.time()
            counter += 1

          if recipe_count > 0:
            logfile.write(u'\n')

        # Finally, write the search value of the ingredient to our completed ingredients file
        try:
          with codecs.open(completed_ingredients_filename, 'a', 'utf-8') as completed_ingredients_file:
            completed_ingredients_file.write(u'{0}\n'.format(ingredient.search_name))
        except IOError:
          with codecs.open(completed_ingredients_filename, 'w', 'utf-8') as completed_ingredients_file:
            completed_ingredients_file.write(u'{0}\n'.format(ingredient.search_name))
