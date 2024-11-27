import streamlit as st
import streamlit_logic as custom_logic
import json
import pandas as pd


st.session_state["start_evaluation"] = False
st.session_state["evaluations"] = []
st.session_state["text_to_evaluate"] = ""
if "custom_evaluations" not in st.session_state:
    st.session_state["custom_evaluations"] = []
st.session_state["model_id"] = ""

st.session_state["first_box_expanded"] = True


st.title(f""":rainbow[Amazon Bedrock Text Analysis & Evaluator]""")
with st.container():
    st.info(
        "Amazon Bedrock is a machine learning model that provides various NLP tasks, such as text classification, sentiment analysis, and language generation. This demo showcases how you can leverage LLMs to perform programmatic text analysis and scoring."
    )
    model_choice_name = st.selectbox(
        "Which model would you like to use?", custom_logic.get_model_names(), index=0
    )
    model_id = custom_logic.get_model_id_from_name(model_choice_name)
    use_case = st.selectbox(
        "Which use case would you like to analyze?",
        custom_logic.get_use_cases(),
        index=0,
    )
    st.session_state["evaluations"] = custom_logic.get_use_case_preset_evaluations(
        use_case
    )
    with st.expander(
        "Evaluation Configuration", expanded=st.session_state["first_box_expanded"]
    ):
        st.write(
            "Select which evaluations you'd like to perform. Altenatively, you can add your own evaluation types."
        )
        if st.session_state["evaluations"]:
            for evaluation in st.session_state["evaluations"]:
                st.session_state[f"evaluation_{evaluation}"] = False
                st.checkbox(evaluation, key="dynamic_checkbox_" + evaluation)
            for evaluation in st.session_state["custom_evaluations"]:
                st.checkbox(evaluation, key="dynamic_checkbox_" + evaluation)
            popover = st.popover("Add a custom evalution type")
            popover.write("Add your custom evaluation now!")
            custom_evaluation = popover.text_input("Custom Evaluation Name")
            custom_evaluation_button = popover.button("Add Evaluation")
            if custom_evaluation_button:
                if f"evaluation_{custom_evaluation}" not in st.session_state:
                    st.session_state[f"evaluation_{custom_evaluation}"] = True
                    st.session_state["custom_evaluations"].append(custom_evaluation)
                    st.session_state["evaluations"].append(custom_evaluation)
                    custom_evaluation = ""
                    st.rerun()
                else:
                    popover.error("Evaluation already exists.")

            st.divider()
            st.write(
                "Please provide the text that you'd like to have evaluated against the selected evaluations."
            )
            st.session_state["text_to_evaluate"] = st.text_area(
                "Text to Evaluate", height=200
            )
            st.session_state["start_evaluation"] = st.button("Evaluate")

    if st.session_state["start_evaluation"]:
        st.session_state["first_box_expanded"] = False
        with st.expander("Evaluating Text", expanded=True) as evaluation_expander:
            with st.spinner("Evaluating..."):
                selected_checkboxes = [
                    i.replace("dynamic_checkbox_", "")
                    for i in st.session_state.keys()
                    if i.startswith("dynamic_checkbox_") and st.session_state[i]
                ]
                eval_prompt = custom_logic.build_evaluation_prompts(
                    model_id, st.session_state["text_to_evaluate"], selected_checkboxes
                )
                response = custom_logic.submit_evaluation(
                    json.dumps(eval_prompt)
                )
                df = pd.DataFrame().from_dict(response)
                st.table(df)
