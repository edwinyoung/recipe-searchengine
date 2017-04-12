import config
import psycopg2

DSN = 'dbname={dbname} user={user} password={password}'

def connect(dbname, user, password):
  return psycopg2.connect(DSN.format(dbname=dbname, user=user, password=password))

DB_CONN_WEBSCRAPER = connect(**config.DB_WEBSCRAPER)
DB_CONN_INDEX = connect(**config.DB_INDEX)
DB_CONN_ENGINE = connect(**config.DB_ENGINE)
