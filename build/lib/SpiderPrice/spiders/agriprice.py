# -*- coding: utf-8 -*-
import json
import os
import time
import datetime

import re
import pickle

from urllib.parse import urlencode
from urllib.request import urlparse

import scrapy
from scrapy import Request
from scrapy.loader import ItemLoader
from SpiderPrice.items import SpiderpriceItem
from SpiderPrice.settings import BASE_DIIR


class AgripriceSpider(scrapy.Spider):
    name = 'agriprice'
    allowed_domains = ['nc.mofcom.gov.cn']
    start_urls = ['http://nc.mofcom.gov.cn/channel/jghq2017/price_list.shtml']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.index = json.loads(open(os.path.join(BASE_DIIR, "index.json"), 'r', encoding='utf-8').read())
        self.cookie_dict = {}
        self.querystring = {"par_craft_index": "",  # 类别编号
                            "craft_index": "",  # 产品编号
                            "startTime": "",
                            "endTime": "",
                            "par_p_index": "",  # 省份编号
                            "p_index": "",  # 市场编号
                            "keyword": "",
                            }

    def start_requests(self):
        from selenium import webdriver
        browser = webdriver.PhantomJS()
        browser.get(self.start_urls[0])
        time.sleep(1)
        cookies = browser.get_cookies()
        for cookie in cookies:
            # 写入文件
            f = open(os.path.join(BASE_DIIR, "tools", "Cookies.txt"), 'wb')
            pickle.dump(cookie, f)
            f.close()
            self.cookie_dict[cookie['name']] = cookie['value']
        browser.close()

        index = self.index
        today = datetime.date.today()
        start_day = today - datetime.timedelta(days=2)
        self.querystring["startTime"] = start_day
        self.querystring["endTime"] = today
        for item in index:
            category_id = item['id']
            category = item['product']
            self.querystring["par_craft_index"] = category_id
            for product in item['sub_value'].keys():
                product_id = item['sub_value'][product]
                self.querystring["craft_index"] = product_id
                parses = urlencode(self.querystring)
                url = self.start_urls[0] + "?" + parses

                yield Request(
                    url=url,
                    dont_filter=True,
                    callback=self.parse,
                    meta={"category": category},
                    cookies=self.cookie_dict
                )

    def parse(self, response):
        try:
            all_page = int(response.css(".table-01.mt30 + script::text").extract_first().split(";")[0].split("=")[-1].strip())
        except:
            all_page = 0
        if all_page > 3:
            all_page = 1
        for i in range(1, int(all_page) + 1):
            self.querystring['page'] = str(i)
            parses = urlencode(self.querystring)
            url = self.start_urls[0] + "?" + parses
            yield Request(
                url=url,
                dont_filter=True,
                callback=self.parse_detail,
                meta={"category": response.meta.get("category", "")}
            )

    def parse_detail(self, response):
        reports = response.css(".table-01.mt30 tr")
        for report in reports[1:]:
            items = SpiderpriceItem()
            items["dates"] = report.css("td:nth-child(1)::text").extract_first()
            items["product"] = report.css("td:nth-child(2) span::text").extract_first()
            items["price"] = report.css("td:nth-child(3) span::text").extract_first()
            items["market"] = report.css("td:nth-child(4) a::text").extract_first()
            items["type"] = response.meta.get("category", "")
            yield items
