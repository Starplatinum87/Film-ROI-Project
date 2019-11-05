# -*- coding: utf-8 -*-
from time import sleep

import scrapy
import selenium

from scrapy import Spider
from scrapy.loader import ItemLoader
from scrapy import Selector
from scrapy.http import FormRequest

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0

import pandas as pd
import re 

import pickle
import logging

# from .. import items # imports items module from one folder level up

# Function to convert budget dollar amount strings to floats for ItemLoader
def dollars_to_floats(self, amount):
    try:
        amount = amount[0] # extracting entry as string b/c add_xpath returns a list
        floats = float(re.sub('[$£€]|[A-Z]{1,3}|,', '', amount))
        return floats
    except Exception as ex:
        logging.debug('EXCEPTION!!! dollars_to_floats: ' + str(ex))
        return 'Not Found'

# Function to make genre string a list for ItemLoader
def genre_to_list(self, genres):
    try:
        genres = genres[0] # extracting entry as string b/c add_xpath returns a list
        genres = re.findall(r'[A-Za-z\-]+', genres)
        return genres
    except Exception as ex:
        logging.debug('EXCEPTION!!! genre_to_list: ' + str(ex))
        return 'Not Found'

# Funcion to clean user vote numbers and convert to ints
def clean_user_votes(self, votes):
    try:
        votes = votes[-1]
        votes = re.findall(r'(.*\d+)', votes)[-1]
        votes = int(re.sub(',', '', votes))
        return votes
    except Exception as ex:
        logging.debug('EXCEPTION!!! clean_user_votes:' + str(ex))
        return 'Not Found'

# Function to extract the film ID 
def extract_ID(self, url):
    try:
        ID = re.findall(r'title\/(\w+)', url)[-1]
        return ID
    except Exception as ex:
        logging.debug('EXCEPION!!! extract_ID:' + str(ex))
        return 'Not Found'

# Use scrapy Items to scrape film data on page
class FilmData(scrapy.Item):
    title = scrapy.Field()
    # genres = scrapy.Field()
    # release = scrapy.Field()
    # budget = scrapy.Field()
    # openinggross = scrapy.Field()
    # uscagross = scrapy.Field()
    # worldgross = scrapy.Field()
    # userrating = scrapy.Field()
    # uservotes = scrapy.Field()
    # articles = scrapy.Field()
    filmid = scrapy.Field()

# Custom ItemLoader class
# class FilmDataLoader(ItemLoader):
    # genres_out=genre_to_list
    # budget_out=dollars_to_floats
    # openinggross_out=dollars_to_floats
    # uscagross_out=dollars_to_floats
    # worldgross_out=dollars_to_floats
    # userrating=dollars_to_floats
    # uservotes_out=clean_user_votes
    # filmid_out=extract_ID

# # import film page url list
# csv_url='/Users/starplatinum87/Google Drive/DATA_SCIENCE/Projects/02_Film_ROI/film_roi/scraped_data/2019.08.15.1503/film_roi_list.csv'
# film_url_list = pd.read_csv(csv_url)['film_page_urls']
# film_url_list = list(film_url_list)
# # clean urls with regex and create list for start_urls
# url_cleaner = re.compile(r'.+\/title\/\w+\/')
# film_url_list = [url_cleaner.findall(url)[0] for url in film_url_list] # [0] slice is to change from list of lists to list of strings

# main parsing spider
class FilmPageSpider(Spider):
    name = 'test_scraper'
    start_urls = ['https://www.imdb.com/title/tt6105098/',
                  'https://www.imdb.com/title/tt2066051/',
                  'https://www.imdb.com/title/tt6533240/',
                  'https://www.imdb.com/title/tt6565702/',
                  'https://www.imdb.com/title/tt7983890/',
                  'https://www.imdb.com/title/tt7802246/',]
    custom_settings = {'DOWNLOAD_DELAY': '2',
                       'LOG_FILE': 'test_scraper.log',
                       'LOG_LEVEL': 'DEBUG',
                       'ROBOTSTXT_OBEY': 'False',
                       'COOKIES_ENABLED': 'False', 
                       'FEED_EXPORT_FIELDS': ['title','filmid']}
    
    # def parse(self, response):        
    #     # pages = film_url_list[35:38]  
    #     pages = ['https://www.imdb.com/title/tt6105098/']
    #     global address # set the address variable for urls to global so the get_data function can grab them
    #     for address in pages:
    #         yield scrapy.Request(url=address, callback=self.get_data) # use yield here to continue to iterate on the urls

    def parse(self, response):
        # Use scrapy ItemLoader to populate Items with scraped data
        loader = ItemLoader(item=FilmData(), response=response)
        loader.add_xpath('title', '/html/head/title/text()')
        loader.add_value('filmid', re.findall(r'title\/(\w+)\?rf=cons_tt_btf_cc', response.text)[0])
        yield loader.load_item()
    


        