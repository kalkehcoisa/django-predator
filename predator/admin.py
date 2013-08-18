# -*- coding: utf-8 -*-

from django.contrib.admin import ModelAdmin, StackedInline, site
from django.db.models import ManyToManyField
from predator.models import WholeBlock, PageBlock, Content, Image
from django.contrib.admin.widgets import FilteredSelectMultiple


class WholeBlockAdmin(ModelAdmin):
    model = WholeBlock
    
class PageBlockAdmin(ModelAdmin):
    model = PageBlock
    
class ContentAdmin(ModelAdmin):
    model = Content
    
class ImageAdmin(ModelAdmin):
    model = Image


site.register(WholeBlock, WholeBlockAdmin) 
site.register(PageBlock, WholeBlockAdmin)
site.register(Content, WholeBlockAdmin)
site.register(Image, WholeBlockAdmin)