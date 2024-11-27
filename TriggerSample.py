#!/usr/bin/env python3

from rich.table import Table
from rich.console import Console
from botocore import client
import argparse
import requests
import boto3
import json
import time
import boto3


def get_api_gateway_url_by_name(api_name: str, region='us-east-1') -> str:
    """
    Retrieves the REST API URL for the specified API name in the given AWS region.

    Args:
        api_name (str): The name of the REST API in Amazon API Gateway.
        region (str, optional): The AWS region where the API Gateway is located. Defaults to 'us-east-1'.

    Returns:
        str: The full REST API URL for the specified API name, or None if the API is not found.
    """
    # Create the API Gateway client
    api_gateway: client.APIGateway = boto3.client('apigateway', region_name=region)

    # Get a list of all the REST APIs in the specified region
    rest_apis: list[dict[str, str]] = api_gateway.get_rest_apis()['items']

    # Find the REST API with the given name
    for api in rest_apis:
        if api['name'] == api_name:
            api_url: str = f"https://{api['id']}.execute-api.{region}.amazonaws.com/prod/"
            return api_url

    # API not found
    return ""


def post_data(
        url: str,
        data: str,
        headers={"Content-Type": "application/json"}
) -> dict[str, str]:
    """
    POST data string to `url`, return page and headers
    """
    start: float = time.time()
    response: requests.models.Response = requests.post(
        url, data=data, headers=headers)
    print(f"Time taken: {time.time() - start}")
    return response.json()


def display_results(response_data: dict, title: str) -> None:
    """
    This function takes the response data and title and
    formats them into a table format to improve readability
    """
    try:
        answers = response_data.get("Answer")
    except TypeError:
        print("ERROR: Did not get answers.")
        print("{response_data}")
        return

    table: Table = Table(title=title, show_lines=True)
    columns: list[str] = ["Criterion", "Score", "Rationale"]

    for column in columns:
        table.add_column(column)

    if type(answers) == list:
        for answer in answers:
            criterion, score, rationale = answer.split(":")
            row: list[str] = [criterion.strip(), score.strip(), rationale.strip()]
            table.add_row(*row, style='bright_green')

    console: Console = Console()
    console.print(table)


def get_prompts():
    parser = argparse.ArgumentParser(
        prog="TriggerSample.py",
        description="Takes a json file with AI promts as input and runs them against the given model"
    )
    parser.add_argument("filename")
    args = parser.parse_args()

    try:
        with open(args.filename) as input:
            return json.load(input)
    except:
        print(f"ERROR: Could not open {args.filename}")
        exit()


def main():
    prompts = get_prompts()

    # The name we gave the API in the CDK code
    api_name = "bedrock-sample"
    url = get_api_gateway_url_by_name(api_name)

    if url == "":
        print("ERROR: Failed to acquire URL")
        return

    title = "Analysis"
    # This just iterates through and prints the results in a table format
    response_data: dict[str, str] = post_data(url, json.dumps(prompts))
    #for answer in response_data['Answer']:
        #print(answer)

    display_results(response_data, title)


if __name__ == "__main__":
    main()
