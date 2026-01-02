# * 랭체인 적용
# * 이 예제는 user, assistant 모두 동일 대화 출력함
import streamlit as st

# 마치 카카오톡 메시지 하나와 같다고 생각하면 됨
# 메시지 내용(content): 카톡의 글 내용
# 발신자(role): 이 메시지를 누가 보냈는지? (HUMAN, AI, SYSTEM, TOOL)
from langchain_core.messages import HumanMessage, AIMessage # * 추가

st.title("나만의 LangChain 챗봇 만들기")

if "messages" not in st.session_state:
    st.session_state["messages"] = []


def print_messages():  # 모든 메시지 출력
    for lang_message in st.session_state["messages"]:
        # LangChain 메시지 객체(HumanMessage, AIMessage)의 'type' 속성은 
        # 각각 'human', 'ai'로 반환됩니다. Streamlit의 역할명으로 매핑합니다.
        if lang_message.type == "human":
            st_role = "user"
        elif lang_message.type == "ai":
            st_role = "assistant"
        else:
            # SystemMessage 등 다른 메시지 유형 처리 (이 예시에서는 'ai'로 간주)
            st_role = "assistant" 
            
        st.chat_message(st_role).write(lang_message.content)


def add_message(role, message):  # * 메시지 저장
    # 역할 문자열에 따라 적절한 LangChain 메시지 객체를 생성하여 저장합니다.
    if role == "user":
        msg_obj = HumanMessage(content=message)
    elif role == "assistant":
        msg_obj = AIMessage(content=message)
    else:
        # 예상치 못한 역할은 저장하지 않습니다.
        return
        
    st.session_state["messages"].append(msg_obj)


user_input = st.chat_input("궁금한 내용을 물어보세요!")

print_messages()

print(user_input)

if user_input:
    # 1. Streamlit에 사용자 메시지 출력
    st.chat_message("user").write(user_input)
    # 2. Streamlit에 어시스턴트 메시지 출력 (사용자 입력 복사)
    st.chat_message("assistant").write(user_input)

    # 3. LangChain 세션에 메시지 저장
    add_message("user", user_input)
    add_message("assistant", user_input)

print(st.session_state["messages"])
