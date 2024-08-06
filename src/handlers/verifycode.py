import json
import boto3
import os

try:
    table_name = os.environ["TABLE_NAME"]
except:
    table_name = "dev-relay_mix_code_table"
 
try:  
    bucket_name = os.environ["BUCKET_NAME"]
except:
    bucket_name = "dev-relay-mix-file-storage"
    
def lambda_handler(event, context):
    print(event)
    # TODO implement
    code = event["queryStringParameters"]["code"]
    ddb_client = boto3.client('dynamodb')
    
    res = ddb_client.get_item(TableName=table_name,Key = {'code':{'S':code}})
    print(res)
    try:
        id = res["Item"]["mix_id"]["S"]
        order = res["Item"]["order"]["N"]
        is_final = res["Item"]["is_final"]["BOOL"]
        expired = res["Item"]["expired"]["BOOL"]
    except:
        return {
            'statusCode': 400,
            'body': json.dumps('Failed to verify the code')
        }
    if expired:
        return {
            'statusCode': 406,
            'body': json.dumps('Code expired')
        }
#    if is_final:
#        return return_page_with_url("body3.html",code,id+"-"+str(int(order)-1)+"-False"+".mp3",order)
#    if int(order) == 1:
#        return return_page("body.html",code,order)
#    elif int(order)>1:
#        return return_page_with_url("body2.html",code,id+"-"+str(int(order)-1)+"-False"+".mp3",order)
    
    return {
        'statusCode': 200,
        'body': {"id" : id, "order" : order, "is_final" : is_final, "download_url" : get_presigned_download_url(id+"-"+str(int(order)-1)+"-False"+".mp3")}
    }


def get_presigned_download_url(filename):
    s3 = boto3.client('s3')
    try:
        response = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': "processed_behind/"+filename, "ResponseContentDisposition": "attachment; filename=StartWithThisFile.mp3"},
            ExpiresIn=300
        )
        return response
    except Exception as e:
        print(f"Error generating pre-signed URL: {e}")
        return None
        
# LEGACY CDOES BELOW
def return_page(filename,code="",order=0):
    body = ""
    with open(filename, "r") as f:
        body = f.read()
    try:
        body = body.replace("{order}",order)
        body = body.replace("{current_code}",code)
    except:
        print("No code required")
    return {
    "statusCode": 200,
    "body": body,
    "headers": {
        'Content-Type': 'text/html',
        }
    }

def return_page_with_url(filename,code,s3_file_name,order):
    body = ""
    with open(filename, "r") as f:
        body = f.read()
    body = body.replace("{order}",order)
    body = body.replace("{current_code}",code)
    body = body.replace("{behind_mix_link}",get_presigned_download_url(s3_file_name))
    return {
    "statusCode": 200,
    "body": body,
    "headers": {
        'Content-Type': 'text/html',
        }
    }

