from django.db import models

class Ingredient(models.Model):
  display_name = models.CharField(max_length=60)
  search_name = models.CharField(max_length=60)

class Recipe(models.Model):
  name = models.CharField(max_length=200)
  source_url = models.CharField(max_length=255, unique=True)
  image_url = models.CharField(max_length=255, null=True)
  description = models.CharField(max_length=1000, null=True)
  prep_time = models.IntegerField(null=True)
  cook_time = models.IntegerField(null=True)
  total_time = models.IntegerField(null=True)
  ingredients = models.ManyToManyField(Ingredient)
  directions = models.TextField(null=True)

class DirectionsIndex(models.Model):
  recipe_id = models.ForeignKey(Recipe)
  stem = models.CharField(max_length=60)
  position = models.IntegerField()

class DirectionsFulltextIndex(models.Model):
  recipe_id = models.ForeignKey(Recipe)
  stem = models.CharField(max_length=60)
  position = models.IntegerField()

