import streamlit as st
import openai
import pandas as pd
import time
import os


# Prompt the user to enter the API key
api_key = st.text_input("Enter your OpenAI API key:", type="password")
if api_key:
    openai.api_key = api_key
else:
    st.warning("Please enter your API key to proceed.")

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = {"OSHA Hazard Violation": [], "RiskRadar: Job Safety Assessment App": []}

# Add company logo
st.image("https://cdn.vectorstock.com/i/500p/05/39/safety-badge-vector-48920539.jpg", width=200)

# Title of the app
st.title("RiskRadar: Job Safety Assessment App")

def wait_on_run(run_id, thread_id):
    """Wait for the OpenAI run to complete."""
    status = "queued"
    while status in ["queued", "in_progress"]:
        run = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
        status = run.status
        time.sleep(1)
    return run

def convert_hazard_to_text(df, hazard_number):
    """Convert a specific hazard from the Excel file to text."""
    row = df.iloc[hazard_number]
    text = f"Hazard {hazard_number + 1}:\n"
    for col in df.columns:
        text += f"{col}: {row[col]}\n"
    return text

def get_assistant_response(content, assistant_id):
    """Get the assistant response from the OpenAI API."""
    try:
        thread = openai.beta.threads.create()
        message = openai.beta.threads.messages.create(thread_id=thread.id, role="user", content=content)
        run = openai.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)
        run = wait_on_run(run.id, thread.id)
        messages = openai.beta.threads.messages.list(thread.id)
        return messages
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return None

def display_messages(selected_tab):
    """Display chat messages from history."""
    for message in st.session_state.messages[selected_tab]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_file_upload(uploaded_file, selected_tab):
    """Handle the file upload and process the Excel file."""
    if uploaded_file:
        with st.spinner("Processing the uploaded file..."):
            try:
                df = pd.read_excel(uploaded_file)
                unique_hazards = df.drop_duplicates().reset_index(drop=True)
                st.success("File processed successfully!")
                st.dataframe(unique_hazards)
                hazard_number = st.selectbox("Select Hazard #", range(len(unique_hazards)))
                hazard_text = convert_hazard_to_text(unique_hazards, hazard_number)
                st.write(hazard_text)
                if st.button("Use Selected Hazard"):
                    st.session_state.messages[selected_tab].append({"role": "user", "content": hazard_text})
                    with st.chat_message("user"):
                        st.markdown(hazard_text)
                    messages = get_assistant_response(hazard_text, "asst_VtTVcysjzIGyZpshBCQW5AfU")
                    if messages:
                        for msg in messages.data:
                            if msg.role == "assistant":
                                with st.chat_message("assistant"):
                                    st.markdown(msg.content[0].text.value)
                                st.session_state.messages[selected_tab].append({"role": "assistant", "content": msg.content[0].text.value})
            except Exception as e:
                st.error(f"An error occurred while processing the file: {e}")

def main():
    if not api_key:
        st.stop()

    selected_tab = st.selectbox("Select Assistant", ["OSHA Hazard Violation", "RiskRadar: Job Safety Assessment App"])

    if selected_tab == "OSHA Hazard Violation":
        st.header("OSHA Hazard Violation")
        display_messages("OSHA Hazard Violation")
        uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
        handle_file_upload(uploaded_file, "OSHA Hazard Violation")
    
    if selected_tab == "RiskRadar: Job Safety Assessment App":
        st.header("RiskRadar: Job Safety Assessment App")
        display_messages("RiskRadar: Job Safety Assessment App")

    if user_input := st.chat_input(f"Ask a question to {selected_tab}..."):
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages[selected_tab].append({"role": "user", "content": user_input})
        assistant_id = "asst_VtTVcysjzIGyZpshBCQW5AfU" if selected_tab == "OSHA Hazard Violation" else "asst_Kr7ozxBcZXSYY1v1oLhqoq3G"
        messages = get_assistant_response(user_input, assistant_id)
        if messages:
            for msg in messages.data:
                if msg.role == "assistant":
                    with st.chat_message("assistant"):
                        st.markdown(msg.content[0].text.value)
                    st.session_state.messages[selected_tab].append({"role": "assistant", "content": msg.content[0].text.value})

if __name__ == "__main__":
    main()
