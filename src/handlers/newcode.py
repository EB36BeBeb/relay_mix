import json
import base64
import os
from urllib.parse import parse_qs
import boto3

def lambda_handler(event, context):
    # TODO implement
    
    body = event["body"]
    new_code = body["newCode"]
    mix_name = body["mixName"]
    
    # 'get os.environr or dev-relay_mix_code_table for default '
    try:
        table_name = os.environ["TABLE_NAME"]
    except:
        table_name = "dev-relay_mix_code_table"
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    # Specify the key for the item you want to update
    key = {'code': new_code}
    
    update_body = {}
    update_body["mix_id"] = mix_name
    update_body["expired"] = False
    update_body["is_final"] = False
    update_body["order"] = 1
    # Create an UpdateExpression and ExpressionAttributeValues for each field in the dictionary
    update_expression = 'SET ' + ', '.join([f'#{key} = :{key}' for key in update_body.keys()])
    expression_attribute_values = {f':{key}': value for key, value in update_body.items()}
    expression_attribute_names = {f'#{key}': key for key in update_body.keys()}
    res = table.update_item(
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_attribute_values,
        ExpressionAttributeNames=expression_attribute_names
    )
    print(res)
    if res["ResponseMetadata"]["HTTPStatusCode"] == 200:
        return {
            "statusCode": 200,
        }
    else:
        return {
            "statusCode": 500,
            "body": "Something Wrong",
            "headers": {
                'Content-Type': 'application/json',
                }
            }
        