from pathlib import Path
import inspect
import json

import pymongo
from pymongo import MongoClient

import logging
from logging import handlers

from scrapers import scrapers
import twitter
import utils

def create_logger(logs_dir):
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # create file handler
    file_handler = handlers.RotatingFileHandler(Path(logs_dir) / Path("log.log"),
                                                        maxBytes=10**6, 
                                                        backupCount=5)
    file_handler.setLevel(logging.DEBUG)

    # create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # set format
    formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(name)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def read_config_file(config_file_path=None):

    curr_dir = Path(__file__).parent.absolute()

    # default config path
    if config_file_path is None:
        config_file_path = curr_dir / Path("config.json")
    
    with open(config_file_path) as f:
        config = json.load(f)
    return config

def update_db(db):
    """ scrape all job sites, and insert new jobs only into DB """
    
    def get_classes(module):
        """ get all classes defined in given module """
        return [name for name in dir(module) if inspect.isclass(getattr(module, name))]

    # get all scrapers
    scrapers_classes = get_classes(scrapers)
    drop_classes = ["Job", "BeautifulSoup"]
    scrapers_classes = list(set(scrapers_classes) - set(drop_classes))

    # update collection for each company
    for scraper_name in scrapers_classes:
        logger.info(f"scraping {scraper_name}")
        collection = db[scraper_name.lower()]
        scraper = getattr(scrapers, scraper_name)()
        
        try:
            new_jobs = scraper.get_new_jobs(collection)
        except Exception:
            logger.exception(f"couldnt get new jobs for {scraper_name}")
        else:
            if new_jobs:
                logger.info(f"{scraper_name} - {len(new_jobs)} new jobs")
                collection.insert_many(new_jobs)

if __name__ == "__main__":

    # read config file
    curr_dir = Path(__file__).parent.absolute()
    config_file = curr_dir / Path("config.json")
    config = read_config_file(config_file)

    # setup logger
    logger = create_logger(config["logs_directory"])
    
    # setup mongo
    client = MongoClient('localhost', 27017)
    db = client["jobs"]

    update_db(db)
    
    # getting jobs from the last hours
    companies = utils.get_last_items(db)
    num_of_jobs = sum(len(companies[c]) for c in companies)
    logger.info(f"found {num_of_jobs} new jobs")

    # filter jobs that were already tweeted at the last 48 hours
    api = twitter.get_twitter_api(config["twitter"]["consumer_key"], 
                                config["twitter"]["consumer_secret"],
                                config["twitter"]["access_token"], 
                                config["twitter"]["access_secret"])
    filtered_jobs = twitter.filter_twitter_jobs(api, companies, hours=48)
    
    # tweet new jobs
    num_of_filtered = sum([len(filtered_jobs[company]) for company in filtered_jobs])
    logger.info(f"{num_of_filtered} new twitter jobs")
    twitter.tweet_jobs(api, filtered_jobs)
