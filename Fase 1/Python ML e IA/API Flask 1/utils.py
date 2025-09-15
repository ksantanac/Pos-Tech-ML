import requests

from bs4 import BeautifulSoup
from flask import jsonify

def get_title(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string.strip()

        return jsonify({"title": title, "url": url})
    except Exception as e:
        return jsonify({"error": e})
    

