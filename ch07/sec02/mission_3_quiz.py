# Mission 3: ChatPromptTemplate을 이용한 퀴즈 생성
from langchain_core.prompts import ChatPromptTemplate

# 객관식 문제를 JSON 형식으로 출력하도록 유도하는 ChatPromptTemplate 구성법을 담고 있습니다.

def question_generator():
    # (주의: chat, st.session_state.pdf_context 등은 scaffold의 전역/세션 변수 활용 가정)
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
    
    # Scaffold에 제공된 parse_ai_json 함수를 사용하여 JSON 추출 및 결과 반환
    return parse_ai_json(ai_response.content)
