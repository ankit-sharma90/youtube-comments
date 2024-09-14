#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Feb  6 20:51:31 2021

@author: ankit
"""
import requests
import os
from flask import Flask, render_template, request
from valid_categories import valid_categories
API_KEY = os.environ.get('YOUTUBE_API_KEY')

def get_video_data(vc_selected_id):
    data = {}
    parameters = {
        "part": "snippet, statistics",
        "regionCode": "US",
        "key": API_KEY,
        "chart": "mostPopular",
        "videoCategoryId": vc_selected_id
    }

    videos_response = requests.get("https://www.googleapis.com/youtube/v3/videos", params=parameters)

    for video in videos_response.json()['items']:
        video_id = video['id']
        video_title = video['snippet']['title']
        video_views = int(video['statistics']['viewCount'])
        data[video_id] = {
            "title": video_title,
            "views": video_views,
            "comment_likes": 0,  # Initialize with default values
            "comment_content": "No comments available",  # Initialize with default values
            "video_url": f'https://www.youtube.com/watch?v={video_id}'
        }

        comment_parameters = {
            "part": 'snippet',
            "regionCode": 'US',
            "key": API_KEY,
            "order": 'relevance',
            "maxResults": 1,
            'videoId': video_id
        }

        comments_response = requests.get("https://www.googleapis.com/youtube/v3/commentThreads",
                                         params=comment_parameters)
        comments_data = comments_response.json()

        if 'items' in comments_data and comments_data['items']:
            top_comment = comments_data['items'][0]
            data[video_id]['comment_likes'] = int(top_comment['snippet']['topLevelComment']['snippet']['likeCount'])
            data[video_id]['comment_content'] = top_comment['snippet']['topLevelComment']['snippet']['textDisplay']

    return data

data = {}
vc_mapping = valid_categories()

app = Flask(__name__)

@app.route('/', methods=['GET','POST'])
def index():
    data = {}
    try:
        vc_selected = request.form["vc_selected"]
        vc_selected_id = vc_mapping[vc_selected]
        data = get_video_data(vc_selected_id)
    except KeyError:
        # This will catch both KeyError from form access and from vc_mapping
        pass
    except Exception:
        # This will catch any other unexpected exceptions
        pass
    return render_template('index.html', data=data, video_categories=vc_mapping)