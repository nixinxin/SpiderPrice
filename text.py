import redis
import time

pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)
r = redis.Redis(connection_pool=pool)

r.lpush("agriprice:start_urls", "http://nc.mofcom.gov.cn/channel/jghq2017/price_list.shtml")
print(r.lrange('agriprice:start_urls', 0, -1))

