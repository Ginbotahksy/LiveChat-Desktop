import requests
import json
import re

url = "https://x.com/SpaceX/status/1768273641756557454"
# Extract ID
match = re.search(r'(?:twitter\.com|x\.com)\/[^\/]+\/status\/(\d+)', url)
if match:
    tweet_id = match.group(1)
    # try fxtwitter API
    try:
        api_url = f"https://api.fxtwitter.com/status/{tweet_id}"
        resp = requests.get(api_url, timeout=5)
        print("fxtwitter:", resp.text)
    except Exception as e:
        print("fxtwitter err:", e)
        
    # try vxtwitter API
    try:
        api_url = f"https://api.vxtwitter.com/status/{tweet_id}"
        resp = requests.get(api_url, timeout=5)
        print("vxtwitter:", resp.text)
    except Exception as e:
        print("vxtwitter err:", e)
