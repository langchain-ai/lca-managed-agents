# identity.py
# Lab 3: the default identity. Requests through the deployment's API must carry a
# LangSmith API key (the Streamlit app does this from your server). People in
# Studio and in Slack are still recognized as themselves, which is what lets
# each person's user-owned Notion connection work.
from managed_deepagents import auth, define_identity

identity = define_identity(auth=auth.langsmith_api_key())
