from django.db import models
from django.urls import reverse
# Create your models here.
class Category(models.Model):
    category_name = models.CharField(max_length=200,unique=True)
    slug = models.SlugField(max_length=200,unique=True)
    description = models.TextField(blank=True,max_length=200)
    category_image = models.ImageField(blank=True,upload_to='photos/category_image')

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def get_url(self):
        return reverse('products_by_category', args=[self.slug])

    def __str__(self):
        return self.category_name
