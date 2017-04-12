
class Webscraper:
  """
  Parent class for all the webscrapers. Contains all the shared filters needed for BeautifulSoup.
  """
  def __init__(self):
    self.has_additional_results = False

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
