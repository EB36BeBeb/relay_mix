import json
from handlers.verifycode import lambda_handler

def test_200():
    context = {}
    
    event_json = open("src/tests/events/verifycode/verifycode_200.json")
    event = json.load(event_json)
    response = lambda_handler(event, context)
    assert response['statusCode'] == 200

#other errors
def test_400():
    context = {}
    event_json = open("src/tests/events/verifycode/verifycode_400.json")
    event = json.load(event_json)
    response = lambda_handler(event, context)
    assert response['statusCode'] == 400
    
#expired
def test_406():
    context = {}
    event_json = open("src/tests/events/verifycode/verifycode_406.json")
    event = json.load(event_json)
    response = lambda_handler(event, context)
    assert response['statusCode'] == 406