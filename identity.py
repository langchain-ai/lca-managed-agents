# identity.py
# Who's calling. Schedules (Lab 2) and Slack (Lab 3) need an identity declared.
# This is the default: API requests carry a LangSmith API key, and people in
# Studio and Slack are recognized as themselves, so each person's own
# connections, like their Notion, work.
from managed_deepagents import auth, define_identity

identity = define_identity(auth=auth.langsmith_api_key())
