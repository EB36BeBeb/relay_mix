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
    print(event)
    filename = event["Records"][0]["s3"]["object"]["key"]
    filename = unquote(filename).replace("+"," ")
    # filename = "processed_front/ABCD-3-True.mp3"
    tokens = filename.replace("processed_front/","").replace(".mp3","").split("-")
    print(tokens)
    mix_id = tokens[0]
    order = int(tokens[1])
    final = tokens[2]
    if final != "True":
        return
    file_list = []
    for i in range(1,order+1):
        if i==order:
            filename = mix_id+"-"+str(i)+"-True.mp3"
        else:
            filename = mix_id+"-"+str(i)+"-False.mp3"
        result = download("processed_front/"+filename,"/tmp/"+filename)
        if result == 1: # retry
            result = download("processed_front/"+filename,"/tmp/"+filename)
        if result == 1: # not found
            break
        file_list.append("/tmp/"+filename)
    print(file_list)
    merge_audio_files(file_list,"/tmp/"+mix_id+".mp3")
    upload("/tmp/"+mix_id+".mp3","finalized/"+mix_id+".mp3")
    
    # TODO implement
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }

def download(object_name, file_name):
    print(object_name)
    s3 = boto3.client('s3')
    try:
        s3.download_file("relay-mix-file-storage", object_name, file_name)
        print(f"File downloaded: {file_name}")
        return 0
    except Exception as e:
        print(f"Error downloading file: {e}")
        return 1

def upload(file_name, object_name):
    s3 = boto3.client('s3')
    try:
        s3.upload_file(file_name, "relay-mix-file-storage", object_name)
        print(f"File uploaded: {object_name}")
    except Exception as e:
        print(f"Error uploading file: {e}")

def merge_audio_files(input_files, output_file):
    # Initialize an empty AudioSegment object
    merged_audio = AudioSegment.empty()

    # Iterate over the input files
    total_length = [0]
    for i,file in enumerate(input_files):
        # Load each audio file
        print(f"Merging No.{i} File")
        audio = AudioSegment.from_file(file)
        print(total_length)
        total_length.append(total_length[i]+audio.duration_seconds*1000)
        # Concatenate the audio file to the merged audio
        merged_audio += audio
        # if i==0:
        #     merged_audio += audio[:-20]
        # elif i==len(input_files)-1:
        #     merged_audio += audio[20:]
        # else:
        #     merged_audio += audio[20:-20]
    print("Removing silence between files")
    silence_regions = detect_silence(merged_audio, silence_thresh=-32, min_silence_len=100)
    print(silence_regions)
    delete_list = []
    for error_candidate in total_length:
        for i,region in enumerate(silence_regions):
            if region[0]<error_candidate+1 and error_candidate+1 < region[1]:
                delete_list.append(i)
                continue
    delete_list = delete_list[::-1]
    print(delete_list)
    for i in delete_list:
        merged_audio = merged_audio[:silence_regions[i][0]] + merged_audio[silence_regions[i][1]:] 
    print("Exporting...")
    # Export the merged audio as a single file
    merged_audio.export(output_file, format="mp3",bitrate='320k')

    # Export the merged audio as a single file
    print("Normalizing the Audio...")
    normalized_audio = normalize(merged_audio)
    normalized_audio.export(output_file, format="mp3",bitrate='320k')