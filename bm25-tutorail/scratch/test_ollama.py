from langchain_ollama import OllamaLLM

model_name = "dengcao/bge-reranker-v2-m3"
llm = OllamaLLM(model=model_name, temperature=0)

query = "배가 너무 고픈데 먹을 것 좀 추천해줘"
doc_content = "점심 메뉴로는 따뜻한 국밥이나 비빔밥을 추천합니다."
prompt = f"질문: {query}\n문서: {doc_content}\n위 문서가 질문에 얼마나 관련이 있는지 0에서 1 사이의 점수(숫자)로만 대답해줘."

print(f"Testing model: {model_name}")
try:
    response = llm.invoke(prompt)
    print(f"Raw Response: '{response}'")
except Exception as e:
    print(f"Error: {e}")
