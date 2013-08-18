#!/usr/bin/python
# -*- coding: utf-8 -*-

import gc
import os
import re
import sys
import urllib
import urllib2
import socket
import time
socket.setdefaulttimeout(30)

from BeautifulSoup import BeautifulSoup, Comment, BeautifulStoneSoup
import MySQLdb as mdb

from django.contrib.auth.models import User
from django.core.files import File
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.utils.encoding import smart_str, force_unicode
from django.utils.html import strip_tags

import settings
#from noticia.models import Noticia, Imagem
#from reuso.models import Reuso, Imagem
from predator.models import WholeBlock, PageBlock, Content, Image

class Crawler():
    
    testMode = False #only browses. Do not download the images
    start = 1
    
    root = None     #store the WholeBlock object used here
    indexes = None  #store the indexes pages to gather the pages urls to get the page urls
    index_filters = None  #filter the contents of the pages to scrap
    index_clear_rules = None #rules to remove garbage and no needed elements from indexes being crawled
    
    page_filter_content = None #select the block of content to take from the page
    page_clear_rules = None #rules to remove garbage and no needed elements from all the pages being crawled
    
    
    content_blocks = None #rules to separate the contents gotten from the url
    content_block_filters = None #rules to filter the contents of a content block
    
    manualClearContentBeforeDownload = None #manual method to clear the contents before starting downloading the images, files, etc
    manualGetContent = None #manual method to get contents from the pages 
    
    downloadImages = True #variable to download images from the html files or not
    
    minContentLength = 100 #if a page is smaller than this, try retrieving it again
    
    timeout = 20 #timeout used to limit the time of the requests
    sleepTime = 5
    
    cur = None  #store the mysql cursor to run the queries
    con = None  #store the mysql connection (commits, rollbacks, etc)
    
    targetDirectory = 'default'
    basePath = os.path.dirname(__file__)
    siteDomain = None

    def __init__(self, args):
        self.siteDomain = args['siteDomain']
        
        self.indexes = args['indexes']
        self.index_filters = args['index_filters']
        if 'index_clear_rules' in args:
            self.index_clear_rules = args['index_clear_rules']
        
        self.page_filter_content = args['page_filter_content']
        self.page_clear_rules = args['page_clear_rules']
        
        self.content_blocks = args['content_blocks']
        #self.content_block_filters = args['content_block_filters']
        
        #self.manualClearContentBeforeDownload = args['manualClearContentBeforeDownload']
        self.targetDirectory = args['targetDirectory']
    
    
    def urlretrieve(self, url, dirr):
        url = smart_str(url)
        for p in xrange(0, 10):
            try:
                request = urllib2.urlopen( url, timeout = self.timeout )
                fil = open( dirr, 'wb+' )
                fil.write(request.read())
                fil.close()
                break
            except:
                time.sleep( self.sleepTime )
            
    
    def unescape(self, text):
        import htmlentitydefs
        def fixup(m):
            text = m.group(0)
            if text[:2] == "&#":
                # character reference
                try:
                    if text[:3] == "&#x":
                        return unichr(int(text[3:-1], 16))
                    else:
                        return unichr(int(text[2:-1]))
                except ValueError:
                    pass
            else:
                # named entity
                try:
                    text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
                except KeyError:
                    pass
            return text  # leave as is
        return re.sub("&#?\w+;", fixup, text)
    
    def connect(self):
        try:
            self.con = mdb.connect('localhost', 'root', '', 'kalkehcoisa_sust2', charset = "utf8", use_unicode = True);
            self.cur = self.con.cursor()
            # cur.execute("TRUNCATE TABLE coleta_tag")
            # cur.execute("TRUNCATE TABLE coleta_coleta_tags")
            # cur.execute("TRUNCATE TABLE coleta_contato")
            # cur.execute("TRUNCATE TABLE coleta_tipocoleta")
            # cur.execute("SELECT VERSION()")
            # data = cur.fetchone()
            
            # print "Database version : %s " % data
        except mdb.Error, e:
            print "Error %d: %s" % (e.args[0], e.args[1])
            sys.exit(1)

       
    def crawIndexPage(self, url='', params=None):
        '''
        This method extracts the urls from an index page ("url"?"params")
        and returns a list of urls based on "self.index_filters".
        '''
        print 'Started getting pages from the index: '+str(url)
        try:
            query = urllib.urlencode(params)
        except:
            query = None
        req = urllib2.Request(url, query)
        for p in xrange(0, 10):
            try:
                response = urllib2.urlopen(req, timeout = self.timeout)
                contents = response.read()
                break
            except:
                time.sleep( self.sleepTime )
        soup = BeautifulSoup(contents)
        
        #remove all the code blocks the user doesn't want
        if self.index_clear_rules is not None:
            for rule in self.index_clear_rules:
                if 'plain_tags' in rule:
                    for p in rule['plain_tags'].split(','):
                        try:
                            [p.extract() for p in soup.findAll(p)]
                        except:
                            pass
                elif 'element' in rule:
                    try:
                        soup.find(rule['element'].keys()[0], rule['element'].values()[0]).extract()
                    except:
                        pass
        
        links = []
        for tup in self.index_filters:
            for p in soup.findAll(tup['container'].keys()[0], tup['container'].values()[0]):
                for l in p.findAll(tup['tag'].keys()[0]):#[ tup['tag'].values()[0] ]
                    links.append( l[ tup['tag'].values()[0] ] )
        print 'Finished getting pages from the index: '+str(url)
        return links
    
    def makePagesList(self):
        '''
        This method saves in PageBlock models the urls extracted from the index pages.
        '''
        print 'Started gathering the pages links.'
        for arr in self.indexes.values():
            for link in arr:
                print '\t'+str(link)
                pages = self.crawIndexPage( link )
                for page in pages:
                    if PageBlock.objects.filter(url = page).count() == 0:
                        print '\t\t'+str(page)
                        pag = PageBlock()
                        if page.find(self.siteDomain) > -1:
                            pag.url = page
                        else:
                            pag.url = self.siteDomain+page
                        pag.wholeblock = self.root
                        pag.save()
        print '\nFinished gathering the pages links.\n'

    def readPagesList(self, last_id=None, begin=None, end=None):
        '''
        Return the list of PageBlock based on the current root WholeBlock.
        '''
        query = None
        if last_id is None:
            last_id = self.root.last_page.id
            if last_id is None:
                query = PageBlock.objects.filter( wholeblock=self.root )
        if query is None:
            query = PageBlock.objects.filter( wholeblock=self.root, id__gt=last_id )
        
        if begin is not None and end is not None:
            return query[begin:end]
        elif begin is not None:
            return query[begin:]
        elif end is not None:
            return query[:end]
        return query
    
    def startScraping(self, name='test'):
        '''
        Create or retrieve the WholeBlock of scraping with "name".
        '''
        print 'Started.'
        try:
            self.root = WholeBlock.objects.get(name=name)
            print smart_str('Loaded WholeBlock: "'+self.root.name+'".\n\n')
        except: 
            self.root = WholeBlock(name=name)
            self.root.save()
            print 'Created WholeBlock.\n\n'
    
    
    def getPageItself(self, page):
        '''
        Receive a PageBlock object (page), retrieves the data contained on its url,
        save this data in an Content object and return it. 
        '''
        print 'Started getting page '+str(page)
        for p in xrange(0, 5):
            minLength = page.cache is not None and len(page.cache) < self.minContentLength
            if minLength:
                print page.id, page.cache
            if page.cache is None or minLength:
                url = page.url
                req = urllib2.Request(url)
                contents = None
                for p in xrange(0, 10):
                    try:
                        response = urllib2.urlopen(req, timeout = self.timeout)
                        contents = response.read()
                        break
                    except:
                        time.sleep( self.sleepTime )
                    else:
                        response.close()
                if contents is None:
                    return
                soup = BeautifulSoup(contents)
                page.cache = str(soup)
                page.save()
            else:
                soup = BeautifulSoup(page.cache)
            if len(page.cache) > self.minContentLength:
                break
        #soup = soup.find('body')
        
        for rule in self.page_clear_rules:
            if 'plain_tags' in rule:
                for p in rule['plain_tags'].split(','):
                    try:
                        [p.extract() for p in soup.findAll(p)]
                    except:
                        pass
            elif 'element' in rule:
                try:
                    soup.find(rule['element'].keys()[0], rule['element'].values()[0]).extract()
                except:
                    pass
        conts = []
        for p in self.content_blocks:
            print 'Getting a pageblock.'
            tag = p.values()[0].keys()[0]
            filt = p.values()[0][tag]
            if p.keys()[0].find('wholepage') > -1:
                aux_soup = soup
            else:
                if self.page_filter_content.values()[0] is not None:
                    aux_soup = soup.find(self.page_filter_content.keys()[0], self.page_filter_content.values()[0])
                else:
                    aux_soup = soup.find(self.page_filter_content.keys()[0])
            
            if not self.testMode and Content.objects.filter(pageblock = page, name = p.keys()[0]).count() == 0:
                if aux_soup is None:
                    return None
                else:
                    if tag is None:
                        aux = [aux_soup]
                    else:
                        aux = aux_soup.findAll( tag, filt )

                    for c in aux:
                        cont = Content()
                        cont.pageblock = page
                        cont.name = p.keys()[0]
                        content = str( c )
        
                        if self.manualClearContentBeforeDownload is not None:
                            content = self.manualClearContentBeforeDownload(content)
                        
                        cont.content = smart_str(content).decode('utf-8')
                        cont.save()
                        conts.append( cont )
            else:
                conts.extend( list( Content.objects.filter(pageblock = page, name = p.keys()[0]) ) )
        
        print 'Finished getting page '+str(page)
        return conts
    
    

       
    
    def writeImage(self, image, dirr):
        image = smart_str(image)
        iname = image.rsplit('/', 1)[-1]
        name = slugify(iname.rsplit('.', 1)[0])
        formatt = iname.rsplit('.', 1)[-1]
        i = 0
        if not self.testMode:
            while True:
                try:
                    if i > 0:
                        writename = dirr + "%s-%d.%s" % (name, i, formatt)
                    else:
                        writename = dirr + "%s.%s" % (name, formatt)
                    writename = self.unescape(writename).replace(' ', '-')
                    fil = open(writename, 'r')
                    fil.close()
                    i += 1
                except:
                    try:
                        self.urlretrieve(image, writename)
                    except:
                        self.urlretrieve((self.siteDomain + image), writename)
                    break
        else:
            writename = (dirr + "%s-%d.%s" % (name, i, formatt))
        print image, '\n', writename
        return writename
    
    
    
    def getContents(self, cont):
        #'''
        #This method is used to get and save the data from a specific page. It process the html, 
        #save the images to the disk and insert the data into the database.
        #'''
        number = cont.id
        dirr = self.basePath+"/%s/%.6d/" % (self.targetDirectory, number)
        soup = BeautifulSoup( smart_str(cont.content) )
        
        #locate all the images in the page, download, write them to disc
        #and fix the reference in the code
        if self.downloadImages:
            if not os.path.exists(dirr):
                os.makedirs(dirr)
            
            for img in soup.findAll('img'):
                imag = self.writeImage(img['src'], dirr)
                im = Image()
                im.content = cont
                try:
                    im.image.save( os.path.basename(imag), File( open(imag) ) )
                    im.save()
                    img['src'] = im.image.url
                except:
                    pass
            
        
        if self.manualGetContent is not None:
            self.manualGetContent(self, soup, cont, dirr, Image)
        
        cont.content = smart_str( soup )
        cont.save()


    def clearPagesListByURL(self, contain):
        '''
        Delete all the pages which url contains the string "contain".
        '''
        pages = self.readPagesList()
        for p in pages:
            if p.url.find(contain) > -1:
                p.delete()
    
    
    def run(self):
        self.testMode = False
        #self.start = 1
        self.downloadImages = False 
        self.minContentLength = 100
        
        i = 1
        self.startScraping( self.targetDirectory )
        #self.makePagesList()
        #self.clearPagesListByURL('#disqus_thread')
        
        #pages = self.readPagesList()
        #pages = pages[self.start-1:]
        
        
        pageSize = 100
        count = self.readPagesList().count()
        if count > pageSize:
            numPages = count/pageSize+1
            indexes = xrange(1, numPages+1)
        else:
            indexes = xrange(1, 2)
        
        
        contCollect = 0
        for p in indexes:
            pages = self.readPagesList(last_id=None, begin=(p-1)*pageSize, end=(p)*pageSize)
            for page in pages:#pages[:pageSize]:
                print '\n', i, page.id
                conts = self.getPageItself( page )
                if conts is not None:
                    for cont in conts:
                        self.getContents( cont )
                self.root.last_page = page
                self.root.save()
                i += 1
            #pages = pages[pageSize:]
            del pages
            #added garbage collecting to reduce the memory use with trash and speed up the tool
            if contCollect > 5:
                gc.collect()
                contCollect = 0
            contCollect += 1



