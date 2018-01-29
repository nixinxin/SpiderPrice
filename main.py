from scrapy.cmdline import execute

import redis

from SpiderPrice.settings import MYSQL_HOST
from SpiderPrice.spiders.agriprice import AgripriceSpider


pool = redis.ConnectionPool(host=MYSQL_HOST, port=6379, decode_responses=True)   # host是redis主机，需要redis服务端和客户端都起着 redis默认端口是6379
conn = redis.Redis(connection_pool=pool)

# if not conn.exists(AgripriceSpider.redis_key):
conn.lpush(AgripriceSpider.redis_key, AgripriceSpider.start_urls[0])

execute(['scrapy', 'crawl', 'agriprice'])