import requests
from bs4 import BeautifulSoup

def get_all_links(url):
    """ get all hrefs form <a> tags, from given url """
    request = requests.get(url)
    soup = BeautifulSoup(request.text, "html.parser")
    links = [a_tag.get("href") for a_tag in soup.find_all("a")]
    links = [link for link in links if link is not None]
    return links