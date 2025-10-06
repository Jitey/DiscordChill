import feedparser
from icecream import ic

url = "https://www.example.com/rss"
feed = feedparser.parse(url)

ic(feed)