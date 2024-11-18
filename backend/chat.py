import json
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import CSVLoader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from langchain_pinecone import PineconeVectorStore
from langchain_core.messages import SystemMessage, HumanMessage
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
        #   template = ChatPromptTemplate.from_messages([
        # SystemMessage(content="hello"),
        # ("human", "Hello, how are you?"),
    #])
        prompt = ChatPromptTemplate.from_template("""
            > **Your role:** You are a Personal Course Advisor agent designed to help students discover the most suitable classes based on their unique preferences, academic goals, and logistical needs.
            > **Task:** Use Retrieval Augmented Generation (RAG) to identify and recommend the top 3 courses that best match the student’s specific query.
            > **Process:**
            > 1. **Understand the query:** Carefully interpret the student’s input to identify key priorities such as:
            >    - Career aspirations or academic goals (e.g., gaining practical skills, fulfilling requirements, exploring a new topic).
            >    - Preferred teaching style (e.g., engaging lectures, hands-on projects, interactive discussions).
            >    - Logistical considerations (e.g., class times, locations, prerequisites).
            > 2. **Retrieve relevant information:** Search through a comprehensive database of course descriptions to identify the most relevant options based on the student’s query.
            > 3. **Generate a response:** Combine the retrieved information into a concise and informative response, listing the top 3 classes, along with brief summaries that include the course name, description, and why it matches the query.         
            
            You are required to answer the question based only on the following context and following these guidelines above:
            > **Context:** {context}
            > **Question:** {question}                           
            """
        )
        docs = self.vectorstore.as_retriever(search_kwargs={"k": 3}).invoke(content)
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
