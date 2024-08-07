import base64
import boto3
import os
import time
import datetime
import logging  
import io
aws_access_key_id ='AKIA3ALSFYMVNU6GKYSS'
aws_secret_access_key = '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'
region_name = 'us-east-1'
request_queue_url = 'https://sqs.us-east-1.amazonaws.com/756690567978/req'
response_queue_url = 'https://sqs.us-east-1.amazonaws.com/756690567978/res'
endpoint_url = 'https://sqs.us-east-1.amazonaws.com'
sqs = boto3.client('sqs', aws_access_key_id= aws_access_key_id, aws_secret_access_key=aws_secret_access_key, endpoint_url=endpoint_url, region_name=region_name)
s3_client = boto3.client('s3', aws_access_key_id= aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)
s3 = boto3.resource(
    service_name='s3',
    region_name=region_name,
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key
    )
# Create a logging instance
logger = logging.getLogger('my_application')

# Assign a file-handler to that instance
fh = logging.FileHandler("index_logger.txt")
fh.setLevel(logging.INFO) # again, you can set this differently

# Add the handler to your logging instance
logger.addHandler(fh)

def receiveMessages() :
    response = sqs.receive_message(
        QueueUrl=request_queue_url,
            AttributeNames=[
            'SentTimestamp'
            ],
            MaxNumberOfMessages=1,
            MessageAttributeNames=[
            'All'
            ],
            VisibilityTimeout=30,
        )

    if 'Messages' in response :
        return response['Messages']
    else :
        time.sleep(5)
        receiveMessages()

def deleteMessage(receipt_handle) :
    sqs.delete_message(
        QueueUrl = request_queue_url,
        ReceiptHandle = receipt_handle
    )

def decodeMessage(fName, msg) :
    decodeit=open(fName,'wb')
    decodeit.write(base64.b64decode((msg)))
    decodeit.close()

def sendMessageInResponseQueue(fName, msg) :
    endpoint_url = 'https://sqs.us-east-1.amazonaws.com'
    sqs = boto3.client('sqs', aws_access_key_id= aws_access_key_id, aws_secret_access_key=aws_secret_access_key, endpoint_url=endpoint_url, region_name=region_name)
    resp = sqs.send_message(
    QueueUrl = response_queue_url,
        MessageBody=(
        fName + " " + msg
        )
    )

# def upload_to_s3_input_bucket(s3, bucket_name, image_name, stream) :
#     s3_client.upload_fileobj(stream, bucket_name, image_name)

# def upload_to_s3_output_bucket(s3, bucket_name, image_name, image_source) :
#     s3.Object(bucket_name, image_name).upload_file(Filename=image_source)

def upload_to_s3_input_bucket(s3, bucket_name, image_name, image_source) :
    s3.Object(bucket_name, image_name).upload_file(Filename=image_source)

def upload_to_s3_output_bucket(s3, bucket_name, image_name, image_source) :
    s3.Object(bucket_name, image_name).upload_file(Filename=image_source)

def initialize() :
    message = receiveMessages()[0]
    receipt_handle = message['ReceiptHandle']
    fName , encodedMssg=message['Body'].split()
    logging.info('file name : ' + fName)
    outputFile = fName[:-4]

    # binEncodedMssg=encodedMssg[2:-1].encode("ascii")
    # decodeMessage(fName, binEncodedMssg)

    msg_value = bytes(encodedMssg, 'utf-8')
    with open(outputFile + '.bin', "wb") as file:
        file.write(msg_value)
    file = open(outputFile + '.bin', 'rb')
    byte = file.read()
    file.close()
    qp = base64.b64decode(byte)
    with open(fName, "wb") as fff:
        fff.write(qp)

    # image_64_decode = base64.b64decode(encodedMssg)
    # stream = io.BytesIO(image_64_decode)
    # upload_to_s3_input_bucket(s3, 'ip34', fName, stream)
    # s3_client.download_file('ip34', fName, fName)
    # print(fName)



    stdout = os.popen(f'python3 face_recognition.py "{fName}"')
    result = stdout.read().strip()
    logging.info('result : ' + result)

    with open(outputFile, 'w') as f:
        f.write(result)

    #upload_to_s3_input_bucket(s3, 'ip34', fName, stream)
    upload_to_s3_input_bucket(s3, 'ip34', fName, '/home/ec2-user/' + fName)
    upload_to_s3_output_bucket(s3, 'op34', outputFile, '/home/ec2-user/' + outputFile)
    #os.system('rm test*')
    sendMessageInResponseQueue(fName, result)
    deleteMessage(receipt_handle)
    
    

logging.info('Timestamp : ' + str(datetime.datetime.now()))
while True :
    initialize()
