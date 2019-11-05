# -*- coding: utf-8 -*-
from time import sleep

import scrapy
import selenium

from scrapy import Spider
from scrapy.selector import Selector

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0

import pandas as pd

from collections import OrderedDict

import pickle
import logging


class ImdbproSpider(Spider):
    name = 'imdbpro_film_list'
    allowed_domains = ['pro.imdb.com'] # Note here the 'domain' is not like the URL below. No 'https://'
    start_urls = ['https://pro.imdb.com/']
    
    # # Custom export settings
    # custom_settings={'FEED_URI':'/Users/starplatinum87/Google Drive/DATA_SCIENCE/Projects/02_Film_ROI/film_roi/%(time)s/%(time)s.csv', 
    #                 'FEED_FORMAT': 'csv'}

    def parse(self, response):

        # User Agent header that will be sent when making a request through Scrapy, which mimics a legitimate browser
        # Found by Googling 'my User Agent header'
        self.header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36'}
        
        # Open IMDbPro Log in page 
        self.driver = webdriver.Chrome('/Applications/chromedriver')
        self.driver.get('https://pro.imdb.com/login/imdb?u=%2F')
        sleep(5)

        # Retrieve login info from local file
        login = open('/Users/starplatinum87/Google Drive/hisoka/imdb.txt', 'r').read()
        login = login.split('\n')[0:2]

        # Enter email and password on login page
        self.driver.find_element_by_xpath('//*[@id="ap_email"]').send_keys(login[0]) # Enter your own login info
        self.driver.find_element_by_xpath('//*[@id="ap_password"]').send_keys(login[1]) # Enter your own login info
        self.driver.find_element_by_xpath('//*[@id="signInSubmit"]').click()
        sleep(7)

        # Go to MOVIEmeter page 
        # self.driver.get('https://pro.imdb.com/inproduction?ref_=hm_reel_mm_all#sort=ranking') # Skip clicks and go directly to page
        self.driver.find_element_by_xpath('//*[@id="meter_type_selections"]/li[2]/a').click()
        self.driver.find_element_by_xpath('//*[@id="meter_headshots"]/div[2]/div[2]/a').click()
        sleep(10)

        # Filter movies on MOVIEmeter page
        self.driver.find_element_by_xpath('//*[@id="type_movie"]').click() # Click Movie checkbox
        self.driver.find_element_by_xpath('//*[@id="status_RELEASED"]').click() # Click Released checkbox
        self.driver.find_element_by_xpath('//*[@id="year_yearMin"]').send_keys('2010') # Set minimum release year to 2010
        self.driver.find_element_by_xpath('//*[@id="year_yearMax"]').send_keys('2018') # Set max release year to 2018
        self.driver.find_element_by_xpath('//*[@id="budget_budgetMin"]').send_keys('0.1') # Set minimum budget to $100k
        self.driver.find_element_by_xpath('//*[@id="gross_grossMin"]').send_keys('0.1') # Set minimum US gross to $100k
        self.driver.find_element_by_xpath('//*[@id="country_US"]').click() # Click United States for Country
        self.driver.find_element_by_xpath('//*[@id="gross"]/ul/li[11]/span/a').click() # Click Go to filter
        sleep(12)

        # Scroll until all films are present on the page
        # scrollHeight is a DOM attribute of the current maximum height of the page
        # last_height = self.driver.execute_script("return document.body.scrollHeight") # execute JS to get current max height
        # while True:
        #     self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # execute JS to scroll to current max height
        #     sleep(7) # sleep to wait for server response
        #     new_height = self.driver.execute_script("return document.body.scrollHeight") 
        #     if new_height == last_height:
        #         break 
        #     last_height = new_height
        #     sleep(1.2)

        # Continue scrolling until we've reached the final entry
        self.driver.get('https://pro.imdb.com/inproduction?ref_=hm_reel_mm_all#type=movie&status=RELEASED&country=US&year=2010-2018&budget=0.1-&gross=0.1-&sort=ranking')
        results_selector = Selector(text=self.driver.page_source) # scrapy selector to extract no. of results from DOM
        results_total = results_selector.xpath('//*[@id="title"]/div[1]/div/span[1]/span[1]/text()').extract() # get no. of results
        results_total = results_total[0].replace(',','') # change results total from list to single string, remove comma
        final_film_xpath = '//*[@id="results"]/ul/li[' + results_total + ']' # xpath for final film entry  
        count = 50
        attempt = 1
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # scroll to bottom of page
            try:
                WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.XPATH, '//*[@id="results"]/ul/li[' + str(count) +']'))) # try to get the xpath indicating a completed scroll for 20 seconds
                logging.debug('Scroll 1: %s Getting %sth result.' % (str(attempt), str(count))) # log scroll attempts as they come in
            except Exception as exp:
                if results_selector.xpath(final_film_xpath).extract(): # check if the exception is because we've successfully scrolled to the end
                    print('Page scrolling completed successfully!') # if so print completed message
                    logging.debug('Page scrolling completed successfully!') # log this result
                    break
                else:
                    print(exp)
                    logging.debug(exp) # log this result
                    break
            count += 25 # update count, as each page update returns 25 new entries
            attempt += 1 # update attempt count

        # Give page source acquired by Selenium to Scrapy selector
        new_source = self.driver.page_source # Very important! Need to use the updated page source after scrolling the page above. 
        # self.driver.refresh # another option to get the latest page source
        # driver.get('https://pro.imdb.com/inproduction?ref_=hm_reel_mm_all#type=movie&status=RELEASED&country=US&year=2010-2018&budget=0.1-&gross=0.1-&sort=ranking') # yet another option, get specific query URL
        scrapy_selector = Selector(text=new_source)

        # Get list of film titles
        titles = scrapy_selector.xpath('//*[@id="results"]/ul/li/ul/li[1]/span/a/text()').extract()

        # Get MM budget on results page. Will use to filter titles that have no budget with the '&nbsp;' instead of dollar amount
        budgets = scrapy_selector.xpath('//*[@id="results"]/ul/li/span[2]/text()').extract()

        # Get film page URLs
        film_page_urls = scrapy_selector.xpath('//*[@id="results"]/ul/li/ul/li[1]/span/a/@href').extract()

        # Get Directors
        directors = scrapy_selector.xpath('//*[@id="results"]/ul/li/ul/li[3]/span[1]/a/text()').extract()

        # Get Director URLs
        director_page_urls = scrapy_selector.xpath('//*[@id="results"]/ul/li/ul/li[3]/span[1]/a/@href').extract()


        # Create an OrderedDict of tuples of the scraped data so pandas df preserves column order
        film_list_tuples =  (('titles', titles), 
                    ('budgets', budgets), 
                    ('film_page_urls', film_page_urls), 
                    ('directors', directors),
                    ('director_page_urls',  director_page_urls))
        film_list_dict = OrderedDict(film_list_tuples)

        # Use pandas to put data into a csv
        film_df = pd.DataFrame(film_list_dict)
        film_df.to_csv('/Users/starplatinum87/Google Drive/DATA_SCIENCE/Projects/02_Film_ROI/film_roi/film_roi_list.csv')

        # Pickle lists just in case
        film_list_names = ['titles', 'budgets', 'film_page_urls', 'directors', 'director_page_urls']
        films = zip(titles, budgets, film_page_urls, directors, director_page_urls)
        film_lists = list(films) # Turn zip into list for pickle and logging
        count = 0
        for data in film_lists:
            pickle_out = open(film_list_names[count] + '.pickle', 'wb')
            pickle.dump(data, pickle_out)
            pickle_out.close()
            count += 1

        # Log number of entries in each data structure
        logging.debug('films: %s entries', len(film_lists))
        logging.debug('titles: %s entries', len(titles))
        logging.debug('budgets: %s entries', len(budgets))
        logging.debug('film_page_urls: %s entries', len(film_page_urls))
        logging.debug('directors: %s entries', len(directors))
        logging.debug('director_page_urls: %s entries', len(director_page_urls))

        # Export data to csv using scrapy item feeds
        # At the terminal input `>> scrapy crawl <spider_name> -o <output_file>.csv/json/jl` to generate the output file
        for item in films:
            film_export = {
                'titles': item[0],
                'budgets': item[1],
                'film_page_urls': item[2],
                'directors': item[3],
                'director_page_urls': item[4]
            }
            yield film_export

        self.driver.close()
        