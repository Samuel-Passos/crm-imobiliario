from langchain_groq import ChatGroq
from pydantic import ConfigDict

class CustomChatGroq(ChatGroq):
    model_config = ConfigDict(extra="allow", populate_by_name=True)

llm = CustomChatGroq(model_name='llama', api_key='123')
setattr(llm, 'ainvoke', 'test')
print(llm.ainvoke)
