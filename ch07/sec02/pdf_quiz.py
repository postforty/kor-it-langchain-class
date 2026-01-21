import streamlit as st
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate
import tempfile
import os
import json
import random
import re
import shutil
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# --- [초기 설정] ---
# 모델 및 임베딩 설정
chat = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    transport='rest' # Streamlit 환경에서의 호환성 및 안정성을 위해 설정
)
db_path = "faiss_index_scaffold"

# 세션 상태 초기화 (UI 상태 유지용)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_context" not in st.session_state:
    st.session_state.pdf_context = ""
if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "wrong_answers" not in st.session_state:
    st.session_state.wrong_answers = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "agent" not in st.session_state:
    st.session_state.agent = None

# --- [유틸리티 함수: 스캐폴딩 제공] ---
def parse_ai_json(ai_response):
    """AI 응답에서 JSON 부분을 추출하여 파싱합니다."""
    try:
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        st.error(f"JSON 파싱 오류: {e}")
    return None

@st.cache_resource
def get_vectorstore():
    """FAISS 저장소가 있으면 로드합니다."""
    if os.path.exists(db_path):
        return FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
    return None

st.session_state.vectorstore = get_vectorstore()

# --- [미션 영역: 수강생이 작성할 부분] ---

# Mission 2: Tool 정의
@tool
def search_pdf_documents(query: str) -> str:
    """업로드된 PDF 문서 내에서 정보를 검색합니다. 
    사실 확인이나 전문적인 내용이 필요할 때 사용하세요.
    """
    if st.session_state.vectorstore is not None:
        # 벡터스토어에서 유사도 검색 수행 (k=3)
        docs = st.session_state.vectorstore.similarity_search(query, k=3)
        return "\n\n".join([doc.page_content for doc in docs])
    return "검색할 문서가 없습니다."

def load_and_parse_pdf(pdf_path):
    # (주의: embeddings, db_path 등은 scaffold의 전역 변수나 세션 상태를 활용한다고 가정)
    # 1. PDF 로드 (하나의 객체로 로드됨)
    loader = PyMuPDFLoader(pdf_path)
    docs = loader.load()

    # 2. 텍스트 분할 (청크 크기 1000, 겹침 100)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = text_splitter.split_documents(docs)

    # 3. 벡터스토어 생성 및 로컬 저장
    st.session_state.vectorstore = FAISS.from_documents(split_docs, embeddings)
    st.session_state.vectorstore.save_local(db_path)
    
    # 전체 컨텍스트 저장 (퀴즈 생성용)
    st.session_state.pdf_context = "\n".join([doc.page_content for doc in docs])


def initialize_agent():
    # (주의: chat, search_pdf_documents 등은 scaffold의 전역 변수 활용 가정)
    system_prompt = """당신은 업로드된 PDF 문서를 바탕으로 학습을 돕는 교육 전문가입니다.
    1. 사용자의 질문에 대해 'search_pdf_documents' 도구를 사용하여 정확한 정보를 찾으세요.
    2. 답변은 반드시 검색된 문서의 내용에만 기반하여 한국어로 작성하세요.
    3. 문서에 관련 내용이 없다면 억지로 꾸며내지 말고 솔직하게 모른다고 답변하세요.
    """
    
    st.session_state.agent = create_agent(
        model=chat,
        tools=[search_pdf_documents],
        system_prompt=system_prompt
    )


def question_generator():
    # (주의: chat, st.session_state.pdf_context 등은 scaffold의 전역/세션 변수 활용 가정)
    prompt = ChatPromptTemplate.from_messages([
        ("system", """당신은 제공된 텍스트에서 4지선다 객관식 문제를 생성하는 교육용 AI입니다.
        반드시 다음 JSON 형식으로만 응답하세요:
        {{
            "question": "문제 내용",
            "options": ["1. 보기1", "2. 보기2", "3. 보기3", "4. 보기4"],
            "answer": "정답 번호 (1~4)",
            "explanation": "해설"
        }}
        
        텍스트: {context}"""),
        ("human", "문제를 1개 생성해 주세요.")
    ])
    
    chain = prompt | chat
    ai_response = chain.invoke({"context": st.session_state.pdf_context})
    
    # Scaffold에 제공된 parse_ai_json 함수를 사용하여 JSON 추출 및 결과 반환
    return parse_ai_json(ai_response.content)

# --- [나머지 UI 및 로직: 스캐폴딩 제공] ---

def check_answer(user_message):
    """사용자가 입력한 숫자가 정답인지 확인"""
    q_data = st.session_state.current_question
    if not q_data: return None
    try:
        user_ans = int(user_message.strip())
        correct_ans = int(q_data['answer'])
        if user_ans == correct_ans:
            return "정답입니다! 🎉"
        else:
            if q_data not in st.session_state.wrong_answers:
                st.session_state.wrong_answers.append(q_data)
            return f"오답입니다. 정답은 {correct_ans}번입니다.\n\n해설: {q_data['explanation']}"
    except ValueError:
        return None

def general_response(user_message):
    """에이전트를 통한 일반 대화"""
    if st.session_state.agent:
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]
        result = st.session_state.agent.invoke({"messages": history + [{"role": "user", "content": user_message}]})
        return result["messages"][-1].content
    return "에이전트가 설정되지 않았습니다."

# --- Streamlit UI 시작 ---
st.title("📖 PDF AI 퀴즈 챗봇 (Scaffold)")

uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")
if st.button("학습 시작") and uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name
    
    with st.spinner("문서를 분석 중..."):
        load_and_parse_pdf(tmp_path)
        initialize_agent()
        q = question_generator()
        st.session_state.current_question = q
        if q:
            st.session_state.messages.append({"role": "assistant", "content": q['question'] + "\n\n" + "\n".join(q['options'])})
            st.session_state.pdf_processed = True
    os.unlink(tmp_path)

# 대화 창 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 메시지 입력 및 답변 처리
if prompt := st.chat_input("메시지를 입력하세요"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    with st.chat_message("assistant"):
        ans_check = check_answer(prompt)
        if ans_check:
            st.write(ans_check)
            st.session_state.messages.append({"role": "assistant", "content": ans_check})
            # 다음 문제 출제
            new_q = question_generator()
            st.session_state.current_question = new_q
            if new_q:
                msg = new_q['question'] + "\n\n" + "\n".join(new_q['options'])
                st.write("---")
                st.write(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
        else:
            resp = general_response(prompt)
            st.write(resp)
            st.session_state.messages.append({"role": "assistant", "content": resp})
