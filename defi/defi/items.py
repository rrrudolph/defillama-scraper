# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst

class Protocol(scrapy.Item):
    
    name = scrapy.Field(output_processor=TakeFirst())
    address = scrapy.Field(output_processor=TakeFirst())
    chains = scrapy.Field(output_processor=TakeFirst())
    twitter = scrapy.Field(output_processor=TakeFirst())
    chain_tvls = scrapy.Field(output_processor=TakeFirst())
    tvl = scrapy.Field(output_processor=TakeFirst())