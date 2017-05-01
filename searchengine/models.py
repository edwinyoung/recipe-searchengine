from django.db import models

class Ingredient(models.Model):
  display_name = models.CharField(max_length=60)
  search_name = models.CharField(max_length=60)

  def __str__(self):
    return u', '.join(map(unicode, (self.id, self.display_name, self.search_name))).encode('utf-8')


class Recipe(models.Model):
  name = models.CharField(max_length=200)
  source_url = models.TextField(unique=True)
  image_url = models.TextField(null=True)
  description = models.TextField(null=True)
  prep_time = models.IntegerField(null=True)
  cook_time = models.IntegerField(null=True)
  total_time = models.IntegerField(null=True)
  ingredients = models.ManyToManyField(Ingredient)
  directions = models.TextField(null=True)

  def __str__(self):
    return u', '.join(map(unicode, (self.name, self.source_url))).encode('utf-8')


class DirectionsIndex(models.Model):
  recipe = models.ForeignKey(Recipe)
  stem = models.CharField(max_length=60)
  position = models.IntegerField()

  def __str__(self):
    return u', '.join(map(unicode, (self.recipe_id, self.stem, self.position))).encode('utf-8')


class DirectionsFulltextIndex(models.Model):
  recipe = models.ForeignKey(Recipe)
  stem = models.CharField(max_length=60)
  position = models.IntegerField()

  def __str__(self):
    return u', '.join(map(unicode, (self.recipe_id, self.stem, self.position))).encode('utf-8')
