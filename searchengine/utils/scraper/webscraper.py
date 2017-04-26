from searchengine.utils.text.processor import TextProcessor
from searchengine.models import Ingredient, DirectionsFulltextIndex, DirectionsIndex
from operator import itemgetter

class Webscraper:
  """
  Parent class for all the webscrapers. Contains all the shared filters needed for BeautifulSoup.
  """
  def __init__(self):
    self.has_additional_results = True

  def has_class(self, tag, class_name=None):
    if class_name is None:
      return tag.has_attr('class')
    else:
      return tag.has_attr('class') and class_name in tag['class']

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

  def is_li(self, tag):
    return tag.name == 'li'

  def is_h4(self, tag):
    return tag.name == 'h4'

  def is_p(self, tag):
    return tag.name == 'p'

  def match_ingredient(self, ingredient_string):
    """
    Attempts to find the id of the ingredient whose name most closely matches the ingredient listed for a recipe.
    
    :param ingredient_string: unicode String with measurement and preparation instructions
    :return: int/None ID of the most relevant ingredient in the database, or None if not found
    """
    if ingredient_string is None:
      return None
    processor = TextProcessor()
    stemmed_target_tokens = processor.stem_document(ingredient_string)

    # Our version of a do-while loop
    token = stemmed_target_tokens[0]
    queryset = Ingredient.objects.filter(search_name__icontains=token)

    # Have to check that the target ingredient wasn't a single word so we don't get an IndexError
    if len(stemmed_target_tokens) > 1:
      for token in stemmed_target_tokens[1:]:
        queryset = (queryset | Ingredient.objects.filter(search_name__icontains=token)).distinct()

    # Sort by the ingredients that have the highest similarity first, then by which ingredient is the longer
    # Let's say our ingredient string is '1/4 cup chopped celery root'
    # We'll get all ingredients with '1', '4', 'cup', 'chop', 'celeri', 'root' in them after stemming
    #     (Sample: 'buttercup squash', 'chop carrot', 'chop onion', 'celeri root', 'celeri root leav', 'root veggi')
    #
    # If we counted by tokens that match, we'd see the following:
    #     'buttercup squash': 0
    #     'chop carrot': 1
    #     'chop onion': 1
    #     'celeri root': 2
    #     'celeri root leav': 2
    #     'root veggi': 1
    #
    # So obviously we need to find another heuristic than just the number of tokens from the ingredients model that
    # match the target ingredient string passed into the function. Since we don't want overly long strings that obscure
    # our fitting algorithm, we can use the % match instead as a heuristic to get the following:
    #     'buttercup squash': 0.0000
    #     'chop carrot': 0.5000
    #     'chop onion': 0.5000
    #     'celeri root': 1.0000
    #     'celeri root leav': 0.6667
    #     'root veggi': 0.5000
    #
    # Which now gives us the desired ingredient. In the event that two or more ingredients have the same percentage
    # of matching tokens, the longest ingredient string will be chosen, as it is assumed that it will be the most
    # specific and descriptive of the target tokens.

    search_dictionaries = []
    for ingredient in queryset:
      dictionary = {'id': ingredient.id}
      stemmed_search_tokens = processor.stem_document(ingredient.search_name)
      found = [i for i in stemmed_search_tokens if i in stemmed_target_tokens]
      dictionary['similarity'] = len(found) / float(len(stemmed_search_tokens))
      dictionary['len'] = len(stemmed_search_tokens)
      search_dictionaries.append(dictionary)

    if len(search_dictionaries) < 1:
      return None

    search_dictionaries = sorted(search_dictionaries, key=itemgetter('similarity', 'len'), reverse=True)
    return search_dictionaries[0]['id']

  def index_directions(self, recipe):
    """
    Indexes the recipe instructions, both with and without stopwords, if available.
    
    :param recipe: searchengine.models.Recipe Recipe object/model with directions
    :return: None 
    """
    processor = TextProcessor()
    if recipe.directions is not None and len(recipe.directions) > 0:
      fulltext_tokens = processor.stem_document(recipe.directions)
      stopword_free_tokens = processor.stem_document(recipe.directions, remove_stopwords=True)

      for i in range(len(fulltext_tokens)):
        DirectionsFulltextIndex.objects.create(recipe=recipe, stem=fulltext_tokens[i], position=i)

      for i in range(len(stopword_free_tokens)):
        DirectionsIndex.objects.create(recipe=recipe, stem=stopword_free_tokens[i], position=i)
