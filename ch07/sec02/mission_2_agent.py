# Mission 2: Tool 정의 및 Agent 초기화
from langchain.agents import create_agent
from langchain.tools import tool

# @tool 정의 법과 create_agent를 통한 지능형 에이전트 구축 방법을 안내합니다.

@tool
def search_pdf_documents(query: str) -> str:
    """업로드된 PDF 문서 내에서 정보를 검색합니다. 
    사실 확인이나 전문적인 내용이 필요할 때 사용하세요.
    """
    if st.session_state.vectorstore is not None:
        # 벡터스토어에서 유사도 검색 수행 (k=3)
        docs = st.session_state.vectorstore.similarity_search(query, k=3)
        return "\n\n".join([doc.page_content for doc in docs])
    return "검색할 문서가 없습니다."

def initialize_agent():
    # (주의: chat, search_pdf_documents 등은 scaffold의 전역 변수 활용 가정)
    system_prompt = """당신은 업로드된 PDF 문서를 바탕으로 학습을 돕는 교육 전문가입니다.
    1. 사용자의 질문에 대해 'search_pdf_documents' 도구를 사용하여 정확한 정보를 찾으세요.
    2. 답변은 반드시 검색된 문서의 내용에만 기반하여 한국어로 작성하세요.
    3. 문서에 관련 내용이 없다면 억지로 꾸며내지 말고 솔직하게 모른다고 답변하세요.
    """
    
    st.session_state.agent = create_agent(
        model=chat,
        tools=[search_pdf_documents],
        system_prompt=system_prompt
    )
