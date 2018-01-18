# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html
import re
import scrapy
from scrapy.loader.processors import MapCompose


def convert(value):
    if value == '�|鱼':
        value = "鮸鱼"
    if value == '�崭�':
        value = "椪柑"
    return value


class SpiderpriceItem(scrapy.Item):
    # define the fields for your item here like:
    dates = scrapy.Field()
    type = scrapy.Field()
    product = scrapy.Field(input_processor=MapCompose(convert))
    price = scrapy.Field()
    market = scrapy.Field()

    def get_sql(self):
        sql = """insert into chartsite.`农产品价格行情数据库`(`类别`, `产品`, `价格`, `市场`, `日期`)
                VALUES ('{0}', '{1}', '{2}', '{3}', '{4}') ON duplicate KEY UPDATE `价格`= VALUES(`价格`)"""
        sql = sql.format(self['type'], self['product'], self['price'], self['market'], self['dates'])
        return sql
