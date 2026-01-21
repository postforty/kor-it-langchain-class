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
    # TODO: st.session_state.vectorstore가 있다면 similarity_search를 수행(k=3)하고 결과를 반환하세요.
    pass

def load_and_parse_pdf(pdf_path):
    """Mission 1: PDF 로드, 분할, 벡터스토어 생성"""
    # 1. TODO: PyMuPDFLoader를 사용하여 PDF를 로드하세요.
    
    # 2. TODO: RecursiveCharacterTextSplitter로 문서를 분할하세요. (chunk_size=1000)
    
    # 3. TODO: FAISS.from_documents를 사용하여 벡터스토어를 생성하고 로컬에 저장하세요.
    
    # 4. 전체 텍스트를 하나로 합쳐서 st.session_state.pdf_context에 저장 (퀴즈 생성용)
    pass

def initialize_agent():
    """Mission 2: 에이전트 초기화"""
    # TODO: create_agent를 사용하여 에이전트를 생성하고 st.session_state.agent에 저장하세요.
    pass

def question_generator():
    """Mission 3: 프롬프트 템플릿을 이용한 퀴즈 생성"""
    # TODO: 4지선다 JSON 형식을 요구하는 ChatPromptTemplate을 작성하고 invoke 하세요.
    # 제공된 parse_ai_json 함수를 사용하여 결과를 반환하세요.
    return None

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
