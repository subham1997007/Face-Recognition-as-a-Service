import os
import boto3
from flask import Flask, request
import base64
from PIL import Image
#import StringIO
from io import BytesIO
from io import StringIO
import io
import glob
import time
#import numpy as np
import asyncio

app = Flask(__name__)
res = dict()
aws_access_key_id ='AKIA3ALSFYMVNU6GKYSS'
aws_secret_access_key = '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'
region_name = 'us-east-1'
request_queue_url = 'https://sqs.us-east-1.amazonaws.com/756690567978/req'
response_queue_url = 'https://sqs.us-east-1.amazonaws.com/756690567978/res'
endpoint_url = 'https://sqs.us-east-1.amazonaws.com'
sqs = boto3.client('sqs', aws_access_key_id= aws_access_key_id, aws_secret_access_key=aws_secret_access_key, endpoint_url=endpoint_url, region_name=region_name)
s3 = boto3.resource(
        service_name='s3',
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )

@app.route("/upload")
def showHomePage():
    return "This is home page"

@app.route('/', methods=["POST"])
async def upload_the_image():
    #print(request.files)
    cnt = 0
    output = None
    if 'myfile' in request.files:
        #print(request.files)
        image = request.files['myfile']
        image1 = request.files['myfile']
        im = image.read()
        f_name = str(image).split(" ")[1][1:][:-1]
        
        #print(f_name)
        if f_name != '':
            f_extension = os.path.splitext(f_name)[1]


            if(f_extension != ".jpg"):
                return "The image should be of type 'JPG'"

            try:
                # value = base64.b64encode(file.read())
                # value = str(value, 'utf-8')

                imopen = Image.open(image)
                qqq = os.path.splitext(f_name)[:1]

                buffered = BytesIO()
                imopen.save(buffered, format="JPEG")
                imopen.save("/home/ubuntu/ipimages/" + str(qqq[0]) + ".jpg")

                filename = "/home/ubuntu/ipimages/" + str(qqq[0]) + ".jpg"
                with open(filename,'rb') as imagefile:
                    #byteform=base64.b64encode(imagefile.read())
                    byteform=base64.b64encode(imagefile.read())
                    value = str(byteform, 'utf-8')
                    str_byte=filename[22:] + " " + value
                    sqs.send_message(
                        QueueUrl=request_queue_url,
                        MessageBody=(
                            str_byte
                        )
                    )
                output  = await get_correct_response(qqq[0])
                return output

            except Exception as e:
                print(str(e))
                return "Something went wrong! x"
        else :
            return "Error with file name"
    else:
        return "File should be of type Image"

    return "Something went wrong"

# @app.route('/results', methods=['GET'])
# def fetchResults():
#     result = ""
#     cnt = 0
#     while get_number_of_msgs_in_res_queue() > 0:
#         response = sqs.receive_message(
#             QueueUrl=request_queue_url,
#             AttributeNames=[
#                 'SentTimestamp'
#             ],
#             MaxNumberOfMessages=100,
#             MessageAttributeNames=[
#                 'All'
#             ],
#             VisibilityTimeout=5,
#         )

#         msgs = response['Messages']
#         for msg in msgs:
#             cnt += 1
#             msg_body = msg['Body']
#             receipt_handle = msg['ReceiptHandle']
#             result = result + f'{cnt} ' + msg_body + "<br/>"
#             sqs.delete_message(
#                 QueueUrl = request_queue_url,
#                 ReceiptHandle = receipt_handle
#             )

#     result = f'Total count: {cnt}<br/>{result}'
#     return result

# @app.route('/clear', methods=['POST'])
# def clear():
#     #Clear all messages from request and response queue
#     sqs.purge_queue( QueueUrl = request_queue_url )
#     sqs.purge_queue( QueueUrl = response_queue_url )

#     #Clear all data from S3 buckets
#     bucket = s3.Bucket('inputbucket34')
#     bucket.objects.all().delete()
#     bucket = s3.Bucket('outputbucket34')
#     bucket.objects.all().delete()

#     return { 'message': 'Cleared all S3 buckets and queues' }

def get_number_of_msgs_in_res_queue() :
    response = sqs.get_queue_attributes(
            QueueUrl=response_queue_url,
            AttributeNames=[
                'ApproximateNumberOfMessages',
                'ApproximateNumberOfMessagesNotVisible'
            ]
        )

    return int(response['Attributes']['ApproximateNumberOfMessages'])

async def get_correct_response(image) :
    result = ""
    

    while True :

        if image in res.keys():
            return res[image]

        response = sqs.receive_message(
            QueueUrl=response_queue_url,
            MaxNumberOfMessages=10,
            MessageAttributeNames=[
                'All'
            ],
        )

        if 'Messages' in response :
            msgs = response['Messages']
            for msg in msgs:
                msg_body = msg['Body']
                res_image = msg_body.split(" ")[0][:-4]

                res[res_image] = msg_body.split(" ")[1]

                receipt_handle = msg['ReceiptHandle']
                sqs.delete_message(
                    QueueUrl = response_queue_url,
                    ReceiptHandle = receipt_handle
                )

                if res_image == image :
                    return res[res_image]


if __name__ == "__main__":
    print("hello")
    app.run(host=os.getenv('IP', '0.0.0.0'),
            port=int(os.getenv('PORT', 8080)))
