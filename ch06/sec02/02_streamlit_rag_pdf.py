import streamlit as st
from langchain_core.messages.chat import ChatMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
# from langchain_community.document_loaders import PDFPlumberLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

import os
from dotenv import load_dotenv

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")


st.title("PDF 기반 QA")

if not os.path.exists(".cache"):
    os.mkdir(".cache")

if not os.path.exists(".cache/files"):  # 폴더 앞에 .을 붙이면 숨김 처리함을 의미
    os.mkdir(".cache/files")

if not os.path.exists(".cache/embeddings"):
    os.mkdir(".cache/embeddings")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

with st.sidebar:
    clear_btn = st.button("대화 초기화")

    uploaded_file = st.file_uploader("파일 업로드", type=["pdf"])

    # selected_prompt = "prompts/pdf-rag.yaml"


@st.cache_resource(show_spinner="업로드한 파일을 처리 중입니다...")
def embed_file(file):
    file_content = file.read()
    file_path = f"./.cache/files/{file.name}"
    with open(file_path, "wb") as f:
        f.write(file_content)

    # 문서 로드
    # loader = PDFPlumberLoader(file_path)
    loader = PyMuPDFLoader(file_path)
    documents = loader.load()

    # 문서 분할
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    splitted_documents = text_splitter.split_documents(documents)

    # 임베딩 모델 준비
    embedding_model = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=gemini_api_key,
        # Streamlit의 동기적인 환경과 호환되도록 설정(GoogleGenerativeAIEmbeddings는 기본값은 비동기)
        transport='rest'
    )

    vectorstore = FAISS.from_documents(splitted_documents, embedding_model)

    # FAISS 벡터스토어가 존재하는 경우에는 덮어쓰기 하지 않고 로드
    # FAISS_INDEX_PATH = "faiss_index"
    # vectorstore = None
    # if os.path.exists(FAISS_INDEX_PATH):
    #     print(f"FAISS 인덱스 {FAISS_INDEX_PATH}를 로드합니다.")
    #     vectorstore = FAISS.load_local(
    #         FAISS_INDEX_PATH,
    #         embedding_model,
    #         allow_dangerous_deserialization=True,
    #     )
    # else:
    #     print(f"FAISS 인덱스 {FAISS_INDEX_PATH}가 없으므로 생성합니다.")
    #     # FAISS 벡터스토어 생성 및 저장
    #     vectorstore = FAISS.from_documents(splitted_documents, embedding_model)
    #     vectorstore.save_local(FAISS_INDEX_PATH)
    #     print(f"FAISS 인덱스를 {FAISS_INDEX_PATH}에 저장했습니다.")

    # 리트리버 생성
    retriever = vectorstore.as_retriever()
    return retriever

# def create_chain(prompt_filepath):


def create_chain(retriever):
    prompt = PromptTemplate.from_template(
        '''다음 컨텍스트만 사용해 질문에 답하세요.
    컨텍스트:{context}

    질문: {question}
    '''
    )

    # prompt = load_prompt(prompt_filepath, encoding="utf-8")

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


if clear_btn:
    st.session_state["messages"] = []

if "mesages" not in st.session_state:
    st.session_state["messages"] = []

if "chain" not in st.session_state:
    st.session_state["chain"] = None

if uploaded_file:
    retriever = embed_file(uploaded_file)
    chain = create_chain(retriever)
    st.session_state["chain"] = chain


print_messages()

user_input = st.chat_input("궁금한 내용을 물어보세요!")

warning_msg = st.empty()

if user_input:
    chain = st.session_state["chain"]

    if chain is not None:

        st.chat_message("user").write(user_input)
        response = chain.stream(user_input)

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
# query = "Advance RAG 기법이 임상시험 데이터 분석에서 수행하는 주요 역할은 무엇인가요?"
# query = "본 연구에서 Private LLM 성능을 평가하기 위해 사용한 지표 3가지는 무엇인가요?"
query = "본 연구에서 Private LLM 구축을 위해 수집한 문서의 총 페이지 수와 문서 유형별 비율은 어떻게 되나요?"
# query = "ROUGE 평가에서 Private LLM과 ChatGPT의 Recall 값은 각각 얼마였나요?"
