# -*- coding: utf-8 -*-
import scrapy

from scrapy import Spider
from scrapy.loader import ItemLoader
from scrapy import Selector
from scrapy.http import FormRequest

import pandas as pd
import re 

import logging

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

# Use scrapy Items to scrape film data on page
class FilmData(scrapy.Item):
    title = scrapy.Field()
    genres = scrapy.Field()
    release = scrapy.Field()
    budget = scrapy.Field()
    openinggross = scrapy.Field()
    uscagross = scrapy.Field()
    worldgross = scrapy.Field()
    userrating = scrapy.Field()
    uservotes = scrapy.Field()
    articles = scrapy.Field()
    filmid = scrapy.Field()
    filmurl = scrapy.Field()
    imdburl = scrapy.Field()

# Custom ItemLoader class
class FilmDataLoader(ItemLoader):
    genres_out=genre_to_list
    budget_out=dollars_to_floats
    openinggross_out=dollars_to_floats
    uscagross_out=dollars_to_floats
    worldgross_out=dollars_to_floats
    userrating=dollars_to_floats
    uservotes_out=clean_user_votes

# import film page url list
csv_url='/Users/starplatinum87/Google Drive/DATA_SCIENCE/Projects/02_Film_ROI/film_roi/scraped_data/scrape_film_pages/2019.08.15.1503/film_roi_list.csv'
film_url_list = pd.read_csv(csv_url)['film_page_urls']
film_url_list = list(film_url_list)
# clean urls with regex and create list for start_urls
url_cleaner = re.compile(r'.+\/title\/\w+\/')
film_url_list = [url_cleaner.findall(url)[0] for url in film_url_list] # [0] slice is to change from list of lists to list of strings

# main parsing spider
class FilmPageSpider(Spider):
    name = 'scrape_film_pages'
    start_urls = ['https://pro.imdb.com/login/imdb?u=%2F']
    custom_settings = {'DOWNLOAD_DELAY': '10',
                       'LOG_FILE': 'scrape_film_pages.log',
                       'LOG_LEVEL': 'DEBUG',
                       'ROBOTSTXT_OBEY': 'False',
                       'COOKIES_ENABLED': 'False', 
                       'FEED_EXPORT_FIELDS': ['title', 'genres', 'release', 'budget', 'openinggross',
                                              'uscagross', 'worldgross', 'userrating', 'uservotes', 
                                              'articles', 'filmid', 'filmurl', 'imdburl']}
    
    # parse method to login
    def parse(self, response):
        # User Agent header that will be sent when making a request through Scrapy, which mimics a legitimate browser
        # Found by Googling 'my User Agent header'
        self.header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'}
        # Get login info from local file
        login = open('/Users/starplatinum87/Google Drive/hisoka/imdb.txt', 'r').read()
        login = login.split('\n')[0:2]
        # Login using the response, then move to next function
        return FormRequest.from_response(
            response,
            formdata={'username': login[0], 'password': login[1]},
            callback=self.request_page
            )

    def get_data(self, response):
        # Use scrapy ItemLoader to populate Items with scraped data
        loader = FilmDataLoader(item=FilmData(), response=response)
        loader.add_xpath('title', '//*[@id="title_heading"]/h1/span/text()')
        loader.add_xpath('genres', '//*[@id="genres"]/text()')
        loader.add_xpath('release','//*[@id="a-page"]/div[4]/div/div/div/div/div[2]/div[2]/div/div[2]/div[3]/span[1]/a/text()')
        loader.add_xpath('budget', '//*[@id="box_office_summary"]/div[2]/div[1]/div/div[2]/text()')
        loader.add_xpath('openinggross','//*[@id="box_office_summary"]/div[2]/div[2]/div/div[2]/text()')
        loader.add_xpath('uscagross','//*[@id="box_office_summary"]/div[2]/div[3]/div/div[2]/text()')
        loader.add_xpath('worldgross','//*[@id="box_office_summary"]/div[2]/div[4]/div/div[2]/text()')
        loader.add_xpath('userrating', '//*[@id="rating_breakdown"]/div[1]/div/div/div[1]/div/div/div[1]/span[2]/text()')
        loader.add_xpath('uservotes', '//*[@id="rating_breakdown"]/div[1]/div/div/div[1]/div/div/div[1]/span[3]/text()')
        loader.add_xpath('articles','//*[@id="popularity_widget"]/div[2]/div/div/div[2]/div[2]/div/div[2]/span/a/text()')
        loader.add_value('filmid', response.text, re=r'title\/(\w+)\/boxoffice\?ref_=tt_pub_see_all_boxoffice')
        loader.add_value('filmurl', response.text, re=r'(https:\/\/pro\.imdb\.com\/title\/\w+)\/boxoffice\?ref_=tt_pub_see_all_boxoffice')
        loader.add_value('imdburl', response.text, re=r'(http:\/\/www\.imdb\.com\/title\/\w+)\/\?ref_=pro_tt_pub_visitcons')
        yield loader.load_item()
    
    def request_page(self, response):        
        pages = film_url_list
        global address # set the address variable for urls to global so the get_data function can grab them
        for address in pages:
            yield scrapy.Request(url=address, callback=self.get_data) # use yield here to continue to iterate on the urls




        