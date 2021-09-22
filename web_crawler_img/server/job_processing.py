import uuid
import redis
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from urllib.parse import urlparse
from pathlib import Path
from multiprocessing import Process
from flask import abort
def create_job_id():
    job_id = str(uuid.uuid4())
    return job_id

def create_job(urls, workers):
    """This function takes in urls and workers, submits a job and return a job id"""
    print(urls)
    print(workers)
    job_id = create_job_id()
    submit_jobs(job_id, urls, workers)
    return job_id

class crawlImages(CrawlSpider):
    rules = (
        # Extract and follow all links!
        Rule(link_extractor = LinkExtractor(), callback='parse', follow=True, process_request='process_request'),
    )     

    def make_requests_from_url(self, url):
        """A method that receives a URL and returns a Request object (or a list of Request objects) to scrape. 
        This method is used to construct the initial requests in the start_requests() method, 
        and is typically used to convert urls to requests.
        """
        return scrapy.Request(url, dont_filter=True, meta = {'start_url': url})
    
    def parse(self, response):
        self.log('crawling: {}'.format(response.url))
        raw_image_urls = response.xpath(".//img/@src").getall()
        clean_image_urls = []
        for img_url in raw_image_urls:
            clean_image_urls.append(response.urljoin(img_url))
        yield {'image_urls': clean_image_urls, 
              'start_url': response.meta['start_url']}

    def process_request(self, request, originating_response):
        request.meta['start_url'] = originating_response.meta['start_url']
        return request

class RedisPipeline(object):  
    @classmethod 
    def from_crawler(cls, crawler): 
        return cls() 

    def open_spider(self, spider): 
        self.client = redis.Redis(host='localhost', port=6379, db=0)

    def close_spider(self, spider): 
        pass

    def process_item(self, item, spider): 
        key = 'result_'+item['start_url']
        self.client.lpush(key, *item['image_urls'])
        return item

ITEM_PIPELINES = {
   RedisPipeline: 600,
}
    
def run_scraper_task(job_id, url, workers):
    """Background task that craw one start_url."""
    process = CrawlerProcess({
        'USER_AGENT': "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.131 Safari/537.36", 
        "ITEM_PIPELINES": ITEM_PIPELINES, 
    "DEPTH_LIMIT": 1,
    "CONCURRENT_REQUESTS": workers}, 
    )
    start_urls = [url]
    allowed_domains = [urlparse(url).netloc for url in start_urls]
    process.crawl(crawlImages, name = job_id+','+url, start_urls = start_urls, domain=allowed_domains)
    process.start()
    process.join()
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    key = 'status_'+url
    redis_client.set(key, 'completed')

def submit_jobs(job_id, urls, workers):
    """Background task that run web crawler jobs."""
    client = redis.Redis(host='localhost', port=6379, db=0)
    client.lpush(job_id, *urls)
    
    for url in urls:
        key = 'status_'+url
        if client.get(key) is None:
            client.set(key, 'in_progress')
            p = Process(target=run_scraper_task, args=(job_id, url, workers))
            p.start()

def check_job_status(job_id):
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    if len(redis_client.lrange(job_id, 0, -1))==0:
        abort(404)
    urls = redis_client.lrange(job_id, 0, -1)
    inprogress_urls = 0
    completed_urls = 0
    for url in urls:
        key = 'status_'+url.decode()
        status=redis_client.get(key).decode()
        if status == 'completed':
           completed_urls+=1
        elif status == 'in_progress':
           inprogress_urls+=1
        else:
            pass
            print('unexpected status')
    response_json = {}
    response_json['completed'] = completed_urls
    response_json['in_progress'] = inprogress_urls
    return response_json

def get_job_result(job_id):
    status_json = check_job_status(job_id)
    if status_json.get('in_progress') >0:
        abort(404)
    result_json = {}
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    start_urls = redis_client.lrange(job_id, 0, -1)
    for url in start_urls:
        url = url.decode()
        key = 'result_'+url
        result=redis_client.lrange(key, 0, -1)
        # remove query part and remove duplicates
        result = list(dict.fromkeys([img_url.decode().split('?')[0] for img_url in result]))
        # check extension only keep the 
        result = [img_url for img_url in result if Path(urlparse(img_url).path).suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']]
        result_json[url] = result
    return result_json
