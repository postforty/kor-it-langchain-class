import streamlit as st
from langchain_core.messages.chat import ChatMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
# from langchain_community.document_loaders import PDFPlumberLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
# from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import load_prompt
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import OllamaEmbeddings

import shutil # 파일 및 디렉토리 작업용
import uuid # 고유 키 생성을 위한 uuid 모듈 임포트

import os
from dotenv import load_dotenv
load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

st.title("PDF 기반 QA봇")
st.caption("Ollama BGE-M3 + Gemini-2.5-FLASH")

if not os.path.exists(".cache"):
    os.mkdir(".cache")

if not os.path.exists(".cache/files"):  # 폴더 앞에 .을 붙이면 숨김 처리함(Linux, macOS)을 의미
    os.makedirs(".cache/files")
    # Windows에서 .cache 폴더를 숨김 처리
    if os.name == 'nt':
        os.system('attrib +h .cache')

if not os.path.exists(".cache/embeddings"):
    os.mkdir(".cache/embeddings")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "chain" not in st.session_state:
    st.session_state["chain"] = None

# 헬퍼 함수 정의
# 벡터스토어 생성 또는 로드
def _get_or_create_vectorstore(file_name, splitted_documents=None):
    # * bge-m3 임베딩 모델 준비
    # OllamaEmbeddings 랭체인 문서: https://python.langchain.com/docs/integrations/text_embedding/ollama/
    embedding_model = OllamaEmbeddings(
        model="bge-m3",
    )

    embedding_path = f".cache/embeddings/{file_name}"
    vectorstore = None
    if splitted_documents is not None:  # If new documents are provided, always create
        print(f"FAISS 인덱스 {embedding_path}를 생성합니다.")
        if os.path.exists(embedding_path):  # Remove old one if exists
            shutil.rmtree(embedding_path)
        vectorstore = FAISS.from_documents(splitted_documents, embedding_model)
        vectorstore.save_local(embedding_path)
        print(f"FAISS 인덱스를 {embedding_path}에 저장했습니다.")
    elif os.path.exists(embedding_path):  # Otherwise, try to load existing
        print(f"FAISS 인덱스 {embedding_path}를 로드합니다.")
        vectorstore = FAISS.load_local(
            embedding_path,
            embedding_model,
            allow_dangerous_deserialization=True,
        )

    return vectorstore


@st.cache_resource(show_spinner="업로드한 파일 처리 중...", ttl=3600) # ttl=3600으로 1시간 동안 캐시된 결과 사용 가능, 불필요한 연산 줄임(필수 아님)
def embed_file(file):
    file_content = file.read()
    file_path = f"./.cache/files/{file.name}"
    with open(file_path, "wb") as f:
        f.write(file_content)

    # # 문서 로드
    # loader = PDFPlumberLoader(file_path)
    loader = PyMuPDFLoader(file_path)
    documents = loader.load()

    # 문서 분할
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    splitted_documents = text_splitter.split_documents(documents)

    # print("splitted_documents:", splitted_documents)

    # 벡터스토어 생성 또는 로드
    vectorstore = _get_or_create_vectorstore(file.name, splitted_documents)

    # 리트리버 생성
    retriever = vectorstore.as_retriever()
    print("retriever:", retriever)

    return retriever

def create_chain(retriever, prompt_filepath):
    prompt = load_prompt(prompt_filepath, encoding="utf-8")

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=gemini_api_key)

    output_parsers = StrOutputParser()

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | output_parsers
    )

    return chain

def print_messages():
    for chat_message in st.session_state["messages"]:
        st.chat_message(chat_message.role).write(chat_message.content)

def add_message(role, message):
    st.session_state["messages"].append(
        ChatMessage(role=role, content=message))

def clear_task():
    st.session_state["messages"] = []
    st.session_state["chain"] = None

    # 파일 업로더 키를 'clear' 상태로 설정
    st.session_state.file_uploader_key = str(uuid.uuid4())  # 고유한 키로 업데이트
    st.session_state.uploaded_file = None

    # .cache/files 및 .cache/embeddings 폴더 삭제 후 재생성
    # 대화 초기화 버튼 클릭하면 해당 폴더와 기존 데이터를 삭제하고 빈 폴더만 다시 생성
    if os.path.exists(".cache/files"):
        shutil.rmtree(".cache/files")
    os.makedirs(".cache/files")
    if os.path.exists(".cache/embeddings"):
        shutil.rmtree(".cache/embeddings")
    os.makedirs(".cache/embeddings")


with st.sidebar:
    clear_btn = st.button("대화 초기화", on_click=clear_task) # on_click 인자로 clear_task 함수를 직접 호출

    # `st.session_state.file_uploader_key`의 상태를 확인하여 업로더를 조건부로 렌더링
    if 'file_uploader_key' not in st.session_state:
        st.session_state.file_uploader_key = str(uuid.uuid4())  # 초기 로드 시 키 생성

    uploaded_file = st.file_uploader(
        "파일 업로드", type=["pdf"], key=st.session_state.file_uploader_key)  # 초기화 삭제 위해 고유키 관리

    selected_prompt = "prompts/pdf-rag.yaml"

# 프로그램 시작 시 또는 다시 시작될 때 기존 벡터 저장소 로드
if st.session_state["chain"] is None:
    embedding_files = [f for f in os.listdir(
        ".cache/embeddings") if os.path.isdir(os.path.join(".cache/embeddings", f))]

    print("embedding_files:", embedding_files)

    if embedding_files:
        # 첫 번째 발견된 임베딩 파일을 로드
        first_embedding_file = embedding_files[0]
        vectorstore = _get_or_create_vectorstore(first_embedding_file)
        if vectorstore:
            retriever = vectorstore.as_retriever()
            st.session_state["chain"] = create_chain(
                retriever, selected_prompt)
            st.success(f"기존 벡터 저장소 '{first_embedding_file}'를 로드했습니다.")

# print("uploaded_file:", uploaded_file)

if uploaded_file:
    retriever = embed_file(uploaded_file)
    chain = create_chain(retriever, selected_prompt)
    st.session_state["chain"] = chain

user_input = st.chat_input("무엇이 궁궁하신가요?")

warning_msg = st.empty()

if user_input:
    if st.session_state["chain"] is not None:
        st.chat_message("user").write(user_input)
        response = st.session_state["chain"].stream(user_input)

        with st.chat_message("assistant"):
            container = st.empty()

            ai_answer = ""

            for token in response:
                ai_answer += token
                container.markdown(ai_answer)

        add_message("user", user_input)
        add_message("assistant", ai_answer)
    else:
        warning_msg.error("파일을 업로드해 주세요.")

print("st.session_state.messages:", st.session_state.messages)

# 질문 예시
# Advance RAG 기법이 임상시험 데이터 분석에서 수행하는 주요 역할은 무엇인가요?
# 본 연구에서 Private LLM 성능을 평가하기 위해 사용한 지표 3가지는 무엇인가요?
# PDF문서 5쪽 - 본 연구에서 Private LLM 구축을 위해 수집한 문서의 총 페이지 수와 문서 유형별 비율은 어떻게 되나요?
# PDF문서 10쪽 - ROUGE 평가에서 Private LLM과 ChatGPT의 Recall 값은 각각 얼마였나요?
