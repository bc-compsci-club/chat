import json
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import CSVLoader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import ChatPromptTemplate
from enum import Enum
import os

class ResourceType(Enum):
    COURSES = "courses"
    RESOURCES = "resources"

class Chat:
    files = ["./data/courses.json", "./data/resources.json"]
    documents: list[Document] = {}
    def __init__(self):
        load_dotenv()

        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ["OPENROUTER_API_KEY"],
            temperature=0,
            model="meta-llama/llama-3.1-8b-instruct:free")
    

        self.vectorstore = PineconeVectorStore(pinecone_api_key=os.environ["PINECONE_API_KEY"], namespace="courses", embedding=HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large"))

    def response(self, content: str):
        prompt = ChatPromptTemplate.from_template("""
            > **Context:** {context}
            Question: {question}
        """)
        docs = self.vectorstore.as_retriever(search_kwargs={"k": 2}).invoke(content)
        formatted = prompt.invoke({"context": docs, "question": content})
        return self.llm.invoke(formatted).content

        
    def _prepareDocument(self, file_path: str):
        if not os.path.exists(file_path):
            raise "File does not exist"
    
        loader = CSVLoader(file_path.replace(".json", ".csv"), csv_args={"delimiter": ",", "quotechar": '"', 'fieldnames': self._getDocumentHeaders(file_path)})
        docs = loader.load()[1:]
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splitted_docs = splitter.split_documents(docs)
        result = []
        header = self._getDocumentHeaders(file_path)[0]

        for doc in splitted_docs:
            metadata = self.parse_document(doc.page_content)
            result.append(Document(doc.page_content, metadata=metadata, id=f"{metadata[header]}"))
              
        self.documents[file_path] = result
        result = []

    def parse_document(self, document: str):
        lines = document.split("\n")
        data = {}
        for line in lines:
            if line.strip():
                key, value = line.split(":", 1)
                data[key.strip()] = value.strip()
                if value.strip().startswith("["):
                    data[key.strip()] = [item.strip().strip("'") for item in value.strip()[1:-1].split("', '")]
        return data


    def generateEmbedding(self, context: list[str]):
        embedding = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large")
        vector = embedding.embed_documents(context)
        return vector

    def getDocument(self, file_path: ResourceType) -> list[Document]:
        return self.documents[f"./data/{file_path.value.lower()}.json"] or None

    def _getDocumentHeaders(self, file_path):
        headers = []
        with open(file_path, 'r') as f:
            data = json.load(f)
            for resource in data:
                for items in data[resource]:
                    for key in items.keys():
                        if key not in headers:
                            headers.append(key)
        return headers
