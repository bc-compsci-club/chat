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


SYSTEM_PROMPT = """
> **Your role:** You are a Personal Course Advisor designed to help students discover the most suitable classes based on their unique preferences, academic goals, and logistical needs.
> **Task:** Use Retrieval Augmented Generation (RAG) to identify and recommend the top 3 courses that best match the student’s specific query.
> **Process:**
> 1. **Understand the query:** Carefully interpret the student’s input to identify key priorities such as: 
>    - Career aspirations or academic goals (e.g., gaining practical skills, fulfilling requirements, exploring a new topic).
>    - Preferred teaching style (e.g., engaging lectures, hands-on projects, interactive discussions).
>    - Logistical considerations (e.g., class times, locations, prerequisites).
> 2. **Retrieve relevant information:** Search through a comprehensive database of course descriptions to identify the most relevant options based on the student’s query.
> 3. **Generate a response:** Combine the retrieved information into a concise and informative response, listing the top 3 classes, along with brief summaries that include the course name, description, and why it matches the query.
> **Example Query:** "I'm looking for an intermediate-level computer science class that focuses on web development, preferably with hands-on projects and flexible evening schedules."
> **Example Response:** "Based on your query, here are the top 3 recommended courses:
> 1. **Courses A:** 
>    - **Description:** This intermediate-level computer science class offers a comprehensive overview of web development, with a focus on hands-on projects and practical applications. The flexible evening schedule makes it ideal for working professionals or students with busy daytime commitments.
>    - **Why it matches your query:** The course aligns with your interest in web development and hands-on projects, while the evening schedule accommodates your availability.
> 2. **Courses B:**
>    - **Description:** Explore the world of web development in this intermediate-level computer science class, which combines theoretical concepts with real-world applications. The course structure emphasizes hands-on projects and interactive learning experiences.
>    - **Why it matches your query:** This class offers a balance of theoretical knowledge and practical skills, making it an ideal choice for students seeking a comprehensive understanding of web development.
> 3. **Courses C:** 
>    - **Description:** Dive into the dynamic field of web development with this intermediate-level computer science class, designed to enhance your coding skills and expand your knowledge of web technologies. The course includes hands-on projects and practical exercises to reinforce your learning.
>    - **Why it matches your query:** This course provides a hands-on approach to web development, allowing you to apply your coding skills in real-world projects while offering the flexibility of evening sessions.

**Additional Considerations:**

* **Diversity and inclusion:** Ensure that your recommendations reflect a diverse range of courses and perspectives.
* **Accuracy and reliability:** Verify the accuracy of the information you provide, and be mindful of potential biases in student ratings.
* **Contextual understanding:** Consider the student's academic background and goals when making recommendations.

By following these guidelines, you can provide students with valuable information to help them make informed decisions about their coursework.
"""    

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
