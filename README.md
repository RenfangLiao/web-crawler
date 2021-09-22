# web-crawler
This repository is based on https://github.com/miguelgrinberg/flask-celery-example  
The framework consists flask and redis.  
The web crawler function is using scrapy.  
# How to run the application
git clone https://github.com/RenfangLiao/web-crawler.git  
cd web-crawler  
docker build -t crawler_test .  
docker run --rm -it -p 8080:8080 crawler_test  
# design decisions
I tried to find a balance between "follow common practice" and "keep it simple" (don't over complicate things).  
I first considered using celery to manage the queue and help me check status, but it turned out to be unnecessary. I started python process for each of the start url, because scrapy doesn't allow me to check the status of each start_url (or I didn't find it) if there are more than one start_url in a spider.  
Instead, I used redis to store the start_url status along with results. 
# possible improvements
- workers definition
- scrapy settings file
- logging
- scalability

