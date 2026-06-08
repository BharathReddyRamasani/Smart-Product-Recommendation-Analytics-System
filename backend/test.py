from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import AIMessage
from langchain_core.documents import Document

class DummyLLM:
    def invoke(self, *args, **kwargs):
        return AIMessage(content='Hello world!')

chain = create_stuff_documents_chain(DummyLLM(), PromptTemplate.from_template('{context}'))
result = chain.invoke({'context': [Document(page_content='hi')]})
print(type(result))
print(repr(result))
