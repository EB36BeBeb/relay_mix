import json
from handlers.download import lambda_handler

def test_404():
    context = {}
    
    event_json = open("src/tests/events/download/download_404.json")
    event = json.load(event_json)
    response = lambda_handler(event, context)
    assert response['statusCode'] == 404
    
def test_200():
    context = {}
    
    event_json = open("src/tests/events/download/download_200.json")
    event = json.load(event_json)
    response = lambda_handler(event, context)
    assert response['statusCode'] == 200