import re
import datetime
from datetime import timedelta

def get_last_items(db, hours=12, field="date", drop_new_collections=True):
    """ return all items which were made at the last given hours """
    
    # setup times
    end = datetime.datetime.now()
    start = end - timedelta(hours=hours)
    
    items = dict()
    for collection_name in db.list_collection_names():
        collection = db[collection_name]
        if not is_new_collection(collection):
            items[collection_name] = list(collection.find({field: {"$lt": end, "$gte": start}}))
    return items

def is_new_collection(collection, hours=12, field="date"):
    """ return True if all items in a collection were made at the last given hours """
    dt = datetime.datetime.now() - timedelta(hours=hours)
    if collection.find_one({field : {"$lt": dt}}):
        return False
    return True

def job_to_string(job):
    s = job["title"] + "\n" + job["url"]
    return s

def jobs_to_string(jobs):
    seperator = "\n\n"
    jobs_lst = [job for collection in jobs for job in jobs[collection]]
    msg = seperator.join([job_to_string(job) for job in jobs_lst])
    return msg
