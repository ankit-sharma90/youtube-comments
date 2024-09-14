import pytest
import os
from unittest.mock import patch, MagicMock
from app import app, get_video_data
API_KEY = os.environ.get('YOUTUBE_API_KEY')

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_api_responses():
    """
    Fixture to set up mock API responses.
    """
    with patch('app.requests.get') as mock_get:
        mock_videos_response = MagicMock()
        mock_videos_response.json.return_value = {
            'items': [{
                'id': 'test_id',
                'snippet': {'title': 'Test Video'},
                'statistics': {'viewCount': '1000'}
            }]
        }

        mock_comments_response = MagicMock()
        mock_comments_response.json.return_value = {
            'items': [{
                'snippet': {
                    'topLevelComment': {
                        'snippet': {
                            'likeCount': 10,
                            'textDisplay': 'Test comment'
                        }
                    }
                }
            }]
        }

        mock_get.side_effect = [mock_videos_response, mock_comments_response]
        yield mock_get


def test_get_video_data_structure(mock_api_responses):
    """
    Test that get_video_data returns the correct data structure.
    """
    result = get_video_data('1')
    assert 'test_id' in result
    assert all(key in result['test_id'] for key in ['title', 'views', 'comment_likes', 'comment_content', 'video_url'])


def test_get_video_data_content(mock_api_responses):
    """
    Test that get_video_data returns the correct content.
    """
    result = get_video_data('1')
    assert result['test_id']['title'] == 'Test Video'
    assert result['test_id']['views'] == 1000
    assert result['test_id']['comment_likes'] == 10
    assert result['test_id']['comment_content'] == 'Test comment'
    assert result['test_id']['video_url'] == 'https://www.youtube.com/watch?v=test_id'


def test_get_video_data_api_calls(mock_api_responses):
    """
    Test that get_video_data makes the correct API calls.
    """
    get_video_data('1')

    mock_api_responses.assert_any_call(
        "https://www.googleapis.com/youtube/v3/videos",
        params={
            "part": "snippet, statistics",
            "regionCode": "US",
            "key": API_KEY,
            "chart": "mostPopular",
            "videoCategoryId": "1"
        }
    )

    mock_api_responses.assert_any_call(
        "https://www.googleapis.com/youtube/v3/commentThreads",
        params={
            "part": 'snippet',
            "regionCode": 'US',
            "key": API_KEY,
            "order": 'relevance',
            "maxResults": 1,
            'videoId': 'test_id'
        }
    )


@patch('app.requests.get')
def test_get_video_data_no_comments(mock_get):
    """
    Test get_video_data when there are no comments.
    """
    mock_videos_response = MagicMock()
    mock_videos_response.json.return_value = {
        'items': [{
            'id': 'test_id',
            'snippet': {'title': 'Test Video'},
            'statistics': {'viewCount': '1000'}
        }]
    }

    mock_comments_response = MagicMock()
    mock_comments_response.json.return_value = {'items': []}

    mock_get.side_effect = [mock_videos_response, mock_comments_response]

    result = get_video_data('1')
    assert result['test_id']['comment_content'] == 'No comments available'
    assert result['test_id']['comment_likes'] == 0


def test_index_get(client):
    """Test the index route with a GET request"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data
    assert b'<html lang="en">' in response.data
    assert b'<title>' in response.data

    # Check for the presence of the form
    assert b'<form' in response.data

    # Check for the presence of the select element for video categories
    assert b'<select' in response.data
    assert b'name="vc_selected"' in response.data

    # Check for at least one video category
    assert b'<option' in response.data

    # Check for the submit button
    assert b'<button type="submit"' in response.data or b'<input type="submit"' in response.data

@pytest.mark.parametrize("vc_selected, expected_id", [
    ("Film & Animation", "1"),
    ("Music", "10"),
    # Add more categories as needed
])
def test_index_post_invalid_category(client):
    """Test the index route with an invalid category"""
    response = client.post('/', data={"vc_selected": "Invalid Category"})
    assert response.status_code == 200

    # Check for the presence of the form
    assert b'<form' in response.data

    # Check for the presence of the select element
    assert b'<select' in response.data
    assert b'name="vc_selected"' in response.data

    # Check for at least one option in the select element
    assert b'<option' in response.data

    # Check for the submit button
    assert b'<button type="submit"' in response.data or b'<input type="submit"' in response.data

    # Check that the page doesn't contain any video data
    assert b'<div class="video-item"' not in response.data


def test_index_post_invalid_category(client):
    """Test the index route with an invalid category"""
    response = client.post('/', data={"vc_selected": "Invalid Category"})
    assert response.status_code == 200

    # Check for the presence of the form
    assert b'<form' in response.data

    # Check for the presence of the select element
    assert b'<select' in response.data
    assert b'name="vc_selected"' in response.data

    # Check for at least one option in the select element
    assert b'<option' in response.data

    # Check for the submit button
    assert b'<button type="submit"' in response.data or b'<input type="submit"' in response.data

    # Check that the page doesn't contain any video data
    assert b'<div class="video-item"' not in response.data


def test_index_keyerror_handling(client):
    """Test the index route when a KeyError would be raised"""
    # Send a POST request without the expected form data
    response = client.post('/', data={})

    assert response.status_code == 200

    # Check that the page still renders the form
    assert b'<form' in response.data
    assert b'<select' in response.data
    assert b'name="vc_selected"' in response.data

    # Check that no video data is displayed
    assert b'<div class="video-item"' not in response.data


@pytest.mark.parametrize("exception", [
    ValueError(),
    TypeError(),
    Exception("Unexpected error")
])
def test_index_other_exceptions(client, exception):
    """Test the index route with other types of exceptions"""
    with patch('app.get_video_data') as mock_get_video_data:
        mock_get_video_data.side_effect = exception
        response = client.post('/', data={"vc_selected": "Film & Animation"})
        assert response.status_code == 200

        # Check for the presence of the form
        assert b'<form' in response.data

        # Check for the presence of the select element
        assert b'<select' in response.data
        assert b'name="vc_selected"' in response.data

        # Check for at least one option in the select element
        assert b'<option' in response.data

        # Check for the submit button
        assert b'<button type="submit"' in response.data or b'<input type="submit"' in response.data

        # Check that the page doesn't contain any video data
        assert b'<div class="video-item"' not in response.data
