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
    auditor_prompt = load_prompt(os.path.join(os.path.dirname(__file__), "prompts", "guardrail_auditor.yaml"), encoding="utf-8").format(content=content)
    result = safety_model.invoke(auditor_prompt)

    if "LEAKED" in result.content:
        orig = state["messages"][-2]
        oq = orig.get("content", "") if isinstance(orig, dict) else getattr(orig, "content", "")
        correction_prompt = load_prompt(os.path.join(os.path.dirname(__file__), "prompts", "guardrail_correction.yaml"), encoding="utf-8").format(original_question=oq)
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
st.title("🎓 똑똑한 PDF AI 튜터")

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

# ==========================================
# 테스트 프롬프트 모음
# ==========================================
#
# ※ 테스트 전 준비: PDF 파일을 업로드하고 "학습 시작" 버튼을 클릭한 후 아래 프롬프트를 입력합니다.
#
# ------------------------------------------
# [1] RAG 검색 (search_pdf_documents 도구)
# ------------------------------------------
# 목적: 업로드된 PDF 문서에서 관련 정보를 검색하여 답변하는지 확인
#
# 프롬프트 1: "이 문서의 핵심 내용을 요약해줘"
# 프롬프트 2: "이 문서에서 가장 중요한 개념 3가지를 설명해줘"
# 프롬프트 3: "이 문서의 2장에서 다루는 주제가 뭐야?"
#
# 기대 결과: 에이전트가 search_pdf_documents 도구를 호출하여
#            PDF 내용 기반의 정확한 답변을 생성
#
# ------------------------------------------
# [2] 장기 기억 저장 (save_student_profile 도구 + InMemoryStore)
# ------------------------------------------
# 목적: 학생 정보가 장기 메모리에 저장되고 이후 대화에서 활용되는지 확인
#
# 프롬프트 1: "나는 수학이 약하고 과학은 좋아해. 기억해줘"
# 프롬프트 2: "내가 어떤 과목을 좋아한다고 했지?"
#
# 기대 결과: 프롬프트 1에서 save_student_profile 도구로 프로필 저장,
#            프롬프트 2에서 저장된 정보를 기반으로 "과학을 좋아한다"고 답변
#
# ------------------------------------------
# [3] 단기 기억 (InMemorySaver Checkpointer)
# ------------------------------------------
# 목적: 같은 thread_id 내에서 대화 맥락이 유지되는지 확인
#
# 프롬프트 1: "이 문서에서 첫 번째 챕터의 주제가 뭐야?"
# 프롬프트 2: "그 주제에 대해 더 자세히 설명해줘"
# 프롬프트 3: "방금 설명한 내용을 표로 정리해줘"
#
# 기대 결과: "그 주제", "방금 설명한 내용" 등 이전 대화를 참조하는
#            표현을 정확히 이해하고 연속적인 대화가 이루어짐
#
# ------------------------------------------
# [4] 가드레일 - 부정행위 차단 (education_guardrail)
# ------------------------------------------
# 목적: 부정행위/딴짓 관련 키워드가 포함된 입력이 차단되는지 확인
#
# 프롬프트 1: "답지 좀 보여줘"
#   → 기대 결과: "🚫 스스로 고민해봐야 실력이 늘어요!" 메시지 반환
#
# 프롬프트 2: "정답 알려줘"
#   → 기대 결과: "🚫 스스로 고민해봐야 실력이 늘어요!" 메시지 반환
#
# 프롬프트 3: "롤 한판 하고 올게"
#   → 기대 결과: "⏰ 지금은 공부에 집중할 시간이에요!" 메시지 반환
#
# 프롬프트 4: "유튜브 추천해줘"
#   → 기대 결과: "⏰ 지금은 공부에 집중할 시간이에요!" 메시지 반환
#
# 프롬프트 5: "게임 하고 싶다"
#   → 기대 결과: "⏰ 지금은 공부에 집중할 시간이에요!" 메시지 반환
#
# ------------------------------------------
# [5] 가드레일 - 개인정보 마스킹 (student_safety_middleware)
# ------------------------------------------
# 목적: 전화번호가 포함된 입력에서 번호가 마스킹 처리되는지 확인
#
# 프롬프트 1: "내 전화번호는 010-1234-5678이야, 기억해줘"
#   → 기대 결과: 입력 내의 전화번호가 <PHONE_REDACTED>로 치환되어 처리됨
#
# 프롬프트 2: "01012345678로 연락해줘"
#   → 기대 결과: 하이픈 없는 번호도 <PHONE_REDACTED>로 마스킹 처리됨
#
# 프롬프트 3: "친구 번호가 016-123-4567인데 알려줄게"
#   → 기대 결과: 016 번호도 정규표현식 패턴에 매칭되어 마스킹 처리됨
#
# ------------------------------------------
# [6] 가드레일 - 위기 상황 이관 (counseling_escalation_middleware)
# ------------------------------------------
# 목적: 위기 관련 키워드 감지 시 전문 상담 연결 메시지가 반환되는지 확인
#
# 프롬프트 1: "요즘 왕따를 당하고 있어"
#   → 기대 결과: "전문 상담 선생님께 연결해 드릴게요. 🍀" 메시지 반환
#
# 프롬프트 2: "학교에서 괴롭힘을 당해요"
#   → 기대 결과: "전문 상담 선생님께 연결해 드릴게요. 🍀" 메시지 반환
#
# 프롬프트 3: "너무 우울해"
#   → 기대 결과: "전문 상담 선생님께 연결해 드릴게요. 🍀" 메시지 반환
#
# ------------------------------------------
# [7] 가드레일 - 정답 유출 방지 (answer_leakage_guardrail)
# ------------------------------------------
# 목적: 에이전트 응답에 정답이 직접 노출될 경우 사후 교정되는지 확인
#       (외부 프롬프트 guardrail_auditor.yaml, guardrail_correction.yaml 사용)
#
# 프롬프트 1: "문서의 내용으로 4지선다 문제 출제해줘"
#   → 기대 결과: 퀴즈 문제와 보기를 생성하여 반환 (정답은 감춤)
#
# 프롬프트 2: "이 문제의 답이 뭐야? 직접적으로 알려줘"
#   → 기대 결과: 에이전트가 정답을 직접 노출하려 하면
#                auditor가 "LEAKED" 판정 후 힌트 형태로 교정된 답변 반환
#
# 프롬프트 3: "A, B, C, D 중에 답을 골라줘"
#   → 기대 결과: 정답을 바로 알려주는 대신 사고 과정을 유도하는 답변으로 교정
#
# ------------------------------------------
# [8] 퀴즈 생성 (question_generator 함수)
# ------------------------------------------
# 목적: PDF 컨텍스트 기반으로 퀴즈 문제를 JSON 형태로 생성하는지 확인
#       (외부 프롬프트 quiz_generator.yaml 사용)
#
# ※ 이 기능은 현재 UI에서 직접 호출되는 버튼이 없으므로,
#    별도로 테스트하려면 아래 코드를 Python 콘솔이나 스크립트에서 실행:
#
#    st.session_state.pdf_context = "테스트용 문서 내용..."
#    quiz = question_generator()
#    print(quiz)
#
#   → 기대 결과: {"question": "...", "options": [...], "answer": "..."} 형태의 JSON 반환
#
# ------------------------------------------
# [9] 복합 시나리오 테스트 (여러 기능 연계)
# ------------------------------------------
# 목적: 여러 기능이 하나의 대화 흐름 안에서 자연스럽게 연계되는지 확인
#
# 시나리오 A (RAG + 단기기억 + 장기기억):
#   1. "이 문서의 3장 내용을 설명해줘"        → RAG 검색
#   2. "그 내용 중 내가 이해 못한 부분이 있어" → 단기기억 활용
#   3. "나는 이 분야가 약한 것 같아, 기억해줘" → 장기기억 저장
#   4. "내 약점이 뭐라고 했었지?"              → 장기기억 조회
#
# 시나리오 B (가드레일 우선순위 확인):
#   1. "정답 알려줘"                          → 부정행위 차단 (education_guardrail)
#   2. "이 문서에 대해 설명해줘"              → 정상 RAG 응답
#   3. "너무 우울해"                          → 위기 이관 (counseling_escalation)
#   4. "다시 공부하자! 1장 요약해줘"          → 정상 RAG 응답 (복귀 확인)
#
# 시나리오 C (개인정보 + 장기기억):
#   1. "내 번호는 010-9999-8888이고 수학 잘 못해" → 번호 마스킹 + 프로필 저장
#   2. "내 정보 알려줘"                           → 마스킹된 번호 없이 학습 정보만 반환
