from bs4 import BeautifulSoup
from urllib import quote
import requests
from models.recipes import Recipe
from utils.time import str_to_time

class WebProcessor:
  """
  Parent class for all the webscrapers. Contains all the shared filters needed for BeautifulSoup.
  """
  def __init__(self):
    return

  def has_class(self, tag):
    return tag.has_attr('class')

  def has_href(self, tag):
    return tag.has_attr('href')

  def not_empty(self, tag):
    return tag is not None

  def is_article(self, tag):
    return tag.name == 'article'

  def is_image(self, tag):
    return tag.name == 'img'

  def is_link(self, tag):
    return tag.name == 'a'

  def is_span(self, tag):
    return tag.name == 'span'

  def is_time(self, tag):
    return tag.name == 'time'

  def is_div(self, tag):
    return tag.name == 'div'

  def is_ol(self, tag):
    return tag.name == 'ol'


class AllrecipeProcessor(WebProcessor):
  """
  Processor for Allrecipes. 
  
  Retrieves all the recipes on a given page, as well as the relevant details for a recipe. 
  """
  def __init__(self):
    WebProcessor.__init__(self)
    self.base_search_url = 'http://allrecipes.com/search/results/?wt={query}&sort=re'
    self.recipe_card = ['grid-col--fixed-tiles']
    self.base_recipe_url = 'http://allrecipes.com{recipe_url}'

  def is_recipe_card(self, tag):
    if self.not_empty(tag) and self.is_article(tag) and self.has_class(tag) and tag['class'] == self.recipe_card:
      return 'Recipe by' in tag.text.strip()
    return False

  def is_recipe_image(self, tag):
    return self.not_empty(tag) and self.is_image(tag) and tag.has_attr('data-original-src')

  def is_recipe_link(self, tag):
    return self.not_empty(tag) and self.is_link(tag) and self.has_href(tag) and '/recipe' in tag['href']

  def is_ingredient(self, tag):
    return self.not_empty(tag) and self.is_span(tag) and self.has_class(tag) and 'recipe-ingred_txt' in tag['class'] \
           and len(tag.text) > 0 and 'ingredients' not in tag.text

  def is_description(self, tag):
    return self.not_empty(tag) and self.is_div(tag) and self.has_class(tag) and 'submitter__description' in tag['class']

  def is_prep_time(self, tag):
    return self.not_empty(tag) and self.is_time(tag) and tag.has_attr('itemprop') and 'prepTime' in tag['itemprop']

  def is_cook_time(self, tag):
    return self.not_empty(tag) and self.is_time(tag) and tag.has_attr('itemprop') and 'cookTime' in tag['itemprop']

  def is_total_time(self, tag):
    return self.not_empty(tag) and self.is_time(tag) and tag.has_attr('itemprop') and 'totalTime' in tag['itemprop']

  def is_directions(self, tag):
    return self.not_empty(tag) and self.is_ol(tag) and self.has_class(tag) and 'recipe-directions__list' in tag['class']

  def fetch_recipes(self, query):
    """
    Fetches recipes for a given query.
    
    :param query: string The query
    :return: list of Recipe, partially initialized
    """
    query = quote(query)
    search_url = self.base_search_url.format(query=query)
    r = requests.get(search_url)
    bs = BeautifulSoup(r.text, 'lxml')
    # This is to ensure we get only recipe cards
    # Otherwise, we may get gallery or video cards, neither of which link to recipes
    recipe_cards = bs.find_all(self.is_recipe_card)
    recipes = []
    for recipe in recipe_cards:
      name = recipe.find_all('h3')[0].text.strip()

      # Each recipe may not have a photo attached to it,
      # So we check to make sure that the photo is not Allrecipes' default recipe photo
      image_url = recipe.find_all(self.is_recipe_image)[0]['data-original-src']
      if 'userphotos' not in image_url:
        image_url = None
      recipe_url = self.base_recipe_url.format(recipe_url=recipe.find_all(self.is_recipe_link)[0]['href'])
      recipes.append(Recipe(name, recipe_url, image_url, []))
    return recipes

  def fetch_recipe(self, recipe):
    """
    Fetches the recipe details for a given recipe.
    
    :param recipe:  Recipe a partially initialized Recipe object 
    :return: Recipe a fully fleshed out Recipe object
    """
    r = requests.get(recipe.source_url)
    bs = BeautifulSoup(r.text, 'lxml')

    ingredients = bs.find_all(self.is_ingredient)
    recipe.ingredients = [i.text for i in ingredients]
    recipe.description = bs.find_all(self.is_description)[0].text.strip()

    # Prep time, cook time, and total time may not be defined for a recipe
    # When this happens, we want to make sure that the default values are
    # inserted and that the program does not crash
    try:
      recipe.prep_time = str_to_time(bs.find_all(self.is_prep_time)[0].text)
    except IndexError:
      recipe.prep_time = 0

    try:
      recipe.cook_time = str_to_time(bs.find_all(self.is_cook_time)[0].text)
    except IndexError:
      recipe.cook_time = 0

    try:
      recipe.total_time = str_to_time(bs.find_all(self.is_total_time)[0].text)
    except IndexError:
      recipe.total_time = 0

    directions = bs.find_all(self.is_directions)[0]
    recipe.directions = u'\n'.join([i.text for i in directions.find_all('li')])
    return recipe


