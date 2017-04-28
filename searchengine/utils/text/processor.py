# coding=utf-8
from operator import itemgetter
from nltk.stem.porter import PorterStemmer
from searchengine.models import Ingredient

# We want to extend nltk.stem.porter.PorterStemmer because the bulk of it does not need to be rewritten
# However, we do want something that can stem an entire document/string at once instead of just one document at a time
class TextProcessor(PorterStemmer):

  def __init__(self):
    super(TextProcessor, self).__init__()
    self.stopwords = (u'the', u'is', u'at', u'of', u'on', u'and', u'a')
    self.quotes = u"‘'’"  # Unicode string containing the single quote (it's) AND the right single quote (it’s)

    # Character replacement dictionary, since some ingredients may be listed in their recipes with or
    # without their special characters - acts as another step in normalization for the search engine
    self.char_dict = {
      u'à': u'a',
      u'á': u'a',
      u'â': u'a',
      u'ä': u'a',
      u'æ': u'a',
      u'ã': u'a',
      u'å': u'a',
      u'ā': u'a',
      u'ç': u'c',
      u'ć': u'c',
      u'č': u'c',
      u'è': u'e',
      u'é': u'e',
      u'ê': u'e',
      u'ë': u'e',
      u'ē': u'e',
      u'ė': u'e',
      u'ę': u'e',
      u'î': u'i',
      u'ï': u'i',
      u'í': u'i',
      u'ī': u'i',
      u'į': u'i',
      u'ì': u'i',
      u'ł': u'l',
      u'ñ': u'n',
      u'ń': u'n',
      u'ô': u'o',
      u'ö': u'o',
      u'ò': u'o',
      u'ó': u'o',
      u'œ': u'o',
      u'ø': u'o',
      u'ō': u'o',
      u'õ': u'o',
      u'ß': u'ss',
      u'ś': u's',
      u'š': u's',
      u'û': u'u',
      u'ü': u'u',
      u'ù': u'u',
      u'ú': u'u',
      u'ū': u'u',
      u'ÿ': u'y',
      u'ž': u'z',
      u'ż': u'z'
    }

  def stem(self, word):
    """
    Stems a word. Additional handling for edge cases in which the stemmed word ends in an apostrophe.
    
    :param word: string/unicode String to be stemmed
    :return: unicode String representing the stemmed word
    """
    word = unicode(super(TextProcessor, self).stem(word))
    if word[-1] == u"'":
      return word[:-1]
    return word

  def tokenize_text(self, data):
    """
      Tokenizes strings using word boundaries.
      
      Removes almost all punctuation, excluding apostrophes for stuff such as "Moscato d'Asti" and "brewer's yeast".

      :param data: a string containing the text of a document
      :return: tokens: list of strings containing the processed tokens in the document
    """
    data = data.strip()
    tokens = []
    token = u''
    for i in range(len(data)):
      char = data[i]
      # Add to current token if not a non-word character
      if char.isalnum() or char in self.quotes:
        # Special conditions to handle apostrophe in string to make sure it's a contraction or possessive
        # E.g. bird's [eye chilies], brewer's [yeast], [Moscato] d'Asti (including right single quote char)
        if char in self.quotes:
          # Checks to see if it's the beginning of a word
          # E.g. ('What) in ('What a knob-end')
          if len(token) == 0:
            continue
          # Checks for trailing apostrophes and adds token if the constructed token is non-zero length
          # E.g. (end') in ('What a knob-end')
          elif i + 1 >= len(data) or not data[i + 1].isalnum():
            if len(token) > 0:
              tokens.append(token)
              token = u''
            continue
          # If it's managed to get this far, it's passed all the tests and we'll want to store just the
          # apostrophe/single quote, and not the right single quote character for the sake of stemming consistency
          token += u'\''
        # Converts special unicode chars to ASCII chars for lookup consistency
        elif char in self.char_dict:
          token += self.char_dict[char]
        # Normal case (any time character is not an apostrophe, right single quote, or a non-ASCII character)
        else:
          token += char
      # If not, check to see that we have a token so we don't push empty tokens to the tokens list
      elif len(token) > 0:
        # Edge case for stuff like '2%' in '2% skim milk'
        if char == u'%':
          token += u'%'
        tokens.append(token)
        token = u''
    # Edge case - adds the last word in the doc
    if len(token) > 0:
      tokens.append(token)
    return tokens

  def stem_document(self, text, remove_stopwords=False):
    """
    Turns a string representing a document into a list of stemmed unicode tokens.
    
    :param text:              str/unicode Text/string to be tokenized & stemmed
    :param remove_stopwords:  boolean Flag to remove stopword tokens from the token list 
    :return:                  unicode list List of unicode token stems in the document
    """
    tokens = map(unicode.lower, self.tokenize_text(text))
    if remove_stopwords:
      tokens = [i for i in tokens if i not in self.stopwords]
    tokens = map(self.stem, tokens)
    return tokens

  def match_ingredient(self, ingredient_string):
    """
    Attempts to find the id of the ingredient whose name most closely matches the ingredient listed for a recipe.

    :param ingredient_string: unicode String with measurement and preparation instructions
    :return: int/None ID of the most relevant ingredient in the database, or None if not found
    """
    if ingredient_string is None or len(ingredient_string) < 1:
      return None
    stemmed_target_tokens = self.stem_document(ingredient_string)

    if len(stemmed_target_tokens) < 1:
      return None

    # Our version of a do-while loop
    token = stemmed_target_tokens[0]
    queryset = [ingredient for ingredient in Ingredient.objects.filter(search_name__icontains=token)
                if token in ingredient.search_name.split()]

    # Have to check that the target ingredient wasn't a single word so we don't get an IndexError
    if len(stemmed_target_tokens) > 1:
      for token in stemmed_target_tokens[1:]:
        queryset += [ingredient for ingredient in Ingredient.objects.filter(search_name__icontains=token)
                     if token in ingredient.search_name.split()]

    # Sort by the ingredients that have the highest similarity first, then by which ingredient is the longer
    # Let's say our ingredient string is '1/4 cup chopped celery root'
    # We'll get all ingredients with '1', '4', 'cup', 'chop', 'celeri', 'root' in them after stemming
    #     (Sample: 'peanut butter cup', 'chop carrot', 'chop onion', 'celeri root', 'celeri root leav', 'root veggi')
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

    queryset = list(set(queryset))

    search_dictionaries = []
    for ingredient in queryset:
      dictionary = {'id': ingredient.id}
      stemmed_search_tokens = ingredient.search_name.split()
      found = [i for i in stemmed_search_tokens if i in stemmed_target_tokens]
      dictionary['name'] = ingredient.display_name
      dictionary['search'] = ingredient.search_name
      dictionary['similarity'] = len(found) / float(len(stemmed_search_tokens))
      dictionary['len'] = len(stemmed_search_tokens)
      search_dictionaries.append(dictionary)

    if len(search_dictionaries) < 1:
      return None

    search_dictionaries = sorted(search_dictionaries, key=itemgetter('similarity', 'len'), reverse=True)
    return search_dictionaries[0]['id']
