from bs4 import BeautifulSoup
from urllib import quote
import requests
from models.recipes import Recipe
from utils.time import str_to_time
from utils.webscraper.webscraper import Webscraper

class BigOvenWebscraper(Webscraper):

  def __init__(self):
    Webscraper.__init__(self)
    self.base_search_url = 'http://www.bigoven.com/recipes/{query}/best/page/{page}'
    self.recipe_card = 'panel-body'

  def is_recipe_card(self, tag):
    return self.not_empty(tag) and self.is_div(tag) and self.has_class(tag, self.recipe_card)

  def is_recipe_image(self, tag):
    return self.not_empty(tag) and self.is_image(tag) and self.has_class(tag, 'recipe-img')

  def is_recipe_link(self, tag):
    return self.not_empty(tag) and self.is_link(tag) and self.has_href(tag) and '/recipe' in tag['href']

  def is_recipe_name(self, tag):
    return self.not_empty(tag) and self.is_li(tag) and self.has_class(tag, 'list-group-recipetile-1')

  def is_total_time(self, tag):
    return self.not_empty(tag) and self.is_time(tag) and tag.has_attr('title')

  def is_ingredient(self, tag):
    return self.not_empty(tag) and self.is_span(tag) and self.has_class(tag, 'ingredient')

  def is_directions_container(self, tag):
    return self.not_empty(tag) and self.is_div(tag) and self.has_class(tag, 'display-field')

  def is_directions(self, tag):
    return self.not_empty(tag) and self.is_div(tag) and tag.has_attr('id') and tag['id'] == 'instr'

  def fetch_recipes(self, query, page=1):
    """
    Fetches recipes for a given query.

    :param query: string The query
    :param page: int indicating which page of search results
    :return: list of Recipe, partially initialized
    """
    query = quote(query)
    search_url = self.base_search_url.format(query=query, page=page)
    r = requests.get(search_url)
    if r.status_code is not 200:
      self.has_additional_results = False
      return []

    bs = BeautifulSoup(r.text, 'lxml')
    recipe_cards = bs.find_all(self.is_recipe_card)
    recipes = []
    for recipe in recipe_cards:
      name = recipe.find_all(self.is_recipe_name)[0].text.strip()
      image_url = recipe.find_all(self.is_recipe_image)[0]['src']
      recipe_url = recipe.find_all(self.is_recipe_link)[0]['href']
      recipes.append(Recipe(name, recipe_url, image_url, []))
    self.has_additional_results = len(recipes) > 0
    return recipes

  def fetch_recipe(self, recipe):
    """
    Fetches the recipe details for a given recipe.

    :param recipe:  Recipe a partially initialized Recipe object 
    :return: Recipe a fully fleshed out Recipe object
    """
    r = requests.get(recipe.source_url)
    if r.status_code is not 200:
      return recipe

    bs = BeautifulSoup(r.text, 'lxml')

    # BigOven just makes this unnecessarily difficult to extract ingredients from a recipe
    # They place it in a <table> instead of a <ul> like a sane web dev
    ingredient_table = bs.find_all('table')[0]
    ingredients = [i.text.strip() for i in ingredient_table.find_all(self.is_ingredient)]

    # This has to be done to get rid of in-line line feeds
    # HTML doesn't give a fuck about whitespace, so this isn't immediately apparent
    # BeautifulSoup, unfortunately, *does* give a fuck about this shit
    temp_ingredients = []
    for i in ingredients:
      temp_ingredients.append(u' '.join([j for j in i.split() if len(j) > 0]))
    recipe.ingredients = temp_ingredients

    # BigOven never provides a recipe blurb/description, hence this boilerplate value
    recipe.description = 'No recipe description provided.'

    # Total time may not be defined for a recipe
    # When this happens, we want to make sure that the default values are
    # inserted and that the program does not crash

    try:
      recipe.total_time = str_to_time(bs.find_all(self.is_total_time)[0]['title'][2:])
    except IndexError:
      recipe.total_time = -1

    # BigOven doesn't make it immediately clear if it's their own data or hosted on a 3rd party food blog
    # So I have to do this - get the directions container and see if it's BigOven's own data and not scraped data
    directions_container = bs.find_all(self.is_directions_container)[0]
    directions = directions_container.find_all(self.is_directions)

    # 3rd-party hosted recipes start with 'Original recipe: http://some.food.blog/...'
    # Funnily enough, the 'http://some.food.blog/...' is the shorthand print of 'http://some.food.blog/insert-recipe-url'
    # So if I hit it, I have to show that 1) I can't scrape the blog, and 2) that the directions are at a new source url
    if len(directions) < 1:
      directions = ['No directions found.']
      links = directions_container.find_all('a')
      for link in links:
        if link.text.strip().replace('...', '') in link['href']:
          recipe.source_url = link['href']

    # Otherwise, BigOven will serve me the directions as a series of <p> tags
    else:
      directions = [i.text.strip() for i in directions_container.find_all(self.is_directions)[0].find_all('p')]

    recipe.directions = u'\n'.join(directions)
    return recipe
