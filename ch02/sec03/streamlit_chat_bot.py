# 설치
# https://streamlit.io/#install
# uv add streamlit

# 챗봇 소스코드
# https://streamlit.io/playground?example=llm_chat&code=H4sIAAAAAAAAA6VVsW4UMRDt7ysmpmBXXPZoaIIiBKJIpEADEkV0ipz1XNaK17bs2RwLoqahoaGl4cv4Aj6B8e7e3m1ySQHb5OwZv3nznsfRtXeBIFJAWRtNICMvZrrfDtIqV29WpGuczSIV66AJM_FuPGTcDUY4O3sTD-DPz18_4PxVo42C1jUB3NpCWUmG9n6ZVUQ-Hi0WypWxGMsW2i0U3qBxfkENuaCliQtj6ri4TEiHpbM3GKIk7aw0hwwVc9AWam0bwjgHqpBX8hqB-Xi3xrBqDFy2IJXS9gp0La9SnpIkV0HW6bcLwDUt4_iGYK3VFVIEcgmso1yIvGu4lD4VzsRbR8hRboYqHUFh7VJboKN9zA2W1EhjWmC2FktClcCkbTtpCnhfuYggAwJ-9GijvkF4nqcaj-DUauKm9ae-MjA8y9DO9AoEk42JvQDrKHXNlCLvMaWLSJLwaAb83d4tNufgGM4_i-AMiiMQklM4bknMQTBTQv7J-2dIj5P5kq1OFIhlS3Z-_yq-LBPF1zp6I9ue34i9Cq7esAVnOzkChsbOVqzvkLaP9EivZ7_WVKWchH4xhLLh73lPfpn3qUOztQzXim_XNmvTzbKT9GVZoidoIobe4iSmZ7q8eXQ81upCmfiQumJPG_9CDHUYQqn-_KYP9nNiz4O6F6wFWpVttU9YU9l7Pl_yoeBG40lRbSeap-tFUlsM9wvXV7pHr74mazStOV4M9i96Z-O_Vd7er53yQ_SCC5VYOaO4vc4CZCZtlo-JPLXmYqx_DEKMoRF4N94_UUzB6RKzMTd955NV-sQJGtONd8ADOHFrKKWF0wE5PVdssJLtCzHfc1bPoWpqaQ_gNPYYabb5IeDn5bRDqtD4DiUpsxfkteviFvltSNm3k5bjaivJI3in68bwzRreaXCrrUWdCbU2Rkdke1R6ldjNraA8hWXV2Otk5l0JC_ZeU7Zj1V0XnhwPCE9AgJgkpv8JRTSIPntaPH2WT4L9_Ei4NNpeJ5XKJkSmw0MUNx1R6zkyObbnrmzv7i1mIH7_-Cbyh-7ZPWfznRHfc_P_c9DveWQnDHjo_wKG2TQxfwcAAA


import streamlit as st

# LLM API
from google import genai

# 환경 변수
import os
from dotenv import load_dotenv
load_dotenv()

print("채팅할 때마다 모든 코드가 다시 실행됨!")

gemini_api_key = os.getenv("GEMINI_API_KEY") # 환경 변수 설정
client = genai.Client(api_key=gemini_api_key) # 모델 객체 생성

st.write("Mark1 🤖")

st.caption(
    "streamlit, gemini-2.5-flash를 사용하였습니다.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "안녕하세요, 저는 Mark1입니다."}]

# 대화 내용을 기억할 수 있도록 처리
if "chat" not in st.session_state:
    st.session_state.chat = client.chats.create(model="gemini-2.5-flash")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    response = st.session_state.chat.send_message(prompt) # 메시지 전송

    # 응답 표시
    with st.chat_message("assistant"): 
        st.markdown(response.text)

    # 대화 내용 저장
    st.session_state.messages.append(
        {"role": "assistant", "content": response.text})

print(st.session_state.messages)  # streamlit이 대화 내용 저장하고 있음

# 실행 방법
# streamlit run streamlit_chat_bot.py