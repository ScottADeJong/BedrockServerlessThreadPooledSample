import json
import time
import requests
import streamlit as st
import re

with open("./front_end/preset_evaluation_types.json", "r") as preset_json:
    all_presets = json.load(preset_json)


def build_evaluation_prompts(model_name, text_to_analyze: str, analysis_prompts):
    print(f"Building evaluation prompts for {model_name}...")
    if model_name == "anthropic.claude3.sonnet":
        full_prompt = {
            "body": {"modelId": "anthropic.claude-3-sonnet-20240229-v1:0", "input": []}
        }
        for prompt in analysis_prompts:
            full_prompt["body"]["input"].append(
                build_model_prompt(model_name, text_to_analyze, prompt)
            )
        print(f"Built evaluation prompts for {model_name}. > {full_prompt}")
        return full_prompt


def build_model_prompt(model_name: str, text_to_analyze: str, analysis_prompt: str):
    """
    Builds a prompt for the LLM to perform text analysis and scoring.
    :param model_name: The name of the LLM model to use.
    :param text_to_analyze: The text to analyze.
    :param analysis_prompt: The prompt to use for the analysis.
    :return: A dictionary containing the prompt for the LLM.
    """
    if model_name == "anthropic.claude3.sonnet":
        return {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 500,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": text_to_analyze},
                    {
                        "type": "text",
                        "text": _get_full_evaluation_prompt_text(analysis_prompt),
                    },
                ]
            }],
        }


model_map = {"Anthropic Claude 3 Sonnet": "anthropic.claude3.sonnet"}


def _get_full_evaluation_prompt_text(input_text):
    return f"Evaluate the given essay using the criterion {input_text}. Provide the criterion inside <criterion>, a numeric score from 1 to 10 inside <score>, and your analysis inside <analysis>."


def get_model_names():
    """
    Returns a list of model names.
    :return: A list of model names.
    """
    return model_map.keys()


def get_model_id_from_name(model_name: str):
    return model_map[model_name]


def get_use_case_preset_evaluations(use_case: str):
    """
    Returns a list of preset evaluations for the given use case.
    :param use_case: The use case to get preset evaluations for.
    :return: A list of preset evaluations.
    """
    if use_case:
        return [
            preset["name"] for preset in all_presets if use_case in preset["useCases"]
        ]
    else:
        return [preset["name"] for preset in all_presets]


def get_use_cases():
    unique_use_cases = []
    for obj in all_presets:
        unique_use_cases.extend(obj["useCases"])

    return list(set(unique_use_cases))


def _extract_tags(prompt_response):
    prompt_response = "".join(prompt_response)
    print(f"processing {prompt_response}")
    tags = {}
    # Extract <criterion>
    criterion_match = re.search(r'<criterion>(.*?)</criterion>', prompt_response, re.DOTALL)
    if criterion_match:
        tags['criterion'] = criterion_match.group(1)
    # Extract <score>
    score_match = re.search(r'<score>(.*?)</score>', prompt_response)
    if score_match:
        tags['score'] = score_match.group(1)

    # Extract <analysis>
    analysis_match = re.search(
        r"<analysis>(.*?)</analysis>", prompt_response, re.DOTALL
    )
    if analysis_match:
        tags['analysis'] = analysis_match.group(1)

        return tags


def _parse_analysis(evaluations):
    print(f"parsing {evaluations['Answer']}")
    print(f"Number of responses: {len(evaluations['Answer'])}")
    return [_extract_tags(evaluation) for evaluation in evaluations["Answer"]]

def submit_evaluation(
    data: str, headers={"Content-Type": "application/json"}
) -> dict[str, str]:
    """
    Submits the evaluation request to the API and returns the response
    """
    url = st.secrets["evaluation_endpoint"]
    start: float = time.time()
    response: requests.models.Response = requests.post(url, data=data, headers=headers)
    print(f"Time taken: {time.time() - start}")
    return _parse_analysis(response.json())
