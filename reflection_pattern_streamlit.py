import os
from autogen import ConversableAgent, AssistantAgent
from typing import Annotated
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

config_list = [
    {
        # "model": "llama3.2:3b",
        "model": "qwen2.5:7b",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
    },
]

api_key = os.environ["OPENAI_API_KEY"]

# == Using the local Ollama model ==
llm_config = {"config_list": config_list, "temperature": 0.0}


# task = """
#         Write a concise, engaging article about
#        AI Agentic Workflows. Make sure the article is
#        within 350 words.
#        """


writer = AssistantAgent(
    name="Writer",
    system_message="You are a writer. You write engaging and concise "
    "articles (with title) on given topics. You must polish your "
    "writing based on the feedback you receive and give a refined "
    "version. Only return your final work without additional comments.",
    llm_config=llm_config,
)




critic = AssistantAgent(
    name="Critic",
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    llm_config=llm_config,
    system_message="You are a critic. You review the work of "
    "the writer and provide constructive "
    "feedback to help improve the quality of the content.",
)



# === Add a SEO reviewer agent to suggest SEO improvements ===
SEO_reviewer = AssistantAgent(
    name="SEO-Reviewer",
    llm_config=llm_config,
    system_message="You are an SEO reviewer, known for "
    "your ability to optimize content for search engines, "
    "ensuring that it ranks well and attracts organic traffic. "
    "Make sure your suggestion is concise (within 3 bullet points), "
    "concrete and to the point. "
    "Begin the review by stating your role, like 'SEO Reviewer:'.",
)

# == Add a compliance reviewer agent to suggest compliance improvements ==
compliance_reviewer = AssistantAgent(
    name="Compliance-Reviewer",
    llm_config=llm_config,
    system_message="You are a compliance reviewer. You ensure that the content "
    "adheres to the guidelines and regulations of the industry and Google algorithms. "
    "Begin the review by stating your role, like 'Compliance Reviewer:'.",
)

# == Meta-reviewer agent to provide a final review of the content ==
meta_reviewer = AssistantAgent(
    name="Meta-Reviewer",
    llm_config=llm_config,
    system_message="You are a meta-reviewer. You provide a final review of the content, "
    "ensuring that all the feedback from the previous reviewers has been incorporated. "
    "Begin the review by stating your role, like 'Meta Reviewer:'.",
)


# == Orchestrate the conversation between the agents and nested chats to solve the task ==
def reflection_message(recipient, messages, sender, config):
    return f"""Review the following content. 
            \n\n {recipient.chat_messages_for_summary(sender)[-1]['content']}"""


review_chats = [
    {
        "recipient": SEO_reviewer,
        "message": reflection_message,
        "summary_method": "reflection_with_llm",
        "summary_args": {
            "summary_prompt": "Return review into as JSON object only:"
            "{'Reviewer': '', 'Review': ''}. Here Reviewer should be your role",
        },
        "max_turns": 1,
    },
    {
        "recipient": compliance_reviewer,
        "message": reflection_message,
        "summary_method": "reflection_with_llm",
        "summary_args": {
            "summary_prompt": "Return review into as JSON object only:"
            "{'Reviewer': '', 'Review': ''}.",
        },
        "max_turns": 1,
    },
    {
        "recipient": meta_reviewer,
        "message": "Aggregrate feedback from all reviewers and give final suggestions on the writing.",
        "max_turns": 1,
    },
]

# Register reviewers and orchestrate the conversation
critic.register_nested_chats(review_chats, trigger=writer)

# Print the summary of the conversation
# print("\n\n == Summary ==\n")
# print(res.summary)

# === Streamlit UI ===
# Input text for the query (text input as part of multimodal interaction)
st.title("Agentic Pattern Demo: Reflection Pattern")
task = st.text_input("Enter your query (e.g., 'Write a concise, engaging article about AI Agentic Workflows. Make sure the article is within 350 words.'):")

# Display input query
if task:
    st.write(f"Your task: {task}")
    
    with st.spinner("Writer Generate Reply..."):
        reply = writer.generate_reply(messages=[{"content": task, 
                                                 "role": "user"}])
        st.markdown("# Generate Cotent:")
        st.write(reply)
    
    # Retrieve images based on the text query (image retrieval based on text)
    with st.spinner("Critic Generate Reply..."):
        res = critic.initiate_chat(recipient=writer, 
                                   message=task, 
                                   max_turns=2, 
                                   summary_method="last_msg")
        st.markdown("# Critic:")
        st.write(res.chat_history)

    with st.spinner("Running Summary of conversation..."):
        st.markdown("# Here is the competion of the task:")
        st.write(res.summary)

# python3 -m venv venv
# source venv/bin/activate
# pip install -r requirements.txt
# streamlit run reflection_pattern_srreamlit.py
# python3 -m streamlit run reflection_pattern_streamlit.py
# task: Write a concise, engaging article about AI Agentic Workflows. Make sure the article is within 350 words.