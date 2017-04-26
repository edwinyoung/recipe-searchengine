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

    previous_time = time.time()
    print 'Got timed!'

    for ingredient in ingredients:
      print ingredient.display_name
      self.stdout.write(u'Ingredient search: {0}...'.format(ingredient.display_name))
      # Resetting this on every loop so that we can have what is effectively a do while loop
      ar_scraper.has_additional_results = True
      bo_scraper.has_additional_results = True
      ep_scraper.has_additional_results = True

      # Also reset the contents of our results cache
      ar_recipes = bo_recipes = ep_recipes = []

      # Initialize search page counter
      page = 0
      while ar_scraper.has_additional_results or bo_scraper.has_additional_results or ep_scraper.has_additional_results:

        # Artificially rate-limit our queries so we don't trip DDoS protections and get null-routed
        # Or worse, have Amazon pull the plug on our AWS instance and threaten to close our AWS account
        if time.time() - previous_time < 5:
          time.sleep(2)
          continue

        # Increment on each pass through
        page += 1
        previous_time = time.time()

        if ar_scraper.has_additional_results:
          ar_recipes = ar_scraper.fetch_recipes(ingredient.display_name, page=page)

        if bo_scraper.has_additional_results:
          bo_recipes = bo_scraper.fetch_recipes(ingredient.display_name, page=page)

        if ep_scraper.has_additional_results:
          ep_recipes = ep_scraper.fetch_recipes(ingredient.display_name, page=page)

        while ar_recipes or bo_recipes or ep_recipes:
          if time.time() - previous_time < 5:
            time.sleep(2)
            continue

          if ar_recipes:
            ar_scraper.fetch_recipe(ar_recipes.pop())

          if bo_recipes:
            bo_scraper.fetch_recipe(bo_recipes.pop())

          if ep_recipes:
            ep_scraper.fetch_recipe(ep_recipes.pop())
