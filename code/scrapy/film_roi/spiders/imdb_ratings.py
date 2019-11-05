# -*- coding: utf-8 -*-
import scrapy

from scrapy import Spider
from scrapy.loader import ItemLoader
from scrapy.loader.processors import TakeFirst

import pandas as pd
import re 

import logging

import pickle

# Use scrapy Items to scrape film data on page
class FilmData(scrapy.Item):
    title = scrapy.Field()
    metacritic = scrapy.Field()
    runtime = scrapy.Field()
    filmid = scrapy.Field()
    filmurl = scrapy.Field()

# import film page url list
csv_url='/Users/starplatinum87/Google Drive/DATA_SCIENCE/Projects/02_Film_ROI/film_roi/scraped_data/scrape_film_pages/scrape_film_pages_20190904_final.csv'
imdb_film_url_list = pd.read_csv(csv_url)['imdburl']
imdb_film_url_list = list(imdb_film_url_list)


# main parsing spider
class FilmPageSpider(Spider):
    name = 'imdb_ratings'
    start_urls = imdb_film_url_list
    custom_settings = {'DOWNLOAD_DELAY': '5',
                       'LOG_FILE': 'imdb_ratings.log',
                       'LOG_LEVEL': 'DEBUG',
                       'ROBOTSTXT_OBEY': 'False',
                       'COOKIES_ENABLED': 'False', 
                       'FEED_EXPORT_FIELDS': ['title', 'metacritic', 'runtime', 'filmid', 'filmurl']}
    
    # parse method to login
    def parse(self, response):
        # Use scrapy ItemLoader to populate Items with scraped data
        loader = ItemLoader(item=FilmData(), response=response)
        loader.add_value('title', response.text, re=r'<h1 class=".*?">(.+)&nbsp;<span id="titleYear">')
        loader.add_value('metacritic', response.text, re=r'<div class="metacriticScore.+\s<span>(\d+)<\/span>')
        loader.add_value('runtime', response.text, TakeFirst(), re=r'<time datetime="PT(\d+)M"') # TakeFirst() will get only the first instance of the runtime
        loader.add_value('filmid', response.text, re=r'<link rel="canonical" href="https:\/\/www\.imdb.com\/title\/(\w+)\/')
        loader.add_value('filmurl', response.text, re=r'<link rel="canonical" href="(https:\/\/www\.imdb.com\/title\/\w+)\/')
        yield loader.load_item()





        