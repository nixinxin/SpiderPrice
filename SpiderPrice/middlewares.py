# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from fake_useragent import UserAgent

from scrapy import signals
from scrapy.responsetypes import responsetypes
from selenium import webdriver
from six.moves import queue
from twisted.internet import defer, threads
from twisted.python.failure import Failure

from tools.crawl_xici_ip import GetIP


class AgriteachSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class SpiderPriceDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    # def __init__(self):
    #     self.driver = webdriver.Chrome()
    #     self.wait = wait.WebDriverWait(self.driver, 10)
    #     super(SpiderPriceDownloaderMiddleware, self).__init__()

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        # return request
        # self.driver.get(request.url)
        # self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'body > section > div > div.w890.fl > table')))
        # time.sleep(DOWNLOAD_DELAY)
        # response = self.driver.page_source
        # 关键
        # return HtmlResponse(self.driver.current_url, status=200, body=response, request=request, encoding='utf-8')

        user = getattr(UserAgent(), 'random')
        request.headers['User-Agent'] = user
        # get_ip = GetIP()
        # request.meta["proxy"] = get_ip.get_random_ip()

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class PhantomJSDownloadHandler(object):

    def __init__(self, settings):
        self.options = settings.get('PHANTOMJS_OPTIONS', {})

        max_run = settings.get('PHANTOMJS_MAXRUN', 10)
        self.sem = defer.DeferredSemaphore(max_run)
        self.queue = queue.LifoQueue(max_run)

    @classmethod
    def from_crawler(cls, crawler):
        s = cls(crawler.settings)
        crawler.signals.connect(s._closed, signal=signals.spider_opened)
        return s

    def download_request(self, request, spider):
        """use semaphore to guard a phantomjs pool"""
        return self.sem.run(self._wait_request, request, spider)

    def _wait_request(self, request, spider):
        try:
            driver = self.queue.get_nowait()
        except queue.Empty:
            driver = webdriver.PhantomJS(**self.options)

        driver.get(request.url)
        # ghostdriver won't response when switch window until page is loaded
        dfd = threads.deferToThread(lambda: driver.switch_to.window(driver.current_window_handle))
        dfd.addCallback(self._response, driver, spider)
        return dfd

    def _response(self, _, driver, spider):
        body = driver.execute_script("return document.documentElement.innerHTML")
        if body.startswith("<head></head>"):  # cannot access response header in Selenium
            body = driver.execute_script("return document.documentElement.textContent")
        url = driver.current_url
        respcls = responsetypes.from_args(url=url, body=body[:100].encode('utf8'))
        resp = respcls(url=url, body=body, encoding="utf-8")

        response_failed = getattr(spider, "response_failed", None)
        if response_failed and callable(response_failed) and response_failed(resp, driver):
            driver.close()
            return defer.fail(Failure())
        else:
            self.queue.put(driver)
            return defer.succeed(resp)

    def _closed(self):
        while not self.queue.empty():
            driver = self.queue.get_nowait()
            driver.close()
