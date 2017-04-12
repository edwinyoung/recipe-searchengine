# coding=utf-8
from nltk.stem.porter import PorterStemmer

# We want to extend nltk.stem.porter.PorterStemmer because the bulk of it does not need to be rewritten
# However, we do want something that can stem an entire document at once instead of just one document at a time
class TextProcessor(PorterStemmer):
  def __init__(self):
    super(TextProcessor, self).__init__()
    self.stopwords = (u'the', u'is', u'at', u'of', u'on', u'and', u'a')
    self.quotes = u'\'’'  # Unicode string containing the single quote (it's) AND the right single quote (it’s)

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
        # E.g. d'Avignon, brewer's, shouldn't've (including right single quote char)
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
        # Normal case (any time character is not an apostrophe or a right single quote)
        else:
          token += char
      # If not, check to see that we have a token so we don't push empty tokens to the tokens list
      elif len(token) > 0:
        tokens.append(token)
        token = u''
    # Edge case - adds the last word in the doc
    if len(token) > 0:
      tokens.append(token)
    return tokens

  def stem_document(self, text, remove_stopwords=True):
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
