import streamlit as st
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
import tempfile
import os
import json
import random
import re
import shutil
from dotenv import load_dotenv
load_dotenv()

# 세션 상태 초기화
if "chat_history_for_chain" not in st.session_state:
    st.session_state.chat_history_for_chain = ChatMessageHistory()
if "pdf_context" not in st.session_state:
    st.session_state.pdf_context = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "wrong_answers" not in st.session_state:
    st.session_state.wrong_answers = []
if "is_retest" not in st.session_state:
    st.session_state.is_retest = False

chat = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash")

# Langchain 모델 및 FAISS DB 초기화
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001", 
    transport='rest' # Streamlit의 동기적인 환경과 호환되도록 설정(GoogleGenerativeAIEmbeddings는 기본값은 비동기)
)
db_path = "faiss_index"

@st.cache_resource
def get_vector_store():
    # FAISS 인덱스 파일이 존재하면 로드
    if os.path.exists(db_path):
        try:
            return FAISS.load_local(db_path, embeddings, allow_dangerous_deserialization=True)
        except Exception as e:
            st.error(f"기존 FAISS DB 로드 중 오류 발생: {e}")
            return None
    # 파일이 없으면 None을 반환
    return None

st.session_state.vector_store = get_vector_store()

# --- 함수 정의 ---
def load_and_embed_pdf(pdf_path):
    """PDF 파일을 로드하고 FAISS에 임베딩합니다."""
    loader = UnstructuredFileLoader(pdf_path)
    docs = loader.load()
    
    if not docs:
        st.error("PDF에서 텍스트를 추출할 수 없습니다. 파일이 유효한지 확인해주세요.")
        return []

    # 텍스트 스플리터를 사용해 문서를 청크로 나눔
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    split_docs = text_splitter.split_documents(docs)

    if not split_docs:
        st.error("추출된 텍스트가 너무 짧거나 유효하지 않아 문제를 생성할 수 없습니다.")
        return []
    
    # FAISS에 임베딩 및 저장
    if st.session_state.vector_store:
        # DB가 존재하면 기존 DB에 문서 추가
        st.session_state.vector_store.add_documents(split_docs)
    else:
        # DB가 없으면 새로 생성
        st.session_state.vector_store = FAISS.from_documents(split_docs, embeddings)
    
    st.session_state.vector_store.save_local(db_path)
    
    # 디버깅을 위해 문서 수를 출력
    st.info(f"성공적으로 처리된 문서 청크 수: {len(split_docs)}개")
    
    return [doc.page_content for doc in split_docs]


def question_generator():
    """세션 상태에 저장된 PDF 문맥을 사용하여 질문을 생성합니다."""
    
    # FAISS DB에 의미 있는 문서가 있는지 확인
    if not st.session_state.vector_store:
        return None
    docs = st.session_state.vector_store.similarity_search("documents", k=1)
    if not docs or docs[0].page_content == "":
        return None
    
    if st.session_state.wrong_answers and random.random() < 0.5:
        st.session_state.is_retest = True
        return random.choice(st.session_state.wrong_answers)
    else:
        st.session_state.is_retest = False
        
        # 문제 생성용 컨텍스트 선택
        if st.session_state.get("latest_pdf_content") and random.random() < 0.5:
            pdf_context = st.session_state.get("latest_pdf_content")
        else:
            retriever = st.session_state.vector_store.as_retriever()
            docs = retriever.invoke("random documents", k=10)
            pdf_context = " ".join([doc.page_content for doc in docs])
        
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """당신은 제공된 텍스트에서 의미 있고 맥락적으로 관련된 객관식 문제(4지선다)를 생성하는 고급 질문 생성기입니다.
                    주어진 텍스트를 사용하여 한국어로 1개의 문제를 생성하세요. 답변을 포함하지 마세요.
                    결과를 다음 JSON 형식으로만 응답하세요.
                    {{
                        "question": "문제 내용",
                        "options": ["1. 보기1", "2. 보기2", "3. 보기3", "4. 보기4"],
                        "answer": "정답 번호 (1~4)",
                        "explanation": "문제에 대한 해설"
                    }}
                    \n\n
                    {context}""",
                ),
                (
                    "human",
                    "{input}"
                )
            ]
        )
        chain = prompt | chat
        try:
            ai_response = chain.invoke({
                "context": pdf_context, "input": "4지선다 1문항을 만들어 주세요."
            }).content
            
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            
            if json_match:
                json_string = json_match.group(0)
                response_json = json.loads(json_string)
                return response_json
            else:
                st.error("AI 응답에서 JSON을 찾을 수 없습니다. 다시 시도해주세요.")
                return None
            
        except json.JSONDecodeError as e:
            st.error("JSON 파싱 오류가 발생했습니다. 다시 시도해주세요.")
            return None


def display_question(q_data):
    """질문 데이터를 UI에 표시합니다."""
    st.session_state.messages.append(
        {"role": "assistant", "content": q_data['question']})
    st.session_state.messages.append(
        {"role": "assistant", "content": "\n".join(q_data['options'])})


def check_answer_and_proceed(user_message):
    """사용자 답변을 확인하고 다음 행동을 결정합니다."""
    q_data = st.session_state.current_question
    if not q_data:
        return "문제가 출제되지 않았습니다. PDF를 제출하여 시작해주세요."

    # 숫자가 아닌 다른 입력이면 일반 대화 처리
    try:
        user_answer = int(user_message.strip())
        correct_answer = int(q_data['answer'])

        if user_answer == correct_answer:
            response = "정답입니다! 🎉"
            if st.session_state.is_retest:
                response += " 이전에 틀렸던 문제였는데, 잘 맞추셨네요! 👍"
                # 정답 맞춘 문제는 오답 리스트에서 제거
                st.session_state.wrong_answers = [
                    q for q in st.session_state.wrong_answers if q['question'] != q_data['question']]

            st.session_state.messages.append(
                {"role": "assistant", "content": response})
            return response
        else:
            response = f"아쉽지만 정답이 아닙니다. 정답은 {correct_answer}번입니다. 😅\n\n**해설:**\n{q_data['explanation']}"

            # 틀린 문제 리스트에 추가 (중복 방지)
            if q_data not in st.session_state.wrong_answers:
                st.session_state.wrong_answers.append(q_data)

            st.session_state.messages.append(
                {"role": "assistant", "content": response})
            return response

    except ValueError:  # 사용자가 숫자가 아닌 다른 텍스트를 입력했을 경우
        return None  # 일반 대화 처리로 넘김


def general_response_generator(user_message):
    """일반적인 대화에 대한 응답을 생성합니다."""
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
                사용자가 올바르게 대답했다면, 다음 질문을 해주세요.
                사용자가 답변하지 않았거나 틀렸을 경우, 제공된 텍스트를 바탕으로 설명해 주시기 바랍니다.
                한국어로 대답해야 합니다.
                제공된 텍스트: {context}""",
            ),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
        ]
    )
    chain = prompt | chat

    chain_with_message_history = RunnableWithMessageHistory(
        chain,
        lambda session_id: st.session_state.chat_history_for_chain,
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    response = chain_with_message_history.invoke(
        {"input": user_message, "context": st.session_state.pdf_context},
        {"configurable": {"session_id": "123"}},
    )
    return response.content


# --- Streamlit UI 구성 ---
st.set_page_config(page_title="📃PDF로 AI와 공부하기", layout="wide")

st.markdown("""
<style>
.header-container {
    text-align: center;
    max-width: 1000px;
    margin: 10px auto;
}
.header-container h1 {
    font-size: 2.5em;
}
.header-container p {
    font-size: 1em;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-container">
    <h1>📖 PDF로 AI와 공부하기 📖</h1>
    <p>💭 학습자료 PDF를 업로드 해보세요. AI가 자료에서 질문을 만들어 줄거예요. 정답을 맞혀 보세요.</p>
</div>
""", unsafe_allow_html=True)

# FAISS DB가 존재하고, 아직 PDF가 처리되지 않았다면(첫 실행), 문제 출제
if st.session_state.vector_store and not st.session_state.pdf_processed:
    try:
        with st.spinner('FAISS DB에서 문제를 생성하고 있습니다...'):
            q_data = question_generator()
            st.session_state.current_question = q_data

        if q_data:
            display_question(q_data)
            st.session_state.pdf_processed = True
        else:
            # question_generator가 None을 반환했을 때만 경고 메시지를 출력
            st.warning("문제가 출제될 문서가 없습니다. PDF를 먼저 업로드해주세요.")
    except Exception as e:
        st.error(f"문제 생성 중 오류가 발생했습니다: {e}")
        st.info("새로운 PDF를 업로드하여 다시 시도하거나, 'faiss_index' 폴더를 삭제하고 다시 실행해주세요.")

# --- PDF 업로드 및 처리 ---
pdf_file = st.file_uploader(
    "Upload a PDF", type=["pdf", "html"], label_visibility="collapsed")
submit_button = st.button("제출", type="primary")

# PDF 제출 버튼 클릭 시 동작
if submit_button and pdf_file is not None:
    # 기존 FAISS DB 초기화 (새로운 PDF 제출 시, 기존 데이터 삭제)
    if os.path.exists(db_path):
        st.warning("기존 FAISS DB가 존재하여, 새로운 PDF로 초기화합니다. 이전 내용은 삭제됩니다.")
        
        # --- 수정된 부분 ---
        # 1. FAISS 폴더를 삭제
        shutil.rmtree(db_path)
        # 2. 캐시된 FAISS 인스턴스도 함께 삭제
        get_vector_store.clear()
        
        st.session_state.vector_store = None
        st.session_state.current_question = None
        st.session_state.messages = []
        st.session_state.wrong_answers = []
    # ------------------
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(pdf_file.read())
        temp_path = temp_pdf.name
    
    st.session_state.pdf_path = temp_path
    st.session_state.pdf_processed = False

    with st.spinner('PDF를 분석하고 있습니다...'):
        load_and_embed_pdf(st.session_state.pdf_path)
        # 벡터 스토어를 다시 로드하여 캐시 업데이트
        st.session_state.vector_store = get_vector_store()
        q_data = question_generator()
        st.session_state.current_question = q_data

    if q_data:
        display_question(q_data)
        st.session_state.pdf_processed = True
    else:
        st.warning("문제가 출제될 문서가 없습니다. PDF 파일의 내용을 확인해주세요.")

# --- 챗봇 인터페이스 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 사용자 입력 처리
if prompt := st.chat_input("AI가 출제한 문제에 답을 하거나 질문을 해보세요."):
    if not st.session_state.pdf_processed:
        st.warning("먼저 PDF 파일을 업로드하고 'PDF 제출' 버튼을 눌러주세요.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("생각 중..."):
                # 사용자 입력이 문제에 대한 답변인지 확인
                answer_check_result = check_answer_and_proceed(prompt)

                if answer_check_result:  # 답변 처리 로직 실행
                    st.write(answer_check_result)

                    # 정답/오답 후 다음 문제 출제
                    new_q_data = question_generator()
                    st.session_state.current_question = new_q_data

                    if new_q_data:
                        # 다음 문제 메시지에 추가
                        display_question(new_q_data)
                        
                        # 다음 문제 즉시 렌더링
                        st.write("---")  # 시각적 구분
                        st.write(new_q_data['question'])
                        st.write("\n".join(new_q_data['options']))
                else:  # 일반 대화 처리
                    full_response = general_response_generator(prompt)
                    st.write(full_response)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": full_response})

# --- PDF 파일 정리 ---
if st.session_state.get("pdf_path") and os.path.exists(st.session_state.pdf_path):
    os.unlink(st.session_state.pdf_path)
