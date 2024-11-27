import json
import time
import boto3
import fnmatch
import concurrent.futures


def run_model(model: str, body: str):
    """This function is called to actually invoke the AI model
       and collect the response. It takes the model ID and a
       formatted JSON body an outputs the response from the
       model"""
    # This will create a new client each time this is called
    # this is necessary since we are using threading and don't
    # want to cross contaminate the clients
    bedrock_runtime = boto3.client(
        service_name='bedrock-runtime',
        region_name='us-east-1'
    )

    start = time.time()
    # The actual call to retrieve an answer from the model
    response = bedrock_runtime.invoke_model(
            body=body,
            modelId=model,
            accept='application/json',
            contentType='application/json',
    )
    print(f"Time taken: {time.time() - start}")
    response_body = json.loads(response.get('body').read())

    # The response from the model now mapped to the answer
    answer = response_body.get('content')[0].get('text')
    return answer


def run_prompts(model_id, prompts):
    """This function takes the given prompts and calls the specified model"""
    reply = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as e:
        future_to_model = {
            e.submit(run_model, model_id, json.dumps(body)):
                body for body in prompts
        }

    for future in concurrent.futures.as_completed(future_to_model):
        try:
            response = future.result()
        except Exception as e:
            print(f"ERROR: {e}")
        else:
            reply.append(response)
    return reply


def write_to_s3(file_name, contents):
    """This function takes a bucket, file name and contents and creates an
       s3 object in the egress bucket"""
    joined_contents = "\n\n".join(contents)
    s3 = boto3.resource('s3')
    bucket_name = get_egress_bucket(s3)
    print(f"INFO: Writing the answers to S3 bucket, {bucket_name}, as {file_name}")
    s3.Object(
            key=file_name,
            bucket_name=bucket_name,
    ).put(Body=joined_contents.encode('utf-8'))


def get_egress_bucket(s3_resource) -> str:
    for bucket in list(s3_resource.buckets.all()):
        if fnmatch.fnmatch(bucket.name, "bedrocksample*egress*"):
            return bucket.name
    return ""


def read_file_from_s3(bucket_name: str, file_name: str):
    """"This function takes a bucket name and object name. It reads prompts
        from the object and returns the body to be processed"""
    s3 = boto3.client('s3')
    print(f"Reading prompts from S3 bucket, {bucket_name}, using {file_name}")
    obj = s3.get_object(Bucket=bucket_name, Key=file_name)
    data = obj['Body'].read().decode('utf-8')

    return json.loads(data)


def parse_event(event):
    """This function takes the event and parses it to get the body"""
    ingress = None
    file = ""

    #default for model_id
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"

    if 'Records' in event:
        print("Getting data from S3")
        ingress = event.get('Records')[0].get('s3').get('bucket').get('name')
        file = event.get('Records')[0].get('s3').get('object').get('key')
        data = read_file_from_s3(ingress, file)
        model_id = data.get("body").get("modelId")
        text = data.get("body").get("input")
    elif type(event.get("body")) == dict:
        print("Getting data from lambda test")
        text = event.get("body").get("body").get("input")
    else:
        print("Getting data from API Gateway")
        model_id = json.loads(
            event.get("body")).get("body").get("modelId")
        text = json.loads(
                event.get("body")).get("body").get("input")

    return (text, file, model_id, ingress)


def lambda_handler(event, _):
    """This is the main lambda handler. It properly formats our input based on
       the point of ingress and calls the evaluation"""

    text, file, model_id, ingress = parse_event(event)
    scores = run_prompts(model_id, list(text))

    if ingress:
        file = ".".join([file, 'analysis'])
        write_to_s3(file, scores)

    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Headers': '*',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        'body': json.dumps({"Answer": scores})
    }
