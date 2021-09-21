from celery.app.utils import Settings
from web_crawler import celery, app
import uuid
import logging 
import redis
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import CrawlSpider

def create_job_id():
    job_id = uuid.uuid4()
    return job_id

def create_job(urls, workers):
    """This function takes in urls and workers, submits a job and return a job id"""
    print(urls)
    print(workers)
    job_id = create_job_id()
    submit_job(job_id, urls, workers)
    return job_id

class crawlImages(scrapy.Spider):
    def parse(self, response): # When writing crawl spider rules, avoid using parse as callback, since the CrawlSpider uses the parse method itself to implement its logic. So if you override the parse method, the crawl spider will no longer work.
        for request_or_item in CrawlSpider.parse(self, response):
            if isinstance(request_or_item, scrapy.Request):
                request_or_item = request_or_item.replace(meta = {'start_url': response.meta['start_url']})
            yield request_or_item
    def make_requests_from_url(self, url):
        """A method that receives a URL and returns a Request object (or a list of Request objects) to scrape. 
        This method is used to construct the initial requests in the start_requests() method, 
        and is typically used to convert urls to requests.
        """
        return scrapy.Request(url, dont_filter=True, meta = {'start_url': url})
    def parse(self, response):
        raw_image_urls = response.xpath(".//img/@src").getall()
        clean_image_urls = []
        for img_url in raw_image_urls:
            clean_image_urls.append(response.urljoin(img_url))
        yield {'image_urls': clean_image_urls, 
              'start_url': response.meta['start_url']}

def run_scrapy(job_id, start_urls=['https://www.nytimes.com/ca/']):
    """This function should run Scrapy"""
    process = CrawlerProcess({
    'USER_AGENT': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36"
    })

    process.crawl(crawlImages, name = job_id, start_urls =start_urls)
    process.start()
    process.join()

class RedisPipeline(object):  
    @classmethod 
    def from_crawler(cls, crawler): 
        return cls() 

    def open_spider(self, spider): 
        self.client = redis.Redis(host='localhost', port=6379, db=0)

    def close_spider(self, spider): 
            pass

    def process_item(self, item, spider): 
        start_url = item['start_url']
        self.client.lpush(start_url, *item['image_urls'])
        return item

ITEM_PIPELINES = {
   RedisPipeline: 600,
}

@celery.task
def submit_job(job_id):
    """Background task to submit a web crawler job."""
    with app.app_context():
        pass

@celery.task(bind=True)
def run_scraper_task(job_id, urls):
    """Background task that runs a long function with progress reports."""
    process = CrawlerProcess({
    'USER_AGENT': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36", 
    "ITEM_PIPELINES": ITEM_PIPELINES})

    process.crawl(crawlImages, name = job_id, start_urls = urls)
    process.start()
    process.join()
