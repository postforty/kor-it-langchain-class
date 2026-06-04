import streamlit as st
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langchain_core.prompts import load_prompt
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import AIMessage
from langchain.agents.middleware import before_agent, after_agent
import tempfile
import os
import json
import re
import uuid
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. 전역 상태 및 기본 설정
# ==========================================
chat = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")
safety_model = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite") # 가드레일용 별도 모델
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", transport='rest')

@dataclass
class Context:
    user_id: str

# 메모리 상태 유지 (Checkpointer & Store)
if "store" not in st.session_state:
    st.session_state.store = InMemoryStore(index={"embed": embeddings, "dims": 1536})
if "checkpointer" not in st.session_state:
    st.session_state.checkpointer = InMemorySaver()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_context" not in st.session_state:
    st.session_state.pdf_context = ""
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "agent" not in st.session_state:
    st.session_state.agent = None

# ==========================================
# 2. 도구 (Tools) 정의 (RAG + 장기기억)
# ==========================================
db_path = "faiss_index_capstone"
@st.cache_resource
def get_vectorstore():
    if os.path.exists(db_path):
        return FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
    return None

st.session_state.vectorstore = get_vectorstore()

@tool
def search_pdf_documents(query: str) -> str:
    """업로드된 PDF 문서 내에서 정보를 검색합니다."""
    vs = st.session_state.get("vectorstore")
    if vs is None: vs = get_vectorstore()
    if vs is not None:
        docs = vs.similarity_search(query, k=3)
        return "\n\n".join([doc.page_content for doc in docs])
    return "검색할 문서가 없습니다."

@tool
def save_student_profile(info: str, runtime: ToolRuntime[Context] = None) -> str:
    """학생의 취약점, 선호도 등 중요한 학습 정보를 장기 메모리에 기록합니다."""
    assert runtime.store is not None
    user_id = runtime.context.user_id
    item_id = str(uuid.uuid4())
    runtime.store.put((user_id, "profile"), item_id, {"text": info})
    return "학생 프로필에 저장되었습니다."

# ==========================================
# 3. 가드레일 미들웨어 4종
# ==========================================
forbidden_topics = {"cheating": ["답지", "정답 알려줘"], "distraction": ["롤", "게임", "유튜브"], "harmful": ["담배", "술"]}
ESCALATION_KEYWORDS = ["왕따", "괴롭힘", "우울해"]

@before_agent(can_jump_to=["end"])
def education_guardrail(state, runtime):
    """사전 차단: 부정행위 및 딴짓 방지"""
    if not state["messages"]: return None
    user_text = state["messages"][-1].get("content", "") if isinstance(state["messages"][-1], dict) else getattr(state["messages"][-1], "content", "")
    for kw in forbidden_topics["cheating"]:
        if kw in user_text: return {"messages": [{"role": "assistant", "content": "🚫 스스로 고민해봐야 실력이 늘어요!"}], "jump_to": "end"}
    for kw in forbidden_topics["distraction"]:
        if kw in user_text: return {"messages": [{"role": "assistant", "content": "⏰ 지금은 공부에 집중할 시간이에요!"}], "jump_to": "end"}
    return None

@before_agent
def student_safety_middleware(state, runtime):
    """사전 마스킹: 개인정보 보호"""
    if not state["messages"]: return None
    last_message = state["messages"][-1]
    content = last_message.get("content", "") if isinstance(last_message, dict) else getattr(last_message, "content", "")
    phone_pattern = r'01[016789]-?[0-9]{3,4}-?[0-9]{4}'
    if re.search(phone_pattern, content):
        content = re.sub(phone_pattern, '<PHONE_REDACTED>', content)
        if isinstance(last_message, dict): last_message["content"] = content
        else: last_message.content = content
    return None

@before_agent(can_jump_to=["end"])
def counseling_escalation_middleware(state, runtime):
    """사전 이관: 위기 상황 감지"""
    if not state["messages"]: return None
    content = state["messages"][-1].get("content", "") if isinstance(state["messages"][-1], dict) else getattr(state["messages"][-1], "content", "")
    for kw in ESCALATION_KEYWORDS:
        if kw in content:
            return {"messages": [{"role": "assistant", "content": "전문 상담 선생님께 연결해 드릴게요. 🍀"}], "jump_to": "end"}
    return None

@after_agent
def answer_leakage_guardrail(state, runtime):
    """사후 교정: 정답 유출 방지 (외부 프롬프트 사용)"""
    if not state["messages"]: return None
    last_message = state["messages"][-1]
    content = last_message.get("content", "") if isinstance(last_message, dict) else getattr(last_message, "content", "")
    role = last_message.get("role", "") if isinstance(last_message, dict) else ("assistant" if isinstance(last_message, AIMessage) else "")
    if role != "assistant" or not content: return None

    # 외부 프롬프트(YAML) 로드
    auditor_prompt = load_prompt(os.path.join(os.path.dirname(__file__), "prompts", "guardrail_auditor.yaml")).format(content=content)
    result = safety_model.invoke(auditor_prompt)

    if "LEAKED" in result.content:
        orig = state["messages"][-2]
        oq = orig.get("content", "") if isinstance(orig, dict) else getattr(orig, "content", "")
        correction_prompt = load_prompt(os.path.join(os.path.dirname(__file__), "prompts", "guardrail_correction.yaml")).format_messages(original_question=oq)
        corrected = safety_model.invoke(correction_prompt)
        if isinstance(last_message, dict): last_message["content"] = corrected.content
        else: last_message.content = corrected.content
    return None

# ==========================================
# 4. 종합 에이전트 초기화 (결합)
# ==========================================
def initialize_agent():
    # 외부 시스템 프롬프트 로드
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "agent_system.yaml")
    system_prompt = load_prompt(prompt_path, encoding="utf-8").format()
    
    # RAG 도구 + 장기기억 도구 + 시스템 프롬프트 + 미들웨어 + 장기/단기 저장소가 모두 결합된 완전체
    st.session_state.agent = create_agent(
        model=chat,
        tools=[search_pdf_documents, save_student_profile], 
        system_prompt=system_prompt,
        store=st.session_state.store,              # 장기 기억 연결
        checkpointer=st.session_state.checkpointer,# 단기 기억 연결
        context_schema=Context,
        middleware=[education_guardrail, student_safety_middleware, counseling_escalation_middleware, answer_leakage_guardrail]
    )

def parse_ai_json(ai_response):
    try:
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match: return json.loads(json_match.group(0))
    except Exception as e: pass
    return None

def question_generator():
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "quiz_generator.yaml")
    prompt = load_prompt(prompt_path, encoding="utf-8")
    chain = prompt | chat
    ai_response = chain.invoke({"context": st.session_state.pdf_context})
    content = ai_response.content
    if isinstance(content, list): content = "".join([p.get("text", "") for p in content if isinstance(p, dict) and p.get("type")=="text"])
    return parse_ai_json(content)

# ==========================================
# 5. UI (Streamlit)
# ==========================================
st.title("🎓 궁극의 PDF AI 튜터 (Capstone)")

uploaded_file = st.file_uploader("PDF 업로드", type="pdf")
if st.button("학습 시작") and uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name
    
    with st.spinner("문서를 분석 중..."):
        loader = PyMuPDFLoader(tmp_path)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        split_docs = text_splitter.split_documents(docs)
        st.session_state.vectorstore = FAISS.from_documents(split_docs, embeddings)
        st.session_state.vectorstore.save_local(db_path)
        get_vectorstore.clear()
        st.session_state.pdf_context = "\n".join([doc.page_content for doc in docs])
        
        initialize_agent()
        st.session_state.messages.append({"role": "assistant", "content": "문서 분석이 완료되었습니다! 무엇이든 물어보세요."})
    os.unlink(tmp_path)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]): st.write(msg["content"])

if prompt := st.chat_input("메시지를 입력하세요"):
    if not st.session_state.agent:
        st.warning("먼저 PDF 파일을 업로드하고 '학습 시작'을 눌러주세요.")
        st.stop()

    # Streamlit UI 상에 표시하기 위해 메시지 저장
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("답변을 찾는 중..."):
            # Checkpointer가 단기 메모리를 관리하므로 이전 메시지들을 잘라서 보낼 필요가 없음!
            result = st.session_state.agent.invoke(
                {"messages": [{"role": "user", "content": prompt}]},
                config={"configurable": {"thread_id": "student_thread_01"}}, # 단기 메모리 식별자
                context=Context(user_id="student_user_01")                 # 장기 메모리 식별자
            )
            
            ai_msg = result["messages"][-1]
            content = ai_msg.content
            if isinstance(content, list):
                content = "".join([part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"])
            
            st.write(content)
            st.session_state.messages.append({"role": "assistant", "content": content})
