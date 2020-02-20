import boto3
import random
import datetime
from nested_lookup import nested_lookup
import json
import sys
import os

def get_service_client(service,region):
	if region != None:
		try:	
			client = boto3.client(service, region_name=region)
		except ClientError as e:
			print(e)
			sys.exit(1)
		else:
			return client
	else:
		print("Region is required")
		sys.exit(1)

def get_random_az(region):
	az = []
	client = get_service_client("ec2", region)
	response = client.describe_availability_zones(
    Filters=[
        {
            'Name': 'region-name',
            'Values': [region]
        },
    ],
    AllAvailabilityZones=True
	)
	for i in response['AvailabilityZones']:
		az.append(i['ZoneName'])
	return random.choice(az)

def get_variable(name):
	try:
		with open("variable.json", "r") as f:
			variable = json.load(f)
	except OSError:
		return "Cannot read/open file: {}".format("variable.json")
	return variable[name]

def launch_instance(region,ClientName,domain_name):
	client = get_service_client("ec2",region)
	response = client.run_instances(
    ImageId=get_variable('ImageId'),
    InstanceType= get_variable('InstanceType'),
    KeyName= get_variable('KeyName'),
    MaxCount=1,
    MinCount=1,
    Monitoring={
        'Enabled': True
    },
    Placement={
        'AvailabilityZone': get_random_az(region),
    },
    SecurityGroupIds=get_variable('SecurityGroup'),
    # UserData=,

    TagSpecifications=[
        {
            'ResourceType': 'instance',
            'Tags': [
                {
                    'Key': 'Name',
                    'Value': ClientName
                },
            ]
        },
    ],

)
	instance_id =  nested_lookup('InstanceId', response)[0]
	if os.path.isfile('outputvariable.json') == False:
		with open("outputvariable.json", "w") as jsonFile:
			json.dump({domain_name: {'InstanceId': instance_id }}, jsonFile)
		return response
	try:
		with open("outputvariable.json", "r") as f:
			data = json.load(f)
	except OSError:
		return "Cannot read/open file: {}".format("outputvariable.json")
	data[domain_name].update({'InstanceId': instance_id})
	with open("outputvariable.json", "w") as jsonFile:
			json.dump(data, jsonFile)
	return response

def get_instanceid(domain_name):
	try:
		with open("outputvariable.json", "r") as f:
			data = json.load(f)
	except OSError:
		return "Cannot read/open file: {}".format("outputvariable.json")
	return data[domain_name]['InstanceId']

def get_public_ip(region,domain_name):
	client = get_service_client("ec2",region)
	instance_id = get_instanceid(domain_name)
	waiter = client.get_waiter('instance_running')
	waiter.wait(InstanceIds=[instance_id])
	response = client.describe_instances(InstanceIds=[instance_id])
	return nested_lookup('PublicIpAddress', response)[0]

def create_domain(domain_name):
	if check_hostedzone(domain_name) == False:
		client=get_service_client('route53', 'us-east-1')
		response = client.create_hosted_zone(
	    Name= domain_name,
	    CallerReference= str(datetime.datetime.now()),
	    HostedZoneConfig={
	        'PrivateZone': False
	    }
    	)
		variables = {'NameServer': response['DelegationSet']['NameServers'], 'HostedZoneId': response['HostedZone']['Id']}
		if os.path.isfile('outputvariable.json') == False:
			with open("outputvariable.json", "w") as jsonFile:
				json.dump({domain_name: variables}, jsonFile)
				return "Root Domain has been added: {}".format(domain_name)
		else:
			with open("outputvariable.json", "r+") as f:
				data = json.load(f)
				f.seek(0)
				data[domain_name].update(variables)
				json.dump(data, f)
				f.close()
			return "Root Domain has been added: {}".format(domain_name)
	else:
		raise Exception("Domain already exist")

def check_hostedzone(domain_name):
	client=get_service_client('route53','us-east-1')
	response = client.list_hosted_zones(
	)
	for i in nested_lookup('Name',response):
		if i == "{}.".format(domain_name):
			return True
			break
	else:
		return False	

def add_record(domain_name,domain,recordvalue):
	if check_hostedzone(domain_name) == True:
		try:
			with open("outputvariable.json", "r") as f:
				variable = json.load(f)
		except OSError:
			return "Cannot read/open file: {}".format("outputvariable.json")
		client=get_service_client('route53','us-east-1')
		response = client.change_resource_record_sets(
	    HostedZoneId= variable[domain_name]['HostedZoneId'],
	    ChangeBatch={
	        'Comment': str(datetime.datetime.now()),
	        'Changes': [
	            {
	                'Action': 'CREATE',
	                'ResourceRecordSet': {
	                    'Name': domain,
	                    'Type': 'A',
	                    'TTL': 300,
	                    'ResourceRecords': [
	                        {
	                            'Value': recordvalue
	                        }
	                    ]}},
	             {
	                'Action': 'CREATE',
	                'ResourceRecordSet': {
	                    'Name': "www.{}".format(domain),
	                    'Type': 'CNAME',
	                    'TTL': 300,
	                    'ResourceRecords': [
	                        {
	                            'Value': domain
	                        }
	                    ]}}

	                    ]})
		return "Records has been added for: {} ".format(domain)
	else:
		raise Exception("Domain Not Present: {}".format(domain_name))


def get_nameserver(domain_name):
	if check_hostedzone(domain_name) == True:
		try:
			with open("outputvariable.json", "r") as f:
				variable = json.load(f)
		except OSError:
			return "Cannot read/open file: {}".format("outputvariable.json")
		return variable[domain_name]['NameServer']
	else:
		return "Domain Not Exist"
