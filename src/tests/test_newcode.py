import json
from handlers.newcode import lambda_handler

def test_200():
    context = {}
    
    event_json = open("src/tests/events/newcode/newcode_200.json")
    event = json.load(event_json)
    response = lambda_handler(event, context)
    assert response['statusCode'] == 200