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
import re
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# --- [초기 설정] ---
chat = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/embedding-001",
    transport='rest'
)
db_path = "faiss_index_pdf_quiz"

# 세션 상태 초기화
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
if "mode" not in st.session_state:
    st.session_state.mode = "퀴즈 풀기"

# --- [유틸리티 함수] ---
def parse_ai_json(ai_response):
    """AI 응답에서 JSON 추출"""
    try:
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        st.error(f"JSON 파싱 오류: {e}")
    return None

@st.cache_resource
def get_vectorstore():
    """FAISS 저장소 로드"""
    if os.path.exists(db_path):
        return FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
    return None

st.session_state.vectorstore = get_vectorstore()

# ==========================================
# --- [MISSION 영역: 수강생이 작성할 부분] ---
# ==========================================

# ✅ [퀴즈 풀기] 기능은 분석 단계까지 구현되어 바로 테스트 가능합니다.
# 🚀 [질문하기] 기능을 위해 아래 RAG 핵심 미션들을 직접 구현해 보세요!

# Mission 1: PDF 로드 및 벡터 스토어 구축
def load_and_parse_pdf(pdf_path):
    """
    1. PDF 로드 및 전체 텍스트 추출 (구현 완료 - 퀴즈 동작용)
    2. RecursiveCharacterTextSplitter로 텍스트를 적절한 크기로 분할하세요. (수강생 미션)
    3. FAISS를 사용하여 벡터 스토어를 생성하고 로컬에 저장하세요. (수강생 미션)
    """
    # [1] PDF 로드 및 전체 텍스트 저장 (퀴즈 기능을 위해 제공됩니다)
    loader = PyMuPDFLoader(pdf_path)
    docs = loader.load()
    st.session_state.pdf_context = "\n".join([doc.page_content for doc in docs])

    # ---------------------------------------------------------
    # [MISSION 1] 여기서부터 수강생이 RAG 엔진을 구축합니다.
    # ---------------------------------------------------------
    
    # [2] 텍스트 분할 (RecursiveCharacterTextSplitter 활용)
    # Hint: chunk_size=1000, chunk_overlap=100 정도로 설정해보세요.
    # split_docs = ...
    
    # [3] 벡터스토어 생성 및 로컬 저장
    # Hint: FAISS.from_documents()와 .save_local(db_path)를 활용하세요.
    # st.session_state.vectorstore = ...
    
    pass

# Mission 2: 검색 도구(Tool) 정의
@tool
def search_pdf_documents(query: str) -> str:
    """업로드된 PDF 문서 내에서 정보를 검색합니다."""
    # [수강생 작성 영역]
    # 팁: st.session_state.vectorstore를 사용하여 유사도 검색을 수행하세요.
    return ""

# Mission 3: 에이전트 초기화
def initialize_agent():
    """
    1. 검색 도구(search_pdf_documents)를 사용하는 에이전트를 생성하세요.
    2. 에이전트가 한국어로 답변하고, 문서 내용에만 기반하도록 시스템 프롬프트를 설정하세요.
    3. 생성된 에이전트를 st.session_state.agent에 저장하세요.
    """
    # [수강생 작성 영역]
    pass

# Mission 4: 에이전트 호출 및 답변 생성
def general_response(user_message):
    """에이전트를 사용하여 사용자의 질문에 답변하세요."""
    # [수강생 작성 영역]
    # 팁: st.session_state.agent.invoke()를 활용하세요.
    pass

# ==========================================
# --- [구현 완료 영역: 퀴즈 및 UI 로직] ---
# ==========================================

def question_generator():
    """PDF 컨텍스트를 기반으로 퀴즈 생성 (구현 완료)"""
    if not st.session_state.pdf_context:
        return None
        
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
    ai_response = chain.invoke({"context": st.session_state.pdf_context[:5000]}) # 속도를 위해 일부만 사용
    return parse_ai_json(ai_response.content)

def check_answer(user_message):
    """정답 확인 로직 (구현 완료)"""
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
    except:
        return None

# --- Streamlit UI (구현 완료) ---
st.title("📖 PDF AI 학습 헬퍼 (Scaffold)")

with st.sidebar:
    st.header("⚙️ 설정")
    st.session_state.mode = st.radio("모드 선택", ["퀴즈 풀기", "질문하기"])
    if st.session_state.wrong_answers:
        st.write(f"❌ 틀린 문제: {len(st.session_state.wrong_answers)}개")

uploaded_file = st.file_uploader("PDF 업로드", type="pdf")
if st.button("학습 시작") and uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        path = tmp.name
    
    with st.spinner("분석 중..."):
        load_and_parse_pdf(path)
        initialize_agent()
        st.session_state.pdf_processed = True
        
        if st.session_state.mode == "퀴즈 풀기":
            q = question_generator()
            st.session_state.current_question = q
            if q:
                msg = f"{q['question']}\n\n" + "\n".join(q['options'])
                st.session_state.messages.append({"role": "assistant", "content": msg})
        else:
            st.session_state.messages.append({"role": "assistant", "content": "준비 완료! 질문해 주세요."})
    os.unlink(path)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.write(msg["content"])

if prompt := st.chat_input("입력하세요"):
    if not st.session_state.pdf_processed:
        st.warning("먼저 PDF를 학습시켜 주세요.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    with st.chat_message("assistant"):
        if st.session_state.mode == "퀴즈 풀기":
            res = check_answer(prompt)
            if res:
                st.write(res)
                st.session_state.messages.append({"role": "assistant", "content": res})
                next_q = question_generator()
                st.session_state.current_question = next_q
                if next_q:
                    msg = f"--- 다음 문제 ---\n{next_q['question']}\n\n" + "\n".join(next_q['options'])
                    st.write(msg)
                    st.session_state.messages.append({"role": "assistant", "content": msg})
            else:
                st.info("번호(1~4)를 입력해 주세요.")
        else:
            resp = general_response(prompt)
            st.write(resp)
            st.session_state.messages.append({"role": "assistant", "content": resp})
