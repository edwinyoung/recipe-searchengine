import config
import psycopg2

class DB:

  DSN = 'dbname={dbname} user={user} password={password}'

  # Helper function to check that all elements in a list/array are of the same type
  # Needed for SQL array type checking, since it's statically typed in SQL but not in Python
  # http://stackoverflow.com/a/13252348
  @staticmethod
  def _homogeneous_type(seq):
    iseq = iter(seq)
    first_type = type(next(iseq))
    return first_type if all((type(x) is first_type) for x in iseq) else False

  @staticmethod
  def connect(dbname, user, password):
    return psycopg2.connect(DB.DSN.format(dbname=dbname, user=user, password=password))

  @staticmethod
  def sql_escape_string(string):
    return string.replace(u"'", u"''")

  @staticmethod
  def sql_format(item):
    if isinstance(item, int) or isinstance(item, float):
      return unicode(item)
    if isinstance(item, str) or isinstance(item, unicode):
      return u"'{0}'".format(DB.sql_escape_string(unicode(item)))
    if isinstance(item, list) and len(item) > 0:
      if not DB._homogeneous_type(item):
        raise TypeError('List provided contains elements of different types.')
      string = u'ARRAY['
      values = []
      for i in item:
        values.append(DB.sql_format(i))
      string += u', '.join(values) + u']'
      return string
    return None

  @staticmethod
  def sql_get_ingredients(cursor):

    return


DB_CONN_WEBSCRAPER = DB.connect(**config.DATABASES['webscraper'])
DB_CONN_ENGINE = DB.connect(**config.DATABASES['searchengine'])

CURSOR_WEBSCRAPER = DB_CONN_WEBSCRAPER.cursor()
CURSOR_ENGINE = DB_CONN_ENGINE.cursor()
