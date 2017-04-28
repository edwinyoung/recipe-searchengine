import requests
from urllib import quote
from bs4 import BeautifulSoup
from titlecase import titlecase

from searchengine.utils.scraper.webscraper import Webscraper
from searchengine.models import Ingredient, Recipe


class EpicuriousWebscraper(Webscraper):

  def __init__(self):
    Webscraper.__init__(self)
    self.base_search_url = 'http://www.epicurious.com/search/{query}?page={page}'
    self.base_recipe_url = 'http://www.epicurious.com{recipe_url}'
    self.recipe_card = 'recipe-content-card'

  def is_recipe_card(self, tag):
    return self.not_empty(tag) and self.is_article(tag) and self.has_class(tag, self.recipe_card)

  def is_recipe_description(self, tag):
    return self.not_empty(tag) and self.is_p(tag) and self.has_class(tag, 'dek')

  def is_ingredient(self, tag):
    return self.not_empty(tag) and self.is_li(tag) and self.has_class(tag, 'ingredient')

  def is_directions(self, tag):
    return self.not_empty(tag) and self.is_li(tag) and self.has_class(tag, 'preparation-step')

  def fetch_recipes(self, query, page=1):
    """
    Fetches recipes for a given query.

    :param query: string The query
    :param page: int indicating which page of search results
    :return: list of Recipe, partially initialized
    """
    if page == 1:
      self.has_additional_results = True
    query = quote(query)
    search_url = self.base_search_url.format(query=query, page=page)
    r = requests.get(search_url, headers=self.request_headers)
    if r.status_code is not 200:
      self.has_additional_results = False
      return []

    bs = BeautifulSoup(r.text, 'lxml')

    # This is to ensure we get only recipe cards
    # Otherwise, we may get article or video cards, neither of which link to recipes
    recipe_cards = bs.find_all(self.is_recipe_card)
    recipes = []
    for recipe in recipe_cards:
      name_tag = recipe.find_all('h4')[0]
      name = name_tag.text.strip()
      recipe_url = self.base_recipe_url.format(recipe_url=name_tag.find_all('a')[0]['href'])

      temp_recipe = {
        'name': titlecase(name),
        'source_url': recipe_url
      }

      # Epicurious has recipe descriptions in the HTML that is usually hidden to humans by CSS
      # This is a webscraper, though, so it doesn't care that it's visually hidden to the end user
      # Still not guaranteed to have a description all the time, so I'm saving it here
      recipe_description = recipe.find_all(self.is_recipe_description)
      if len(recipe_description) > 0:
        temp_recipe['description'] = recipe_description[0].text.strip()

      recipes.append(temp_recipe)

    self.has_additional_results = len(recipes) > 0

    source_urls = [r['source_url'] for r in recipes]
    source_urls = [r.source_url for r in Recipe.objects.filter(source_url__in=source_urls)]
    recipes = [r for r in recipes if r['source_url'] not in source_urls]

    return recipes

  def fetch_recipe(self, recipe):
    """
    Fetches the recipe details for a given recipe.

    :param recipe:  Recipe a partially initialized Recipe object 
    :return: Recipe a fully fleshed out Recipe object
    """
    if Recipe.objects.filter(source_url__iexact=recipe['source_url']):
      return

    r = requests.get(recipe['source_url'], headers=self.request_headers)
    if r.status_code is not 200:
      return recipe
    bs = BeautifulSoup(r.text, 'lxml')

    ingredients = [i.text.strip() for i in bs.find_all(self.is_ingredient)]

    # We'll want to extract the ids of the ingredients hidden in the ingredient string which usually
    # also contains the measurements and sometimes preparation instructions (like 'onions, chopped')
    ingredient_ids = [self.text_processor.match_ingredient(i) for i in ingredients if i is not None]
    ingredients = [Ingredient.objects.get(pk=i) for i in ingredient_ids if i is not None]

    # Epicurious does not provide prep time, cook time, or total time, so we won't be changing those values

    directions = bs.find_all(self.is_directions)
    if len(directions) < 1:
      directions = ['No directions found.']
    else:
      directions = [i.text.strip() for i in bs.find_all(self.is_directions)[0].find_all('p')]

    recipe['directions'] = u'\n'.join(directions)

    r = Recipe.objects.create(**recipe)
    if len(ingredients) > 0:
      for i in ingredients:
        r.ingredients.add(i)

    self.index_directions(r)

    return r
