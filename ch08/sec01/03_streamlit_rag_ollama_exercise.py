import streamlit as st
from langchain_core.messages.chat import ChatMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import load_prompt

# [미션] langchain_ollama 에서 필요한 모듈을 임포트하세요.
# from langchain_ollama import ...

import shutil # 파일 및 디렉토리 작업용
import uuid # 고유 키 생성을 위한 uuid 모듈 임포트
import os
from dotenv import load_dotenv

load_dotenv()

st.title("PDF 기반 QA봇 (Ollama 실습)")
st.caption("실습: Ollama Embeddings + Ollama LLM")

if not os.path.exists(".cache"):
    os.mkdir(".cache")
    if os.name == 'nt':
        os.system('attrib +h .cache')

if not os.path.exists(".cache/files"): 
    os.makedirs(".cache/files")
    
if not os.path.exists(".cache/embeddings"):
    os.mkdir(".cache/embeddings")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

if "chain" not in st.session_state:
    st.session_state["chain"] = None

# 헬퍼 함수 정의
# 벡터스토어 생성 또는 로드
def _get_or_create_vectorstore(file_name, splitted_documents=None):
    # [미션] OllamaEmbeddings 모델을 설정하세요.
    # 힌트: model="bge-m3"
    embedding_model = None  # 코드를 작성하세요.

    if embedding_model is None:
        raise ValueError("임베딩 모델이 설정되지 않았습니다. 코드를 완성해주세요.")

    embedding_path = f".cache/embeddings/{file_name}"
    vectorstore = None
    if splitted_documents is not None:
        print(f"FAISS 인덱스 {embedding_path}를 생성합니다.")
        if os.path.exists(embedding_path):
            shutil.rmtree(embedding_path)
            
        vectorstore = FAISS.from_documents(splitted_documents, embedding_model)
        vectorstore.save_local(embedding_path)
        print(f"FAISS 인덱스를 {embedding_path}에 저장했습니다.")
    elif os.path.exists(embedding_path):
        print(f"FAISS 인덱스 {embedding_path}를 로드합니다.")
        vectorstore = FAISS.load_local(
            embedding_path,
            embedding_model,
            allow_dangerous_deserialization=True,
        )

    return vectorstore


@st.cache_resource(show_spinner="업로드한 파일 처리 중...", ttl=3600)
def embed_file(file):
    file_content = file.read()
    file_path = f"./.cache/files/{file.name}"
    with open(file_path, "wb") as f:
        f.write(file_content)

    loader = PyMuPDFLoader(file_path)
    documents = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    splitted_documents = text_splitter.split_documents(documents)

    vectorstore = _get_or_create_vectorstore(file.name, splitted_documents)
    
    if vectorstore is None:
        return None
        
    retriever = vectorstore.as_retriever()
    print("retriever:", retriever)

    return retriever

def create_chain(retriever, prompt_filepath):
    prompt = load_prompt(prompt_filepath, encoding="utf-8")

    # [미션] Ollama LLM 모델을 설정하세요.
    # 힌트: ChatOllama 또는 OllamaLLM을 사용하세요. (model="gemma2:2b" 또는 수강생이 보유한 모델 등)
    llm = None  # 코드를 작성하세요.
    
    if llm is None:
        raise ValueError("LLM이 설정되지 않았습니다. 코드를 완성해주세요.")

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
    st.session_state.file_uploader_key = str(uuid.uuid4())
    st.session_state.uploaded_file = None

    if os.path.exists(".cache/files"):
        shutil.rmtree(".cache/files")
    os.makedirs(".cache/files")
    if os.path.exists(".cache/embeddings"):
        shutil.rmtree(".cache/embeddings")
    os.makedirs(".cache/embeddings")


with st.sidebar:
    clear_btn = st.button("대화 초기화", on_click=clear_task)

    if 'file_uploader_key' not in st.session_state:
        st.session_state.file_uploader_key = str(uuid.uuid4())

    uploaded_file = st.file_uploader(
        "파일 업로드", type=["pdf"], key=st.session_state.file_uploader_key)

    selected_prompt = "prompts/pdf-rag.yaml"


if st.session_state["chain"] is None:
    embedding_files = [f for f in os.listdir(
        ".cache/embeddings") if os.path.isdir(os.path.join(".cache/embeddings", f))]

    print("embedding_files:", embedding_files)

    if embedding_files:
        first_embedding_file = embedding_files[0]
        try:
            vectorstore = _get_or_create_vectorstore(first_embedding_file)
            if vectorstore:
                retriever = vectorstore.as_retriever()
                st.session_state["chain"] = create_chain(
                    retriever, selected_prompt)
                st.success(f"기존 벡터 저장소 '{first_embedding_file}'를 로드했습니다.")
        except Exception as e:
            st.error(f"초기화 중 오류가 발생했습니다: {e}")

if uploaded_file:
    try:
        retriever = embed_file(uploaded_file)
        if retriever:
            chain = create_chain(retriever, selected_prompt)
            st.session_state["chain"] = chain
    except Exception as e:
        st.error(f"파일 처리 중 오류가 발생했습니다: {e}")

user_input = st.chat_input("무엇이 궁금하신가요?")

warning_msg = st.empty()

print_messages()

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
