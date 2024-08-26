from langchain_community.agent_toolkits import SlackToolkit

toolkit = SlackToolkit()

tools = toolkit.get_tools()