from django.conf.urls.defaults import patterns

urlpatterns = patterns('predator.views',
    (r'list/$', 'predators', {}, 'predator_predators'),
    (r'list/(?P<block>.*)/(?P<page>\d+)/$', 'predators', {}, 'predator_predators'),
    (r'list/(?P<block>.*)/$', 'predators', {}, 'predator_predators'),
    
    (r'detail/page/(?P<id>\d+)/$', 'predator_page_detail', {}, 'predator_page_detail'),
    (r'detail/(?P<id>\d+)/$', 'predator_detail', {}, 'predator_detail'),
    
    (r'$', 'home', {}, 'predator_home'),
    #(r'(?P<permalink>.*)/$', 'predator', {}, 'predator_item'),
)