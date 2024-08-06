import json
import boto3
from pydub import AudioSegment
from pydub.silence import detect_silence
from pydub.effects import normalize
from urllib.parse import unquote

AudioSegment.converter = "/opt/ffmpeg"
AudioSegment.ffmpeg = "/opt/ffmpeg"
AudioSegment.ffprobe ="/opt/ffprobe"

def lambda_handler(event, context):
    print(event["Records"][0]["s3"]["object"]["key"])
    filename = event["Records"][0]["s3"]["object"]["key"]
    filename = unquote(filename).replace("+"," ")
    tokens = filename.replace("uploads/","").replace(".mp3","").split("-")
    print(tokens)
    duration = int(tokens[0])
    if duration == 0:
        duration = 0.01
    mix_id = tokens[1]
    order = int(tokens[2])
    final = tokens[3]
    result_file_name = mix_id+"-"+str(order)+"-"+final+".mp3"

    result = download(filename,"/tmp/"+result_file_name)
    if result ==1: #retry once if failed.
        result = download(filename,"/tmp/"+result_file_name)
    cut_audio("/tmp/"+result_file_name,duration)
    upload("/tmp/"+result_file_name+".cut","processed_behind/"+result_file_name)
    upload("/tmp/"+result_file_name+".front","processed_front/"+result_file_name)
    
    # Expire code after process is done
    query_and_update_table(mix_id,order,'expired',True)
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

def download(object_name, file_name):
    s3 = boto3.client('s3')
    try:
        s3.download_file("relay-mix-file-storage", object_name, file_name)
        print(f"File downloaded: {file_name}")
    except Exception as e:
        print(f"Error downloading file: {e}")
        return 1
    return 0

def upload(file_name, object_name):
    s3 = boto3.client('s3')
    try:
        s3.upload_file(file_name, "relay-mix-file-storage", object_name)
        print(f"File uploaded: {object_name}")
    except Exception as e:
        print(f"Error uploading file: {e}")
        
def query_and_update_table(query_partition_value,query_sort_value, update_key, update_value,query_partition_key='mix_id',query_sort_key='order'):
    # Create the DynamoDB resource
    dynamodb = boto3.resource('dynamodb')

    # Get the table resource
    table = dynamodb.Table("relay_mix_code_table")

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
    
    next_code = ""
    next_is_final = False
    next_order = 0
    # Update the retrieved items
    with table.batch_writer() as batch:
        for item in response['Items']:
            item[update_key] = update_value
            batch.put_item(Item=item)
            next_code = item["next_code"]
            next_is_final = item["next_is_final"]
            next_order = query_sort_value+1
            
    new_item = {
        'code': next_code,
        'order': next_order,
        'mix_id': query_partition_value,
        'is_final': next_is_final,
        'expired': False,
    }
    print(new_item)
    table.put_item(Item=new_item)
    print("Update completed.")

def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)
    
def cut_audio(filename,time):
    # Load the MP3 file
    audio = AudioSegment.from_file(filename, format="mp3")
    if time*1000 > len(audio):
        time = len(audio)//1000-5
    
    # Define parameters for silence detection
    silence_threshold = -28  # dBFS threshold for silence
    silence_min_duration = 300  # Minimum duration of silence in milliseconds
    
    print("Detecting Silent Areas...")
    # Detect silence regions
    silence_regions = detect_silence(audio, silence_thresh=silence_threshold, min_silence_len=silence_min_duration)
    
    # Extract start and end points of non-silent regions
    non_silent_start = silence_regions[0][1]
    non_silent_end = silence_regions[-1][0]
    if non_silent_start >300:
        non_silent_start=0
    if non_silent_end < 300:
        non_silent_end=-1
    gap = silence_regions[-1][1] - silence_regions[-1][0]
    # Trim the audio to remove silent areas
    trimmed_audio = audio[non_silent_start:non_silent_end]
    
    print("Normalizing the Audio...")
    normalized_audio = match_target_amplitude(trimmed_audio,-15)
    # Calculate the duration of the last 10 seconds (in milliseconds)
    cut_sec = (time * 1000) - gap
    if cut_sec < 0:
        cut_sec = 1
    print(gap)
    print("Cutting the Audio...")
    # Extract the last 10 seconds
    cut_audio = normalized_audio[-cut_sec:]
    front_audio = normalized_audio[:-cut_sec]
    
    # Export the cut audio as an MP3 file
    cut_audio.export(filename+".cut", format="mp3",bitrate='320k')
    front_audio.export(filename+".front",format="mp3",bitrate='320k')