# -*- coding: utf-8 -*-


from django.db.models import Model
#from django.db.models import permalink as models_permalink
from django.db.models import BooleanField, CharField, ForeignKey, TextField, ImageField
#from django.contrib.contenttypes.models import ContentType
#from django.core.urlresolvers import reverse
#from django.contrib.auth.models import User

from django.utils.encoding import smart_str
#from django.utils.html import strip_tags

#import settings
#from ckeditor.fields import HTMLField as ckeditor_HTMLField
#from thumbs import ImageWithThumbsField
#from predator.helpers import unescape


class WholeBlock(Model):
    '''
    This model represents the website/the craw execution.
    '''
    name = CharField(max_length=255, null=False, blank=False, unique=True)
    #finished = BooleanField(default=0)
    last_page = ForeignKey('predator.PageBlock', null=True, blank=True, related_name='last_page')
    
    def __str__(self):
        return smart_str(self.name).decode('utf-8')
    
    def __unicode__(self):
        return smart_str(self.name).decode('utf-8')
    
    class Meta():
        ordering = ['id',]


class PageBlock(Model):
    '''
    This model stores a single url from the page/pages to be crawled.
    '''
    url = CharField(max_length=1024, null=False, blank=False)
    wholeblock = ForeignKey('predator.WholeBlock', null=False, blank=False)
    cache = TextField(null=True, blank=True) #cache to not need to retrieve the page code again 
    
    def __str__(self):
        return smart_str(self.url).decode('utf-8')
    
    def __unicode__(self):
        return smart_str(self.url).decode('utf-8')
    
    class Meta():
        ordering = ['id',]


class Content(Model):
    '''
    This model stores the data fetched by one filter used on one page.
    '''    
    name = CharField(max_length=255, null=False, blank=False)
    content = TextField(null=True, blank=True, default='')
    pageblock = ForeignKey('predator.PageBlock', null=False, blank=False)
    
    def __str__(self):
        return smart_str(self.content[:100]).decode('utf-8')
    
    def __unicode__(self):
        return smart_str(self.content[:100]).decode('utf-8')
    
    class Meta():
        ordering = ['id',]


class Image(Model):
    '''
    This model store a image fetched from a page.
    '''
    image = ImageField(upload_to='predator_files', null=False, blank=False)
    content = ForeignKey('predator.Content', null=False, blank=False)
    
    #link = CharField(max_length=512, null=True, blank=True)
    #legenda = TextField(null=True, blank=True)
    
    def __str__(self):
        return smart_str(self.image).decode('utf-8')
    
    def __unicode__(self):
        return smart_str(self.image).decode('utf-8')
    
    class Meta():
        ordering = ['id',]


'''class File(Model):
    file = FileField(upload_to='predator_files', null=False, blank=False)
    content = ForeignKey('predator.Content', null=False, blank=False)
    
    def __str__(self):
        return smart_str(self.file).decode('utf-8')
    
    def __unicode__(self):
        return smart_str(self.file).decode('utf-8')'''
    
    
    