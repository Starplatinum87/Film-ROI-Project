# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class FilmData(scrapy.Item):
    title = scrapy.Field()
    genres = scrapy.Field()
    release = scrapy.Field()
    budget = scrapy.Field()
    openinggross = scrapy.Field()
    uscagross = scrapy.Field()
    worldgross = scrapy.Field()
    articles = scrapy.Field()
    # moviemeter = scrapy.Field()
    # url = scrapy.Field()