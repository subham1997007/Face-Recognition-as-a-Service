import time
from urllib import response
import boto3
import os

aws_access_key_id ='AKIA3ALSFYMVNU6GKYSS'
aws_secret_access_key = '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'
region_name = 'us-east-1'
endpoint_url='https://sqs.us-east-1.amazonaws.com'

req_que_url = 'https://sqs.us-east-1.amazonaws.com/756690567978/req'

sqs = boto3.client('sqs', aws_access_key_id= aws_access_key_id, aws_secret_access_key=aws_secret_access_key, endpoint_url=endpoint_url, region_name=region_name)
ec2 = boto3.client('ec2', aws_access_key_id= aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)
ec2x = boto3.resource('ec2', aws_access_key_id= aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)

running_instances = []
stopped_instances = []
starting_instances = []
stopping_instances = []

def get_total_mssg():
    response = sqs.get_queue_attributes(
            QueueUrl=req_que_url,
            AttributeNames=[
                'ApproximateNumberOfMessages',
                'ApproximateNumberOfMessagesNotVisible'
            ]
        )

    num_visible_messages = int(response['Attributes']['ApproximateNumberOfMessages'])
    num_invisible_messages = int(response['Attributes']['ApproximateNumberOfMessagesNotVisible'])
    num_requests = num_visible_messages + num_invisible_messages

    return num_requests

def get_active_app_ins():
    cnt=0
    running_instances.clear()
    instances = ec2x.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    for instance in instances:
        if instance.id != 'i-0115db72bd51fbae9' :
            running_instances.append(instance.id)
            cnt += 1
    print("Running instances: ", cnt)
    return cnt

def get_stopped_ins():
    cnt=0
    stopped_instances.clear()
    instances = ec2x.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['stopped']}])
    for instance in instances:
        cnt += 1
        stopped_instances.append(instance.id)
    print("Stopped instances: ",cnt)
    return cnt

def get_starting_ins():
    cnt=0
    starting_instances.clear()
    instances = ec2x.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['Pending']}])
    for instance in instances:
        cnt += 1
        starting_instances.append(instance.id)
    print("Starting : ",cnt)
    return cnt

def get_stopping_ins():
    cnt=0
    stopping_instances.clear()
    instances = ec2x.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['Stopping']}])
    for instance in instances:
        cnt += 1
        stopping_instances.append(instance.id)
    print("Stopping: ",cnt)
    return cnt

def create_ins(cnt):

    user_data = f"""#!/bin/bash
touch /home/ec2-user;
runuser -l ec2-user -c 'screen -dm bash -c "python3 /home/ec2-user/index.py ; exec sh"'
"""

    instances = ec2.run_instances(
        ImageId="ami-08ed30111b5c00a35",
        MinCount=1,
        MaxCount=1,
        InstanceType="t2.micro",
        # SecurityGroupIds=['sg-0f1e9319e6de67578'],
        KeyName='x',
        UserData = user_data,
        TagSpecifications=[{'ResourceType':'instance', 'Tags': [{'Key':'Name','Value':'app-ins'+str(cnt)}]}],
    )

    return cnt

def scale_up():
    starting_ins_len = get_starting_ins()
    get_stopping_ins()
    get_stopped_ins()
    total_msg = get_total_mssg()
    app_ins = get_active_app_ins()
    total_run_ins = app_ins + starting_ins_len

    print("Start Logic")
    print('total_msg: ', total_msg)
    print('total: app_ins: ', app_ins)

    if total_msg and total_msg > total_run_ins:
        t = 19 - (app_ins + starting_ins_len)

        if t > 0 and  len(stopped_instances) != 0:
            st = total_msg - (app_ins + starting_ins_len)
            min_ins = min(t,st)
            count = 0
            print(len(stopped_instances))
            while count < min_ins and len(stopped_instances):
                inst_id = stopped_instances.pop()
                ec2.start_instances(InstanceIds = [inst_id])
                count += 1


def scale_down():
    get_starting_ins()
    get_stopping_ins()
    get_stopped_ins()
    msgs_in_req_que = get_total_mssg()
    app_ins = get_active_app_ins()
    diff = msgs_in_req_que - (app_ins)

    print("Stop Logic")
    print('total_msg: ', msgs_in_req_que)
    print('total app_ins: ', app_ins)
    print('diff: ', diff)
    print(len(running_instances))

    count = 0
    if diff < 0:
        while count < abs(diff) and len(running_instances):
            inst_id = running_instances.pop()
            ec2.stop_instances(InstanceIds=[inst_id])
            count += 1

def initialize() :
    scale_up()
    time.sleep(5)
    scale_down()
    time.sleep(5)

#os.system('python3 ./deployedapp/webv2.py')

while True :
    initialize()
