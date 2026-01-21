# Mission 3: ChatPromptTemplate을 이용한 퀴즈 생성
from langchain_core.prompts import ChatPromptTemplate

def generate_quiz_implement(llm, context):
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
    
    chain = prompt | llm
    response = chain.invoke({"context": context})
    
    # 이 이후에는 스캐폴딩에 제공된 parse_ai_json 함수를 사용하여 
    # response.content에서 JSON을 추출합니다.
    return response.content
