import os
import asyncio
from typing import List, TypedDict
from dotenv import load_dotenv

import gradio as gr
from langchain_postgres.vectorstores import PGVector
from langchain_ollama import OllamaEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document
from langgraph.graph import StateGraph, START, END

# 환경 변수 로드
load_dotenv()

# 에이전트 상태 정의
class AgentState(TypedDict):
    query: str
    context: List[Document]
    answer: str

# 데이터베이스 연결 설정
PGVECTOR_ID = os.getenv("PGVECTOR_ID")
PGVECTOR_PW = os.getenv("PGVECTOR_PW")
PGVECTOR_HOST = os.getenv("PGVECTOR_HOST", "localhost")
PGVECTOR_PORT = os.getenv("PGVECTOR_PORT", "5432")
PGVECTOR_DB = os.getenv("PGVECTOR_DB")
CONNECTION = f'postgresql+psycopg://{PGVECTOR_ID}:{PGVECTOR_PW}@{PGVECTOR_HOST}:{PGVECTOR_PORT}/{PGVECTOR_DB}'

# RAG 프롬프트 템플릿 정의
RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """당신은 소득세법 전문가입니다. 주어진 문맥을 바탕으로 정확하고 상세한 답변을 제공하세요.

문맥:
{context}

답변 시 다음 규칙을 따르세요:
1. 문맥에 있는 정보만 사용하여 답변하세요
2. 확실하지 않은 경우 "제공된 문서에서 해당 정보를 찾을 수 없습니다"라고 답하세요
3. 법률 용어는 쉽게 풀어서 설명하세요
4. 구체적인 예시를 들어 설명하세요"""),
    ("human", "{question}")
])

# 임베딩 및 LLM 초기화
embedding_model = OllamaEmbeddings(model="bge-m3")
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

# 벡터스토어 로드
try:
    db = PGVector(
        embeddings=embedding_model,
        connection=CONNECTION,
        collection_name="langchain"
    )
    print("✅ 벡터스토어 연결 성공")
except Exception as e:
    print(f"❌ 벡터스토어 연결 실패: {e}")
    raise

# 노드 함수 정의
def retrieve(state: AgentState) -> AgentState:
    """유사 문서 검색"""
    query = state['query']
    try:
        docs = db.similarity_search(query, k=3)
        print(f"📚 검색된 문서 수: {len(docs)}")
        return {'context': docs}
    except Exception as e:
        print(f"❌ 검색 오류: {e}")
        return {'context': []}

def generate(state: AgentState) -> AgentState:
    """답변 생성"""
    context = state['context']
    query = state['query']
    
    if not context:
        return {'answer': "죄송합니다. 관련 정보를 찾을 수 없습니다."}
    
    try:
        # 문맥을 문자열로 변환
        context_str = "\n\n".join([doc.page_content for doc in context])
        
        # RAG 체인 구성
        rag_chain = RAG_PROMPT | llm | StrOutputParser()
        
        # 답변 생성
        response = rag_chain.invoke({
            'question': query,
            'context': context_str
        })
        
        print(f"✅ 답변 생성 완료 (길이: {len(response)}자)")
        return {'answer': response}
    
    except Exception as e:
        print(f"❌ 생성 오류: {e}")
        return {'answer': f"답변 생성 중 오류가 발생했습니다: {str(e)}"}

# 그래프 구축
workflow = StateGraph(AgentState)

workflow.add_node("retrieve", retrieve)
workflow.add_node("generate", generate)

workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

graph = workflow.compile()

# Gradio 챗봇 함수
async def predict(message, history):
    """사용자 메시지 처리"""
    if not message.strip():
        return "질문을 입력해주세요."
    
    try:
        initial_state = {"query": message}
        result = await asyncio.to_thread(graph.invoke, initial_state)
        return result.get('answer', "답변을 생성할 수 없습니다.")
    
    except Exception as e:
        print(f"❌ 예측 오류: {e}")
        return f"오류가 발생했습니다: {str(e)}"

# Gradio 인터페이스 실행
def main():
    print("🚀 소득세법 질의응답 에이전트를 시작합니다...")
    
    demo = gr.ChatInterface(
        fn=predict,
        title="💼 소득세법 질의응답 에이전트",
        description="""
        **LangGraph**와 **Gemini**를 활용한 법률 상담 에이전트입니다.
        
        소득세법 관련 질문을 입력하시면, 관련 문서를 검색하여 정확한 답변을 제공합니다.
        """,
        examples=[
            "연봉 5천만원 직장인의 소득세는 얼마인가요?",
            "근로소득공제 한도는 얼마인가요?",
            "종합소득세 신고 기간은 언제인가요?",
            "퇴직소득세 계산 방법을 알려주세요"
        ],
        chatbot=gr.Chatbot(height=500)
    )

    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )

if __name__ == "__main__":
    main()

    # http://127.0.0.1:7860 에서 접속 가능합니다