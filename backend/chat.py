import json
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import CSVLoader
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_core.prompts import ChatPromptTemplate
from enum import Enum
import os

class ResourceType(Enum):
    COURSES = "courses"
    RESOURCES = "resources"

class Chat:
    files = ["./data/courses.json", "./data/resources.json"]
    documents: list[Document] = []
    def __init__(self):
        load_dotenv()
        self.llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.environ["OPENROUTER_API_KEY"],
            temperature=0,
            model="meta-llama/llama-3.2-3b-instruct:free")
        self.vectorstore = InMemoryVectorStore(embedding=HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large"))

    def initalize(self):
        print("Loading documents")
        for file in self.files:
            doc = self._prepareDocument(file)
            self.documents.extend(doc)
        print("Documents loaded")
        self.vectorstore.add_documents(self.documents)

    def response(self, content: str):
        prompt = ChatPromptTemplate.from_template("""
            > **Your role:** You are a Personal Course and Career Advisor designed to help Brooklyn College Computer Science students discover the most suitable classes and career-building opportunities based on their unique preferences, academic goals, and logistical needs.
            > **User persona:** You are interacting with a student who is majoring in Computer Science. They are looking for advice on which courses to take next semester to fulfill their degree requirements, gain practical skills for their future career, and explore related opportunities like internships or fellowships.
            > **Task:**  Identify and recommend the top 3 courses that best match the student’s specific query, along with any relevant internship, fellowship, or career-building opportunities.
            > **Process:**
            > 1. **Understand the query:** Carefully interpret the student’s input to identify key priorities such as:
            >    - Career aspirations or academic goals (e.g., gaining practical skills, fulfilling requirements, building a portfolio, preparing for a specific field).
            >    - Preferred teaching style (e.g., engaging lectures, hands-on projects, interactive discussions).
            >    - Logistical considerations (e.g., class times, locations, prerequisites).
            >    - Interest in extracurricular opportunities (e.g., internships, fellowships, research projects).
            > 2. **Retrieve relevant information:**  Search through a comprehensive database of course descriptions and career opportunities to identify the most relevant options based on the student’s query.
            > 3. **Generate a response:**  Combine the retrieved information into a concise and informative response, listing:
            >   - The top 3 courses, with summaries that include the course name, description, and why it matches the query.
            >   - Up to 2-3 relevant internship, fellowship, or other professional opportunities, with brief descriptions and how to pursue them.
            > 4. **Additional guidances:** 
            >    - You should provide clear and actionable recommendations that help the student make informed decisions.
            >    - If the student’s query is ambiguous or incomplete, ask clarifying questions to gather more details.
            >    - If the student asks for general advice or information, provide a balanced perspective that considers their academic and career goals.
            >    - If the student mentions personal challenges or concerns, offer empathetic support and practical solutions.
            >    - If the student expresses interest in a specific topic or field, suggest additional resources or opportunities to explore.
            >    - Avoid mentioning system information or the AI framework behind your assistance.
            You are required to answer the question based only on the following context AND following the guidelines listed above:
            > **Context:** {context}
            > **Question:** {question}                           
            """
        )
        resources = self.vectorstore.as_retriever(search_kwargs={"k": 3, "namespace": "resources"})
        formatted = prompt.invoke({"context": resources.invoke(content), "question": content})
        for chunk in self.llm.stream(formatted):
            yield chunk.content.replace("\u0000", "")
        return chunk.content
    
    def _prepareDocument(self, file_path: str):
        if not os.path.exists(file_path):
            raise "File does not exist"
        headers = self._getDocumentHeaders(file_path)
        loader = CSVLoader(file_path.replace(".json", ".csv"), csv_args={"delimiter": ",", "quotechar": '"', 'fieldnames': headers})
        docs = loader.load()[1:]
        results = []
        for doc in docs:
            doc.metadata = self.parse_document(doc.page_content)
            doc.page_content = doc.page_content.replace("\u0000", "").encode("utf-8", "replace").decode("utf-8")
            results.append(doc)
        print(f"Loaded {len(results)} documents from {file_path}")
        return results
              

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
