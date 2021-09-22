import unittest
import redis
import requests
import subprocess
import time
import os
# note
# you need to run FLASK_APP='web_crawler:application'
# then go to web_crawler_img/server dir and run 'FLASK RUN'
# then 'redis-server'
# then go to the repo's root dir run 'python -m unittest'
# helper
def free_up_redis():
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    redis_client.flushdb()

class TestWebCrawler(unittest.TestCase):
    def setUp(self):
        free_up_redis()
        #os.environ['FLASK_APP'] = 'web_crawler:application'
        #self.flask_process = subprocess.Popen(['flask', 'run'], cwd='./web_crawler_img/server/')

    def tearDown(self):
        #self.flask_process.terminate()
        pass
    def test_one_job_multiple_urls(self):
        r_post_job = requests.post('http://127.0.0.1:5000/jobs', json={"urls":["https://4chan.org/", 'https://golang.org/'], "workers":3})
        job_id = r_post_job.json()['job_id']
        while True:
            r_check_result = requests.get('http://127.0.0.1:5000/jobs/{}/result'.format(job_id))
            r_check_status = requests.get('http://127.0.0.1:5000/jobs/{}/status'.format(job_id))
            status = r_check_status.json()
            print(status)
            if status['in_progress'] > 0 :
                self.assertEqual(r_check_result.status_code, 404)
                time.sleep(2)
            else:
                self.assertEqual(r_check_status.json()['completed'], 2)
                break
        r_check_result = requests.get('http://127.0.0.1:5000/jobs/{}/result'.format(job_id))
        r_check_result.json()
        self.assertEqual(r_check_result.status_code, 200)
    
    def test_two_jobs_different_workers(self):
        r_post_job_1 = requests.post('http://127.0.0.1:5000/jobs', json={"urls":['https://golang.org/']})
        job_id_1 = r_post_job_1.json()['job_id']
        r_post_job_2 = requests.post('http://127.0.0.1:5000/jobs', json={"urls":['https://www.nytimes.com/ca/', 'https://www.bbc.com/'], "workers": 4})
        job_id_2 = r_post_job_2.json()['job_id']
        while True:
            r_check_status_1 = requests.get('http://127.0.0.1:5000/jobs/{}/status'.format(job_id_1))
            status_1 = r_check_status_1.json()
            r_check_status_2 = requests.get('http://127.0.0.1:5000/jobs/{}/status'.format(job_id_2))
            status_2 = r_check_status_2.json()
            print(job_id_1, status_1)
            print(job_id_2, status_2)
            if status_1['in_progress'] > 0 :
                time.sleep(2)
            elif status_2['in_progress'] > 0 :
                time.sleep(2)
            else:
                break
        r_check_result_1 = requests.get('http://127.0.0.1:5000/jobs/{}/result'.format(job_id_1))
        self.assertEqual(r_check_result_1.status_code, 200)
        r_check_result_2 = requests.get('http://127.0.0.1:5000/jobs/{}/result'.format(job_id_2))
        self.assertEqual(r_check_result_2.status_code, 200)

            
