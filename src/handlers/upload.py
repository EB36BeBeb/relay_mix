import json
import boto3
import os
import json
import time

fail_response = {
        "isBase64Encoded": False,
        'statusCode': 400,
        "headers": {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'text/plain'
        },
        'body': json.dumps({
            'message': 'File too large'
        })
    }

try:
    table_name = os.environ["TABLE_NAME"]
except:
    table_name = "dev-relay_mix_code_table"
 
try:  
    bucket_name = os.environ["BUCKET_NAME"]
except:
    bucket_name = "dev-relay_mix_file_storage"

def get_presigned_url(bucket_name, key):
    s3_client = boto3.client('s3')
    params = {'Bucket': bucket_name, 'Key': key, 'ContentType':'audio/mpeg'}
    presigned_url = s3_client.generate_presigned_url('put_object', Params=params)
    return presigned_url

def lambda_handler(event, context):
    # file = json.loads(event['body'])['file']
    data = event["body"]
    if int(data['filesize']) > 40*1024*1024: # 40MB max
        return fail_response

    code = data['current_code']
    # Get Information from ddb
    ddb_client = boto3.client('dynamodb')
    res = ddb_client.get_item(TableName=table_name,Key = {'code':{'S':code}})
    try:
        id = res["Item"]["mix_id"]["S"]
        order = res["Item"]["order"]["N"]
        is_final = res["Item"]["is_final"]["BOOL"]
        expired = res["Item"]["expired"]["BOOL"]
    except:
        return fail_response
    if expired:
        return fail_response
    # Generate a unique file name
    file_extension = ".mp3"
    if is_final:
        cut = 0
    else:
        cut = data['duration']
    final = str(is_final)
    
    file_name = f"{cut}-{id}-{order}-{final}{file_extension}"
    
    # Return the presigned URL and success response
    s3_key = f"uploads/{file_name}"
    presigned_url = get_presigned_url(bucket_name, s3_key)
    if not is_final:
        query_and_update_table(id,int(order),'next_code',data["code"],'next_is_final',data["checkbox"])
    print(presigned_url)
    query_and_update_table_single(id,int(order),'mail',data["mail"])
    response = {
        "isBase64Encoded": False,
        'statusCode': 200,
        "headers": {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'text/plain'
        },
        'body': json.dumps({
            'presigned_url': presigned_url,
            'message': 'Presigned URL generated successfully!'
        })
    }
    return response

def query_and_update_table(query_partition_value,query_sort_value, update_key1, update_value1, update_key2, update_value2,query_partition_key='mix_id',query_sort_key='order'):
    # Create the DynamoDB resource
    dynamodb = boto3.resource('dynamodb')

    # Get the table resource
    table = dynamodb.Table(table_name)

    # Define the query parameters
    query_params = {
        'IndexName': 'mix_id-order-index',
        'KeyConditionExpression': f"#{query_partition_key} = :{query_partition_key} AND #{query_sort_key} = :{query_sort_key}",
        'ExpressionAttributeNames': {
            '#'+query_partition_key: query_partition_key,
            '#'+query_sort_key: query_sort_key
        },
        'ExpressionAttributeValues': {
            ':'+query_partition_key: query_partition_value,
            ':'+query_sort_key: query_sort_value
        }
    }

    # Query the table using the GSI
    response = table.query(**query_params)

    # Update the retrieved items
    with table.batch_writer() as batch:
        for item in response['Items']:
            item[update_key1] = update_value1
            item[update_key2] = update_value2
            batch.put_item(Item=item)

    print("Update completed.")

def query_and_update_table_single(query_partition_value,query_sort_value, update_key1, update_value1, query_partition_key='mix_id',query_sort_key='order'):
    # Create the DynamoDB resource
    dynamodb = boto3.resource('dynamodb')

    # Get the table resource
    table = dynamodb.Table(table_name)

    # Define the query parameters
    query_params = {
        'IndexName': 'mix_id-order-index',
        'KeyConditionExpression': f"#{query_partition_key} = :{query_partition_key} AND #{query_sort_key} = :{query_sort_key}",
        'ExpressionAttributeNames': {
            '#'+query_partition_key: query_partition_key,
            '#'+query_sort_key: query_sort_key
        },
        'ExpressionAttributeValues': {
            ':'+query_partition_key: query_partition_value,
            ':'+query_sort_key: query_sort_value
        }
    }

    # Query the table using the GSI
    response = table.query(**query_params)

    # Update the retrieved items
    with table.batch_writer() as batch:
        for item in response['Items']:
            item[update_key1] = update_value1
            batch.put_item(Item=item)

    print("Update completed.")