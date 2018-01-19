# -*- coding: utf-8 -*-
import json
import datetime
from urllib.parse import urlencode

from scrapy import Request
from scrapy_redis.spiders import RedisSpider
from SpiderPrice.items import SpiderpriceItem
from SpiderPrice.settings import STARTDAY, TIMEDELTA


class AgripriceSpider(RedisSpider):

    name = 'agriprice'
    redis_key = "agriprice:start_urls"
    allowed_domains = ['nc.mofcom.gov.cn']
    start_urls = ['http://nc.mofcom.gov.cn/channel/jghq2017/price_list.shtml']

    def __init__(self, *args, **kwargs):
        indexdata = open("index/index.json", 'r', encoding='utf-8').read()
        self.index = json.loads(indexdata)
        self.cookie_dict = {}
        self.querystring = {"par_craft_index": "",  # 类别编号
                            "craft_index": "",  # 产品编号
                            "startTime": "",
                            "endTime": "",
                            "par_p_index": "",  # 省份编号
                            "p_index": "",  # 市场编号
                            "keyword": "",
                            }

        super(AgripriceSpider, self).__init__()

    def parse(self, response):
        start = datetime.datetime.strptime(STARTDAY, '%Y-%m-%d').date()
        end = datetime.date.today()
        interval = int(int((end - start).days) / TIMEDELTA) + 1
        ninedays = datetime.timedelta(days=TIMEDELTA)
        for i in range(0, interval):
            start_day = (start + ninedays * i)
            if i == interval - 1:
                end_day = datetime.date.today()
            else:
                end_day = start_day + ninedays
            self.querystring["startTime"] = start_day
            self.querystring["endTime"] = end_day

            for item in self.index:
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
                        callback=self.parse_two,
                        meta={"category": category},
                        cookies=self.cookie_dict
                    )

    def parse_two(self, response):
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
                callback=self.parse_three,
                meta={"category": response.meta.get("category", "")}
            )

    def parse_three(self, response):
        reports = response.css(".table-01.mt30 tr")
        for report in reports[1:]:
            items = SpiderpriceItem()
            items["dates"] = report.css("td:nth-child(1)::text").extract_first()
            items["product"] = report.css("td:nth-child(2) span::text").extract_first()
            items["price"] = report.css("td:nth-child(3) span::text").extract_first()
            items["market"] = report.css("td:nth-child(4) a::text").extract_first()
            items["type"] = response.meta.get("category", "")
            yield items
