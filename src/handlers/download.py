import json
import boto3
from datetime import datetime, timedelta
import os

try:
    table_name = os.environ["TABLE_NAME"]
except:
    table_name = "dev-relay_mix_code_table"
 
try:  
    bucket_name = os.environ["BUCKET_NAME"]
except:
    bucket_name = "dev-relay_mix_file_storage"

def get_s3_directory_structure(prefix):
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix = prefix)
    directory_structure = {}
    directory_structure["finalized"]=[]
    for fileinfo in response.get('Contents', []):
        filename = fileinfo["Key"].replace(prefix,"")
        filedate = fileinfo["LastModified"] + timedelta(hours=9)
        update_date = filedate.strftime("%Y-%m-%d-%H-%M-%S")
        if len(filename)==0:
            continue
        directory_structure["finalized"].append([filename,update_date])

    return directory_structure

def lambda_handler(event, context):
    print(event)
    target_mix = event["body"]["fileName"]+".mp3"
    result = {}
    directory_structure = get_s3_directory_structure("finalized/")
    for single_object in directory_structure["finalized"]:
        if single_object[0] == target_mix:
            signed_url = boto3.client('s3').generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': "finalized/"+single_object[0]},
                ExpiresIn=3600  # Link valid for 1 hour
            )
            result["url"] = signed_url
    
    if len(result) == 0:
        response = {
            "statusCode": 404,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps("Target File Not Found")
        }
    
    if len(result) > 0:
        response = {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": result
        }
        
    return response