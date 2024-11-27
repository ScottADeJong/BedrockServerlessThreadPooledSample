## Name
Sample Serverless Architecture to execute parallel prompts against an Amazon Bedrock hosted Large Language Model (LLM)

## Description
This project uses CDK to create an API Gateway, two S3 buckets (ingresss and egress) and a lambda. A JSON file containing a model ID and an array of prompts structured for the model can be uploaded to the ingress bucket or passed through the API. Either of these will trigger the lambda to do parallel calls to Amazon Bedrock through thread pooling. The sample JSON files use non-copyright essays and grade them using four criteria, originality, idea and content, organization and presentation. Any valid combination of a structured prompt and model ID should work and the essays are just a sample.

## Installation
To install, do the following:
1. Make sure you have a working install of the AWS CLI
2. Make sure you have a working copy of the Cloud Development Kit (CDK)
3. Make sure you have a working python install >= 3.9
4. Get a local copy of the repository
5. cd to the root directory of the project
6. Create the pythong virtual environment
```bash
python -m venv .venv
```
7. Start the virtual python environment
```bash
source ./.venv/bin/activate
```
7. Install dependencies
```bash
pip install -r requirements.txt
```
8. Bootstrap the CDK for your account
```bash
cdk bootstrap
```
9. Synthesize the project
```bash
cdk synth
```
10. Deploy the project to AWS
```bash
cdk deploy
```

## Usage
To use without modification to the main code, make sure you have access to the Anthropic Sonnet 3 model (anthropic.claude-3-sonnet-20240229-v1:0) enabled. You can find instructions to do this at this link: https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html

Once deployed, if you are using the TriggerSample.py to run the model, it will find the API by name, send the request to it and return the result. If you want to use the S3 bucket, get the name of the bucket from the AWS Console, the output of the cdk deploy step or from aws s3 ls command and upload or copy a file to the bucket. The analysis will be placed in the egress bucket with .analyzed appended to the name.

The included front end requires a working version of Streamlit, which should be installed if you completed step 7 above.

The front end has to have the URL updated. You can get the API ID with the following command:
```bash
aws apigateway get-rest-apis --query 'items[?name==`bedrock-sample`]' |grep '"id":'
```
The format for the url is https://[id].execute-api.[region].amazonaws.com/[stage]/

Edit the [project_root]/.streamlit/secrets.toml file and modify any part of the URL that needs to be changed. Unless you changed the project, it should be the id and region at most.

Once the secrets.toml file is updated, you are ready to run the front end.
You can start it by going to the root project directory and typing
```bash
streamlit run ./front_end/streamlit_app.py
```

## Support
This is currently unsupported but, if you have questions feel free to contact me and I'll do what I can to help:
@sdejong on slack
sdejong@amazon.com on email

## Roadmap

## Contributing
@awsrudy awsrudy@amazon.com Addie Rudy

## Authors and acknowledgment
@sdejong sdejong@amazon.com Scott DeJong

## License

## Project status
This is a prototype that is likely finished. My plan is to do very little additional to it unless I find another need for it.

Enjoy!
