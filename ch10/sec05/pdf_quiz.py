import streamlit as st
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, load_prompt # 추가
import tempfile
import os
import json
import re
from dotenv import load_dotenv

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
    vectorstore = st.session_state.get("vectorstore")
    if vectorstore is None:
        vectorstore = get_vectorstore()
        
    if vectorstore is not None:
        docs = vectorstore.similarity_search(query, k=3)
        return "\n\n".join([doc.page_content for doc in docs])
    return "검색할 문서가 없습니다."

def initialize_agent():
    # prompts/pdf_quiz_agent.yaml: 교육 전문가로서 PDF 검색 도구를 활용해 답변하도록 지시하는 시스템 프롬프트를 로드합니다.
    prompt_template = load_prompt("prompts/pdf_quiz_agent.yaml", encoding="utf-8")
    system_prompt = prompt_template.format()
    
    st.session_state.agent = create_agent(
        model=chat,
        tools=[search_pdf_documents],
        system_prompt=system_prompt
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
    # prompts/pdf_quiz_generator.yaml: PDF 컨텍스트로부터 4지선다 객관식 퀴즈를 JSON 형식으로 생성하기 위한 프롬프트를 로드합니다.
    prompt = load_prompt("prompts/pdf_quiz_generator.yaml", encoding="utf-8")
    
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
