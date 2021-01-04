import json
import datetime
import requests
from bs4 import BeautifulSoup
from scrapers import utils

import logging
logger = logging.getLogger(__name__)

def log_wrapper(func):
    """ decorator to log methods """
    def wrapper(*args, **kwargs):
        logger.debug(f"{func.__name__}({args}, {kwargs})")
        return func(*args, **kwargs)
    return wrapper
    

class Job:

    @log_wrapper
    def scrape(self, limit=-1):

        jobs_urls = self._get_all_jobs_urls()

        if limit != -1 and limit < len(jobs_urls):
            jobs_urls = jobs_urls[:limit]

        # extract data from every job link
        jobs = []
        for url in jobs_urls:
            job = self._scrape_job(url)
            jobs.append(job)

        return jobs
    
    @log_wrapper
    def get_new_jobs(self, collection):
        """ return list of new jobs - jobs with url who isnt in given collection """
        
        jobs_urls = self._get_all_jobs_urls()
        collection_urls = collection.find({}, {"_id": 0 ,"url": 1})
        collection_urls = [d["url"] for d in collection_urls]

        # leave only new urls
        jobs_urls = list(set(jobs_urls) - set(collection_urls))

        # scrape new jobs from new urls
        jobs = []
        for url in jobs_urls:
            job = self._scrape_job(url)
            jobs.append(job)
        
        return jobs

    def _scrape_job(self, url):
        pass

    def _get_all_jobs_urls(self):
        pass


class Amdocs(Job):

    @staticmethod
    @log_wrapper
    def _scrape_job(url):
        
        # init
        job = dict()
        request = requests.get(url)
        soup = BeautifulSoup(request.text, "html.parser")

        job["date"] = datetime.datetime.now()
        job["url"] = url
        job["title"] = soup.find("span", {"itemprop":"title"}).text.strip()
        job["html_description"] = str(soup.find_all("div", class_="col-xs-12 fontalign-left")[1])
        url_list = [e for e in url.split("/") if e]
        job["job_id"] = url_list[-1]
        job["location"] = url_list[-2].split("-")[0]

        return job
    
    @log_wrapper
    def _get_all_jobs_urls(self):

        base_url = r"https://jobs.amdocs.com/search/?q=&locationsearch=israel&startrow="
        num_of_jobs = self._num_of_jobs()
        
        jobs_urls = []
        for i in range(0, num_of_jobs, 15):
            url = base_url + str(i)
            links = utils.get_all_links(url)
            links = list(set(links))
            links = [link for link in links if link.startswith(r"/job/")]
            jobs_urls += links

        prefix = r"https://jobs.amdocs.com"
        jobs_urls = [prefix+url for url in jobs_urls]
        
        return jobs_urls

    @staticmethod
    @log_wrapper
    def _num_of_jobs():
        url = r"https://jobs.amdocs.com/search/?createNewAlert=false&q=&locationsearch=israel"
        request = requests.get(url)
        soup = BeautifulSoup(request.text, "html.parser")
        num_of_jobs = int(soup.find("span", class_="paginationLabel").find_all("b")[1].text)
        return num_of_jobs


class Checkpoint(Job):

    @staticmethod
    @log_wrapper
    def _scrape_job(url):
        
        # init
        job = dict()
        request = requests.get(url)
        soup = BeautifulSoup(request.text, "html.parser")

        job["date"] = datetime.datetime.now()
        job["url"] = url
        job["html_description"] = str(soup.find("div", {"id":"jobOrderInfo"}))
        
        job_header = soup.find("div", {"id":"jobOrderHeader"})
        job["title"] = job_header.find("h1").text.strip()
        job["location"] = job_header.find("p").text.strip()
        job["job_id"] = job_header.find_all("p")[1].text.split("Job Id:")[1].strip()

        return job
    
    @log_wrapper
    def _get_all_jobs_urls(self):

        base_url = r"https://careers.checkpoint.com/?q=&module=cpcareers&a=search&fa%5B%5D=country_ss%3AIsrael&sort=&start="
        num_of_jobs = self._num_of_jobs()
        
        jobs_urls = []
        url_start = r"https://careers.checkpoint.com/index.php?m=cpcareers&a=show&jobOrderID="
        for i in range(0, num_of_jobs, 10):
            url = base_url + str(i)
            links = utils.get_all_links(url)
            links = list(set(links))
            links = [link for link in links if link.startswith(url_start)]
            jobs_urls += links
        
        return jobs_urls

    @staticmethod
    @log_wrapper
    def _num_of_jobs():
        url = r"https://careers.checkpoint.com/?q=&module=cpcareers&a=search&fa%5B%5D=country_ss%3AIsrael&sort="
        request = requests.get(url)
        soup = BeautifulSoup(request.text, "html.parser")
        num_of_jobs = int(soup.find("span", {"id":"resSize"}).text)
        return num_of_jobs


class Apple(Job):

    @staticmethod
    @log_wrapper
    def _scrape_job(url):

        # init
        job = dict()
        request = requests.get(url)
        soup = BeautifulSoup(request.text, "html.parser")

        job["date"] = datetime.datetime.now()
        job["url"] = url
        job["html_description"] = str(soup.find("div", {"itemprop":"description"}))
        job["title"] = soup.find("h1", {"itemprop":"title"}).text
        job["location"] = soup.find("div", {"id":"job-location-name"}).text
        job["job_date"] = soup.find("time", {"id":"jobPostDate"}).text
        job["job_id"] = soup.find("strong", {"id":"jobNumber"}).text
        job["team"] = soup.find("div", {"id":"job-team-name"}).text

        return job
    
    @log_wrapper
    def _get_all_jobs_urls(self):

        base_url = r"https://jobs.apple.com/en-il/search?location=israel-ISR&page="
        num_of_pages = self._num_of_job_pages()
        
        jobs_urls = []
        for page_i in range(1, num_of_pages+1):
            url = base_url + str(page_i)
            links = utils.get_all_links(url)
            links = list(set(links))
            links = [link for link in links if link.startswith(r"/en-il/details/")]
            jobs_urls += links
        
        url_start = r"https://jobs.apple.com"
        jobs_urls = [url_start+url for url in jobs_urls]
        return jobs_urls

    @staticmethod
    @log_wrapper
    def _num_of_job_pages():
        url = r"https://jobs.apple.com/en-il/search?location=israel-ISR&page=1"
        request = requests.get(url)
        soup = BeautifulSoup(request.text, "html.parser")
        max_page = int(soup.find_all("span", class_="pageNumber")[1].text)
        return max_page
