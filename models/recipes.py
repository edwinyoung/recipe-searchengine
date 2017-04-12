
class Recipe:
  def __init__(self, name, source_url, image_url, ingredients):
    self.name = name
    self.source_url = source_url
    self.image_url = image_url
    self.ingredients = ingredients
    self.description = u''
    self.prep_time = 0
    self.cook_time = 0
    self.total_time = 0
    self.directions = u''

  def __str__(self):
    return '[{0}, {1}, {2}, {3}]'.format(self.name, self.source_url, self.image_url, self.ingredients)

  def __repr__(self):
    return '[{0}, {1}, {2}, {3}]'.format(self.name, self.source_url, self.image_url, self.ingredients)

  def __unicode__(self):
    return u'[{0}, {1}, {2}, {3}]'.format(self.name, self.source_url, self.image_url, self.ingredients)

