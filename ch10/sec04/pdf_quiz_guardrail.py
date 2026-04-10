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
from langchain.agents.middleware import before_agent, after_agent
from langchain.messages import SystemMessage, AIMessage, HumanMessage

load_dotenv()

chat = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    transport='rest'
)
db_path = "faiss_index_pdf_quiz"

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

# ==========================================
# [가드레일 가이드] 주요 보안 및 교육용 미들웨어 설정
# ==========================================

# 1. 감시 및 교정을 위한 별도의 모델 인스턴스 생성
# (실제 답변을 생성하는 에이전트와 분리하여 공정하고 엄격한 검토 수행)
safety_model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")

# 2. 필터링할 금지 키워드 및 에스컬레이션 키워드 사전 정의
forbidden_topics = {
    # 학생이 스스로 문제를 풀지 않고 정답을 요구하는 경우를 방지하기 위한 키워드
    "cheating": ["답지", "정답 알려줘", "숙제 대신", "써줘", "베끼기"],
    # 학습 시간 중 집중을 방해하는 게임이나 엔터테인먼트 관련 키워드
    "distraction": ["롤", "게임", "유튜브", "아이돌", "웹툰", "웃긴"],
    # 교육 서비스 내에서 부적절한 언어나 위험 요소를 차단하기 위한 키워드
    "harmful": ["담배", "술", "폭력", "싸움", "바보"]
}

# 심리적 불안정, 학교 폭력 등 전문가의 개입이 필요한 심각한 상황을 감지하기 위한 키워드
ESCALATION_KEYWORDS = ["왕따", "괴롭힘", "우울해", "학교 폭력", "상담 선생님", "사람 불러줘"]

# 3. [미들웨어 A] 교육 가드레일 (사전 차단)
# 에이전트가 답변을 생성하기 전(before_agent)에 호출되어 질문의 적절성 검사
@before_agent(can_jump_to=["end"])
def education_guardrail(state, runtime):
    """
    사용자의 질문이 교육적으로 부적절하거나 부정행위 의도가 있는 경우
    LLM 본체로 질문을 전달하지 않고 즉시 교육적인 피드백을 주며 대화를 종료(jump_to=end)합니다.
    """
    if not state["messages"]:
        return None

    last_message = state["messages"][-1]
    
    # 메시지 타입 유연성 확보 (dict 형태와 LangChain 객체 형태 모두 지원)
    if isinstance(last_message, dict):
        user_text = last_message.get("content", "")
    else:
        user_text = getattr(last_message, "content", str(last_message))

    # [카테고리 1] 부정행위 방지: 스스로 생각하도록 유도하는 멘트 제공
    for keyword in forbidden_topics["cheating"]:
        if keyword in user_text:
            return {
                "messages": [{"role": "assistant", "content": "🚫 스스로 고민해봐야 실력이 늘어요! 정답을 바로 알려드리는 대신, 힌트를 드릴까요? 어떤 부분이 가장 어려운지 말해주세요."}],
                "jump_to": "end" # AI 답변 생성을 건너뛰고 바로 출력 단계로 점프
            }

    # [카테고리 2] 학습 집중 유도: 주의 환기 및 현재 학습에 집중하도록 독려
    for keyword in forbidden_topics["distraction"]:
        if keyword in user_text:
            return {
                "messages": [{"role": "assistant", "content": "⏰ 지금은 공부에 집중할 시간이에요! 딴짓은 쉬는 시간에 하고, 지금 풀고 있는 문제에 집중해볼까요?"}],
                "jump_to": "end"
            }

    # [카테고리 3] 유해 콘텐츠 차단: 부적절한 주제에 대해 경고 및 거절
    for keyword in forbidden_topics["harmful"]:
        if keyword in user_text:
            return {
                "messages": [{"role": "assistant", "content": "⚠️ 부적절한 대화 주제입니다. 바르고 고운 말을 사용해주세요."}],
                "jump_to": "end"
            }
    return None

# 4. [미들웨어 B] 개인정보 보호 가드레일 (사전 필터링)
# 에이전트에게 정보를 넘기기 전, 민감한 개인정보를 마스킹하여 AI에게 전달
@before_agent
def student_safety_middleware(state, runtime):
    """
    사용자의 메시지에서 전화번호나 이메일 패턴을 찾아 <PHONE_REDACTED> 등으로 마스킹 처리합니다.
    이를 통해 외부 모델(클라우드 서비스)로 개인정보가 유출되는 것을 원천 차단합니다.
    """
    if not state["messages"]: return None
    last_message = state["messages"][-1]
    
    content = last_message.get("content", "") if isinstance(last_message, dict) else getattr(last_message, "content", "")
    if not content: return None

    # 전화번호(010 계열) 및 이메일의 정규표현식 패턴 정의
    phone_pattern = r'01[016789]-?[0-9]{3,4}-?[0-9]{4}'
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    is_redacted = False
    # 감지된 패턴을 마스킹 된 문자열로 치환
    if re.search(phone_pattern, content):
        content = re.sub(phone_pattern, '<PHONE_REDACTED>', content)
        is_redacted = True
    if re.search(email_pattern, content):
        content = re.sub(email_pattern, '<EMAIL_REDACTED>', content)
        is_redacted = True

    # 원래의 메시지 내용을 마스킹된 내용으로 수정 (에이전트는 마스킹된 버전만 보게 됨)
    if is_redacted:
        if isinstance(last_message, dict):
            last_message["content"] = content
        else:
            last_message.content = content
    return None

# 5. [미들웨어 C] 상담 이관 가드레일 (위기 감지 및 에스컬레이션)
# 위험 상황 감지 시 대화를 중단하고 전문가(인간) 상담을 안내
@before_agent(can_jump_to=["end"])
def counseling_escalation_middleware(state, runtime):
    """
    심리적 고통이나 학교 폭력 등 위급한 키워드를 감지하면 
    AI의 답변을 차단하고, 따뜻한 위로와 함께 전문가 연결 안내를 제공합니다.
    """
    if not state["messages"]: return None
    last_message = state["messages"][-1]
    content = last_message.get("content", "") if isinstance(last_message, dict) else getattr(last_message, "content", "")

    for keyword in ESCALATION_KEYWORDS:
        if keyword in content:
            return {
                "messages": [{
                    "role": "assistant",
                    "content": "학생, 많이 힘들었겠구나. 이 문제는 내가 답변하기보다는 전문 상담 선생님이 직접 듣고 도와주시는 게 좋을 것 같아. \n\n지금 바로 상담 선생님께 연결해 드릴 수 있도록 주변에 도움을 정하는 게 어떨까? 🍀"
                }],
                "jump_to": "end"
            }
    return None

# 6. [미들웨어 D] 정답 유출 방지 가드레일 (사후 검증 및 교정)
# AI가 답변을 생성한 직후(after_agent)에 실행되어 답변 내용의 적절성 평가
@after_agent
def answer_leakage_guardrail(state, runtime):
    """
    에이전트가 생성한 답변이 문제의 정답을 직접 노출해버렸는지 감시자 AI를 통해 확인합니다.
    만약 정답이 유출되었다면, 답변을 폐기하고 힌트 형식의 답변으로 재설명하도록 유도합니다.
    """
    if not state["messages"]: return None
    last_message = state["messages"][-1]

    # AI가 생성한 마지막 응답 메시지 추출
    content = last_message.get("content", "") if isinstance(last_message, dict) else getattr(last_message, "content", "")
    role = last_message.get("role", "") if isinstance(last_message, dict) else ("assistant" if isinstance(last_message, AIMessage) else "")
    
    if role != "assistant" or not content:
        return None

    # [검증 단계] 감시자용 프롬프트를 통해 정답 유출 여부 판단 (LEAKED vs SAFE)
    auditor_prompt = f"""
    당신은 엄격한 교육 감독관입니다.
    다음 '튜터의 답변'을 확인하세요.
    답변이 학생을 지도하지 않고 문제의 정답이나 전체 풀이를 직접적으로 제공한다면 'LEAKED'라고 답하세요.
    답변이 적절한 힌트나 설명을 제공한다면 'SAFE'라고 답하세요.

    튜터의 답변: {content}
    """
    result = safety_model.invoke([{"role": "user", "content": auditor_prompt}])

    # [교정 단계] 유출이 감지되면 소크라테스식(질문을 통한 유도) 교육법으로 응답 재구성
    if "LEAKED" in result.content:
        # 사용자의 원본 질문을 참고하여 문맥에 맞는 힌트 생성
        original_msg = state["messages"][-2]
        original_question = original_msg.get("content", "") if isinstance(original_msg, dict) else getattr(original_msg, "content", "")

        correction_prompt = f"""
        당신은 친절한 AI 튜터입니다.
        절대 정답을 직접 말하지 말고, 학생이 스스로 생각할 수 있도록 유도하는 질문이나 핵심 개념(힌트)만 설명하세요.
        말투는 친절하게 해주세요.

        사용자 질문: {original_question}
        """
        corrected_response = safety_model.invoke([
            SystemMessage(content="당신은 소크라테스식 교육법을 사용하는 튜터입니다."),
            HumanMessage(content=correction_prompt)
        ])
        
        # 유출된 원래 답변을 교정된(Safe) 답변으로 덮어씌움
        if isinstance(last_message, dict):
            last_message["content"] = corrected_response.content
        else:
            last_message.content = corrected_response.content

    return None

def parse_ai_json(ai_response):
    try:
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        st.error(f"JSON 파싱 오류: {e}")
    return None

@st.cache_resource
def get_vectorstore():
    if os.path.exists(db_path):
        return FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
    return None

st.session_state.vectorstore = get_vectorstore()

def load_and_parse_pdf(pdf_path):
    loader = PyMuPDFLoader(pdf_path)
    docs = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    split_docs = text_splitter.split_documents(docs)

    st.session_state.vectorstore = FAISS.from_documents(split_docs, embeddings)
    st.session_state.vectorstore.save_local(db_path)
    
    get_vectorstore.clear()
    
    st.session_state.pdf_context = "\n".join([doc.page_content for doc in docs])

@tool
def search_pdf_documents(query: str) -> str:
    """업로드된 PDF 문서 내에서 정보를 검색합니다. 
    사실 확인이나 전문적인 내용이 필요할 때 사용하세요.
    """
    vectorstore = st.session_state.get("vectorstore")
    if vectorstore is None:
        vectorstore = get_vectorstore()
        
    if vectorstore is not None:
        docs = vectorstore.similarity_search(query, k=3)
        return "\n\n".join([doc.page_content for doc in docs])
    return "검색할 문서가 없습니다."

def initialize_agent():
    system_prompt = """당신은 업로드된 PDF 문서를 바탕으로 학습을 돕는 교육 전문가입니다.
    1. 사용자의 질문에 대해 'search_pdf_documents' 도구를 사용하여 정확한 정보를 찾으세요.
    2. 답변은 반드시 검색된 문서의 내용에만 기반하여 한국어로 작성하세요.
    3. 문서에 관련 내용이 없다면 억지로 꾸며내지 말고 솔직하게 모른다고 답변하세요.
    """
    
    # 에이전트 생성 시 정의한 4계층 가드레일 미들웨어를 장착하여 보안 및 교육 철학 관철
    st.session_state.agent = create_agent(
        model="google_genai:gemini-2.5-flash",
        tools=[search_pdf_documents],
        system_prompt=system_prompt,
        middleware=[
            education_guardrail,             # 1단계: 입력 필터 (규칙 기반)
            student_safety_middleware,       # 2단계: 개인정보 보호 (마스킹)
            counseling_escalation_middleware,# 3단계: 상담 이관 (에스컬레이션)
            answer_leakage_guardrail         # 4단계: 출력 필터 (모델 기반 교정)
        ]
    )

def general_response(user_message):
    if st.session_state.agent:
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[-5:]]
        result = st.session_state.agent.invoke({"messages": history + [{"role": "user", "content": user_message}]})
        
        ai_msg = result["messages"][-1]
        content = ai_msg.content
        
        if isinstance(content, list):
            text_parts = [part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"]
            return "".join(text_parts)
        
        return content
    return "에이전트가 설정되지 않았습니다."

def question_generator():
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
    content = ai_response.content
    
    if isinstance(content, list):
        content = "".join([part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"])
    
    return parse_ai_json(content)

def check_answer(user_message):
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

st.title("📖 PDF AI 퀴즈 챗봇")

with st.sidebar:
    st.header("⚙️ 설정")
    st.session_state.mode = st.radio(
        "학습 모드 선택",
        ["퀴즈 풀기", "질문하기"],
        help="퀴즈를 풀며 학습하거나, 문서에 대해 자유롭게 질문하세요."
    )
    
    if st.session_state.wrong_answers:
        st.write("---")
        st.write(f"❌ 틀린 문제: {len(st.session_state.wrong_answers)}개")
        if st.button("오답 노트 초기화"):
            st.session_state.wrong_answers = []
            st.rerun()

uploaded_file = st.file_uploader("PDF 파일을 업로드하세요", type="pdf")
if st.button("학습 시작") and uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name
    
    with st.spinner("문서를 분석 중..."):
        load_and_parse_pdf(tmp_path)
        initialize_agent()
        st.session_state.pdf_processed = True
        
        if st.session_state.mode == "퀴즈 풀기":
            q = question_generator()
            st.session_state.current_question = q
            if q:
                msg = q['question'] + "\n\n" + "\n".join(q['options'])
                st.session_state.messages.append({"role": "assistant", "content": msg})
        else:
            st.session_state.messages.append({"role": "assistant", "content": "문서 분석이 완료되었습니다! 분석된 내용에 대해 무엇이든 물어보세요."})
    os.unlink(tmp_path)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("메시지를 입력하세요"):
    if not st.session_state.pdf_processed:
        st.warning("먼저 PDF 파일을 업로드하고 '학습 시작'을 눌러주세요.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.write(prompt)

    with st.chat_message("assistant"):
        if st.session_state.mode == "퀴즈 풀기":
            ans_check = check_answer(prompt)
            if ans_check:
                st.write(ans_check)
                st.session_state.messages.append({"role": "assistant", "content": ans_check})
                with st.spinner("다음 문제를 생성 중..."):
                    new_q = question_generator()
                    st.session_state.current_question = new_q
                    if new_q:
                        msg = new_q['question'] + "\n\n" + "\n".join(new_q['options'])
                        st.write("---")
                        st.write(msg)
                        st.session_state.messages.append({"role": "assistant", "content": msg})
            else:
                guide = "퀴즈 풀기 모드입니다. 정답 번호(1~4)를 입력해 주세요. 문질문에 답변을 듣고 싶다면 사이드바에서 '질문하기' 모드로 변경해 주세요."
                st.info(guide)
                st.session_state.messages.append({"role": "assistant", "content": guide})
        else:
            with st.spinner("답변을 찾는 중..."):
                resp = general_response(prompt)
                st.write(resp)
                st.session_state.messages.append({"role": "assistant", "content": resp})
