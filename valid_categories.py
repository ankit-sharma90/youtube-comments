import requests
import json

def valid_categories():
    parameters = {
        "part": "snippet",
        "regionCode": "US",
        "key": "AIzaSyBcAFV0eSetpir285H_cQGt1-c3OFk60Nc"
    }

    vc_mapping = {}

    vid_categories_response = requests.get("https://www.googleapis.com/youtube/v3/videoCategories", params=parameters)

    for category in vid_categories_response.json()['items']:
        vc_title = category['snippet']['title']
        vc_id = category['id']

        if is_category_valid(vc_id):
            vc_mapping[vc_title] = vc_id

    return vc_mapping

def is_category_valid(id):
    parameters = {
        "part": "snippet, statistics",
        "regionCode": "US",
        "key": "AIzaSyBcAFV0eSetpir285H_cQGt1-c3OFk60Nc",
        "chart": "mostPopular",
        "videoCategoryId": id
    }

    videos_response = requests.get("https://www.googleapis.com/youtube/v3/videos", params=parameters)

    try:
        videos_response.json()['etag']
        return True
    except:
        return False