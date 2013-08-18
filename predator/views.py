#-*- coding: utf-8 -*-

def home(request):
    from django.template import RequestContext
    from django.shortcuts import render_to_response
    from django.core.urlresolvers import reverse
    from predator.models import WholeBlock, PageBlock
    
    blocks = WholeBlock.objects.all()
    base_url = reverse( 'predator_predators' )
    return render_to_response('predator/home.html', { 'itens': blocks,
                                             'current_page': 'predator',
                                             'base_url': base_url,
                                            }, context_instance=RequestContext(request))

def predators(request, block='', page=1):
    from django.template import RequestContext
    from django.shortcuts import render_to_response
    from django.core.urlresolvers import reverse
    from predator.models import WholeBlock, PageBlock
    
    main = WholeBlock.objects.get(name=block)
    
    pages = PageBlock.objects.filter(wholeblock=main)
    
    pagina = {}
    pagina['itens_pagina'] = 12
    pagina['tags'] = False
    pagina['url'] = None
    try:
        pagina['page'] = int(page)
    except:
        pagina['page'] = 1
    
    pagina['num_pag'] = pages.count()/pagina['itens_pagina']
    if pagina['num_pag'] < 1:
        pagina['num_pag'] = 1
    if pagina['page'] < 1:
        pagina['page'] = 1
    if pagina['page'] > pagina['num_pag']:
        pagina['page'] = pagina['num_pag']
    
    itens = pages[(pagina['page']-1)*pagina['itens_pagina']:pagina['page']*pagina['itens_pagina']]
    
    base_url = reverse( 'predator_predators', kwargs={'block': block} )
    return render_to_response('predator/list.html', { 'paginas': range(1, pagina['num_pag']+1),
                                             'itens': itens,
                                             'current_page': 'predator',
                                             'base_url': base_url,
                                             'next_url': (base_url + str(pagina['page']+1)),
                                             'prev_url': (base_url + str(pagina['page']-1)),
                                             'next': pagina['page'] < pagina['num_pag'],
                                             'prev': pagina['page'] > 1,
                                             'page': pagina['page'],
                                             'url': pagina['url'],
                                             'block': block
                                            }, context_instance=RequestContext(request))
    
def predator_detail(request, id):
    from django.contrib.auth.models import User
    from django.template import RequestContext
    from django.shortcuts import render_to_response
    #from django.shortcuts import get_list_or_404#, get_object_or_404
    from django.http import Http404
    from predator.models import WholeBlock, PageBlock, Content, Image
    
    page = Content.objects.get(id=id).pageblock
    contents = page.content_set.all()
    #images = Image.objects.filter(pageblock=page)
    
    current_page = 'predator'
    return render_to_response('predator/detail.html', locals(), context_instance=RequestContext(request))
    
def predator_page_detail(request, id):
    from django.contrib.auth.models import User
    from django.template import RequestContext
    from django.shortcuts import render_to_response
    #from django.shortcuts import get_list_or_404#, get_object_or_404
    from django.http import Http404
    from predator.models import WholeBlock, PageBlock, Content, Image
    
    page = PageBlock.objects.get(id=id)
    contents = page.content_set.all()
    #images = Image.objects.filter(pageblock=page)
    
    current_page = 'predator'
    return render_to_response('predator/detail.html', locals(), context_instance=RequestContext(request))

