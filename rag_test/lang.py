from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import OracleVS  # Oracle 23ai용 커넥터
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

# 1) 오라클 벡터DB 연결
vs = OracleVS(
    user="admin",
    password="GaonDB#2025!Xy",
    dsn="gaondb_high",
    collection_name="ref_handbook_snippet"
)

# 2) LLM 정의
llm = ChatOpenAI(model="gpt-4-turbo")

# 3) 검색 + QA 체인
qa = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=vs.as_retriever(search_type="similarity", k=3)
)

# 4) 질문
query = "이 책에서 '휘발' 개념이 뭐야?"
answer = qa.run(query)
print(answer)
