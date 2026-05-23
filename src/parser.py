import requests
from bs4 import BeautifulSoup

from pyVinted import Vinted

vinted = Vinted()


def get_page_data(url):

    items = vinted.items.search(url, 10, 1)
    x = []
    for item in items:
        x.append({'title': item.title, 'url': item.url, 'price': item.price})
    return x

