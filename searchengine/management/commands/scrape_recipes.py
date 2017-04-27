# encoding=utf8
import time

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

    start_time = previous_time = time.time()

    # We want to cap the total number of results for an initial run,
    # particularly if only one of our sources is returning results
    #
    # Worst case scenario, given 20 unique results/query from a single source,
    # this will take about 35(!) minutes with our self-imposed rate limit of 1 request/5 seconds
    max_results = 400
    counter = 0  # Keeps track of the total number of unique recipes we have for our query

    for ingredient in ingredients:
      self.stdout.write(u'Scraping for recipes containing "{0}"...'.format(ingredient.display_name))
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
             ep_scraper.has_additional_results) and counter < max_results:

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
        counter += recipe_count
        if recipe_count > 0:
          self.stdout.write(u'Retrieving {0} recipes...'.format(recipe_count))
        else:
          self.stdout.write(u'No new recipes found; continuing search.')
          continue

        # Reset request timer at the end to ensure we have a minimum of 5s between requests
        # Doing it immediately after the time check would include time required to process each page,
        # which doesn't accurately reflect when the actual request was issued
        previous_time = time.time()

        while ar_recipes or bo_recipes or ep_recipes:
          if time.time() - previous_time < 5:
            time.sleep(2)
            continue

          if ar_recipes:
            recipe = ar_recipes.pop()
            self.stdout.write(u'AR | ' + unicode(recipe['name']))
            ar_scraper.fetch_recipe(recipe)

          if bo_recipes:
            recipe = bo_recipes.pop()
            self.stdout.write(u'BO | ' + unicode(recipe['name']))
            bo_scraper.fetch_recipe(recipe)

          if ep_recipes:
            recipe = ep_recipes.pop()
            self.stdout.write(u'EP | ' + unicode(recipe['name']))
            ep_scraper.fetch_recipe(recipe)

          previous_time = time.time()

        if recipe_count > 0:
          self.stdout.write(u'\n')
