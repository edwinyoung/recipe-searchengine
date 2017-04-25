from utils.database import CURSOR_WEBSCRAPER, sql_format
import psycopg2

class Recipe:
  def __init__(self, name, source_url, image_url, ingredients):
    # There are additional fields that are defined at the end of the class
    self.name = name
    self.source_url = source_url
    self.image_url = image_url
    self.ingredients = ingredients
    self.description = u''
    self.prep_time = -1
    self.cook_time = -1
    self.total_time = -1
    self.directions = u''

    self.ingredient_index = {}
    self.ingredient_index_fulltext = {}
    self.directions_index = {}
    self.directions_index_fulltext = {}

  def sql_get_document_id(self, cur=CURSOR_WEBSCRAPER):
    if self.source_url is None or u'http' not in self.source_url:
      return None
    statement = u'SELECT id FROM recipes WHERE source_url={source_url}'
    cur.execute(statement.format(source_url=sql_format(self.source_url)))
    return cur.fetchone()

  def sql_insert_ingredient(self):
    statements = []
    return statements

  def sql_insert_document(self):
    statement = u'INSERT INTO recipes ({fields}) VALUES ({items})'
    data = {
      u'name': sql_format(self.name),
      u'source_url': sql_format(self.source_url)
    }
    if self.image_url is not None:
      data[u'image_url'] = sql_format(self.image_url)
    if self.description is not None and len(self.description) > 0:
      data[u'description'] = sql_format(self.description)
    if self.prep_time > 0:
      data[u'prep_time'] = sql_format(self.prep_time)
    if self.cook_time > 0:
      data[u'cook_time'] = sql_format(self.cook_time)
    if self.total_time > 0:
      data[u'total_time'] = sql_format(self.total_time)
    if len(self.ingredients) > 0:
      data[u'ingredients'] = sql_format(self.ingredients)
    if self.directions is not None and len(self.directions) > 0:
      data[u'directions'] = sql_format(self.directions)

    fields = u', '.join(data.keys())
    items = u', '.join(data.values())
    return statement.format(fields=fields, items=items)

  def commit(self, cur=CURSOR_WEBSCRAPER):
    if self.db_id is None:
      cur.execute(self.insert_document_statement)

  def __repr__(self):
    return '[{0}, {1}, {2}, {3}]'.format(self.name, self.source_url, self.image_url, self.ingredients)

  def __unicode__(self):
    return u'[{0}, {1}, {2}, {3}]'.format(self.name, self.source_url, self.image_url, self.ingredients)

  def __str__(self, encoding="utf-8"):
    return self.__unicode__().encode(encoding)

  db_id = property(sql_get_document_id)
  insert_document_statement = property(sql_insert_document)
