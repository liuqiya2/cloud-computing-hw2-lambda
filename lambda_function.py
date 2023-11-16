import json

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

REGION = 'us-east-1'
HOST = 'search-photos-ypc2mfwdjhxbxyeewmd3v3zi6e.us-east-1.es.amazonaws.com'
INDEX = 'photos'
BUCKET = 'hw2-b2-qiyan'

client = boto3.client('lexv2-runtime')
s3 = boto3.client('s3')

def lambda_handler(event, context):
    print("change in demo")
    print(f"Event here:{event}")
    msg_from_user = event['queryStringParameters']['q']
    print(f"Message from frontend: {msg_from_user}")
    
    response = client.recognize_text(
        botId='CD8QPGLDRK', # MODIFY HERE
        botAliasId='TSTALIASID', # MODIFY HERE
        localeId='en_US',
        sessionId='testuser',
        text=msg_from_user)
    
    print(f"response form lex: {response}")
    
    keyword1 = response['sessionState']['intent']['slots']['Keyword']['value']['interpretedValue'] if response['sessionState']['intent']['slots']['Keyword'] else None
    keyword2 = response['sessionState']['intent']['slots']['Keyword2']['value']['interpretedValue'] if response['sessionState']['intent']['slots']['Keyword2'] else None
    
    print("Keyword1: " + str(keyword1))
    print("Keyword2: " + str(keyword2))
    
    results = query(keyword1, keyword2)
    results = list(set(results))
    print(f"Photo results:{results}")
    
    photos = []
    for photo_name in results:
        #image_url = f"https://{BUCKET}.s3.amazonaws.com/{photo_name}"
        #photos.append(image_url)
        img_response = s3.get_object(Bucket=BUCKET, Key=photo_name)
        image_data = img_response['Body'].read()
        encoded_photo_data = image_data.decode('utf-8')
        photos.append(encoded_photo_data)
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': '*',
        },
        'body': json.dumps(photos)
    }


def query(term1, term2):
    if (term1 is None and term2 is None):
        empty_list = []
        return empty_list
    elif (term1 is None and term2 is not None):
        q = {
            'size': 5,  # Retrieve only one matching document
            'query': {
                'bool': {
                    'must': [
                        {'match': {'labels': term2}}
                    ]
                }
            }
        }
    elif (term1 is not None and term2 is None):
        q = {
            'size': 5,  # Retrieve only one matching document
            'query': {
                'bool': {
                    'must': [
                        {'match': {'labels': term1}}
                    ]
                }
            }
        }
    elif (term1 is not None and term2 is not None):
        q = {
            'size': 5,  # Retrieve only one matching document
            'query': {
                'bool': {
                    'must': [
                        {'match': {'labels': term1}},
                        {'match': {'labels': term2}}
                    ]
                }
            }
        }
    
    client = OpenSearch(hosts=[{
        'host': HOST,
        'port': 443
    }],
                        http_auth=get_awsauth(REGION, 'es'),
                        use_ssl=True,
                        verify_certs=True,
                        connection_class=RequestsHttpConnection)

    res = client.search(index=INDEX, body=q)
    print(res)

    hits = res['hits']['hits']
    object_keys = [image['_source']['objectKey'] for image in hits]
    # Return the _id of the first matched document if any
    #return hits[0]['_id'] if hits else None
    return object_keys


def get_awsauth(region, service):
    cred = boto3.Session().get_credentials()
    return AWS4Auth(cred.access_key,
                    cred.secret_key,
                    region,
                    service,
                    session_token=cred.token)
