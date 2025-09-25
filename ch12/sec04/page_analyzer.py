import os
import asyncio
from typing import TypedDict, Optional, List
from bs4 import BeautifulSoup
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
from langchain_core.runnables.graph_mermaid import MermaidDrawMethod

# .env 파일에서 환경 변수 로드
load_dotenv()


class PageAnalyzerState(TypedDict):
    """Page Analyzer 에이전트의 상태를 정의합니다.
    - query: 사용자의 원본 자연어 질문
    - content: 슈퍼바이저로부터 전달받은 분석할 HTML 콘텐츠
    - selector: LLM이 생성한 CSS 셀렉터
    - extracted_elements: CSS 셀렉터를 통해 추출된 HTML 요소 목록
    """
    query: str
    content: str
    selector: Optional[str]
    extracted_elements: Optional[List[str]]


class PageAnalyzer:
    """HTML 콘텐츠와 사용자 쿼리를 기반으로 관련 HTML 요소를 식별하는 에이전트.
    CSS 셀렉터를 생성하고 해당 요소를 추출하는 역할을 담당합니다.
    """

    def __init__(self):
        """에이전트 초기화 시 LLM 모델을 한 번만 로드합니다."""
        self.model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
        self.graph = self._build_graph()

        # 그래프 시각화를 비동기로 처리 (이벤트 루프가 있는 경우)
        self._schedule_graph_visualization()

    def _build_graph(self) -> StateGraph:
        """LangGraph를 사용하여 에이전트의 작업 흐름을 정의하고 컴파일합니다."""
        graph_builder = StateGraph(PageAnalyzerState)

        # 노드 추가
        graph_builder.add_node("generate_selector",
                               self._generate_selector_node)
        graph_builder.add_node("extract_html_elements",
                               self._extract_html_elements_node)

        # 진입점 설정
        graph_builder.set_entry_point("generate_selector")

        # 조건부 엣지: 셀렉터 생성 성공 여부에 따라 분기
        graph_builder.add_conditional_edges(
            "generate_selector",
            self._route_after_selector_generation,
            {"success": "extract_html_elements", "failure": END}
        )

        # 일반 엣지: 요소 추출 후 종료
        graph_builder.add_edge("extract_html_elements", END)

        return graph_builder.compile()

    def _schedule_graph_visualization(self):
        """그래프 시각화를 스케줄링합니다. 이벤트 루프가 있으면 비동기로, 없으면 동기로 실행합니다."""
        try:
            # 현재 실행 중인 이벤트 루프가 있는지 확인
            loop = asyncio.get_running_loop()
            # 이벤트 루프가 있으면 비동기 태스크로 실행
            loop.create_task(self._generate_graph_visualization())
        except RuntimeError:
            # 이벤트 루프가 없으면 새로운 이벤트 루프에서 실행
            asyncio.run(self._generate_graph_visualization())

    async def _generate_graph_visualization(self):
        """그래프 시각화를 비동기로 생성합니다."""
        try:
            print("🔄 PageAnalyzer 그래프 시각화 생성 중...")

            # 절대 경로로 파일 저장 위치 설정
            current_dir = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(current_dir, "page_analyzer_graph.png")

            # CPU 집약적인 작업을 별도 스레드에서 실행
            loop = asyncio.get_event_loop()

            def generate_graph():
                try:
                    # PYPPETEER 방법을 먼저 시도
                    return self.graph.get_graph().draw_mermaid_png(
                        draw_method=MermaidDrawMethod.PYPPETEER
                    )
                except Exception as e:
                    print(f"⚠️ PYPPETEER 방법 실패, API 방법으로 시도: {e}")
                    # API 방법으로 대체 시도
                    return self.graph.get_graph().draw_mermaid_png(
                        draw_method=MermaidDrawMethod.API
                    )

            mermaid_png = await loop.run_in_executor(None, generate_graph)

            # 파일 쓰기
            with open(output_path, "wb") as f:
                f.write(mermaid_png)

            print(f"✅ PageAnalyzer 그래프 시각화 저장: {output_path}")
        except Exception as e:
            print(f"⚠️ PageAnalyzer 그래프 시각화 실패: {e}")
            # 최후의 수단으로 동기 방식 시도
            try:
                print("🔄 동기 방식으로 그래프 시각화 재시도...")
                current_dir = os.path.dirname(os.path.abspath(__file__))
                output_path = os.path.join(
                    current_dir, "page_analyzer_graph.png")

                mermaid_png = self.graph.get_graph().draw_mermaid_png()
                with open(output_path, "wb") as f:
                    f.write(mermaid_png)
                print(f"✅ PageAnalyzer 그래프 시각화 저장 (동기): {output_path}")
            except Exception as sync_e:
                print(f"⚠️ 동기 방식도 실패: {sync_e}")

    def _generate_selector_node(self, state: PageAnalyzerState) -> PageAnalyzerState:
        """LLM을 사용하여 HTML 콘텐츠와 쿼리를 기반으로 CSS 셀렉터를 생성합니다."""
        print("🤖 Page Analyzer: CSS 셀렉터 생성 중...")

        prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 사용자의 요청과 제공된 HTML을 분석하여, 웹페이지에서 특정 요소를 찾는 데 가장 적합한 CSS 셀렉터를 반환하는 전문가입니다.

다음 규칙을 반드시 준수해야 합니다:
1. **CSS 셀렉터 문자열만 반환**해야 합니다. 다른 설명은 절대 추가하지 마십시오.
2. 사용자 쿼리에 해당하는 적절한 셀렉터를 찾을 수 없다면, **'None'** 이라는 단 하나의 문자열만 반환해야 합니다.
3. 쿼리가 '검색창'이나 '입력 필드'를 찾는다면, `<input type="text">`, `<input type="search">`, `<textarea>` 등의 요소를 우선적으로 고려하십시오.
4. ID가 있는 요소가 가장 안정적인 선택지이므로, 가능하다면 ID 기반의 셀렉터 (예: `#main-content`)를 사용하십시오.

--- 예시 ---
쿼리: "블로그 제목들을 찾아줘"
HTML: ...<h2 class="f-display-2 relative">블로그 제목</h2>...
반환: "h2.f-display-2.relative"

쿼리: "페이지에 없는 엉뚱한 요소를 찾아줘"
HTML: ...
반환: "None"

---
반드시 규칙에 따라 CSS 셀렉터 문자열 또는 'None'만 반환해야 합니다."""),
            ("user", "분석할 HTML:\n\n{html_content}\n\n사용자 쿼리:\n\n{query}")
        ])

        chain = prompt | self.model

        try:
            result = chain.invoke(
                {"html_content": state["content"], "query": state["query"]})
            selector = result.content.strip()

            if selector.lower() == "none" or not selector:
                print("🤖 Page Analyzer: 적절한 셀렉터를 찾지 못했습니다.")
                state["selector"] = None
            else:
                print(f"🤖 Page Analyzer: 생성된 셀렉터: '{selector}'")
                state["selector"] = selector

        except Exception as e:
            print(f"🔥 Page Analyzer: CSS 셀렉터 생성 중 오류 발생: {e}")
            state["selector"] = None

        return state

    def _extract_html_elements_node(self, state: PageAnalyzerState) -> PageAnalyzerState:
        """생성된 CSS 셀렉터를 사용하여 HTML에서 실제 요소를 추출합니다."""
        print("🤖 Page Analyzer: HTML 요소 추출 중...")

        selector = state.get("selector")
        content = state.get("content")

        if not selector or not content:
            state["extracted_elements"] = None
            return state

        try:
            soup = BeautifulSoup(content, 'html.parser')
            elements = soup.select(selector)

            if not elements:
                print(
                    f"🤖 Page Analyzer: 셀렉터 '{selector}'에 해당하는 요소를 찾을 수 없습니다.")
                state["extracted_elements"] = []
                return state

            # 요소의 외부 HTML(outerHTML)을 리스트로 저장
            extracted_html_list = [element.prettify() for element in elements]
            state["extracted_elements"] = extracted_html_list
            print(f"🤖 Page Analyzer: {len(extracted_html_list)}개의 요소를 추출했습니다.")

        except Exception as e:
            print(f"🔥 Page Analyzer: HTML 요소 추출 중 오류 발생: {e}")
            state["extracted_elements"] = None

        return state

    def _route_after_selector_generation(self, state: PageAnalyzerState) -> str:
        """셀렉터 생성 성공 여부에 따라 다음 단계를 결정하는 라우터입니다."""
        if state.get("selector"):
            return "success"
        else:
            return "failure"

    def run(self, query: str, html_content: str) -> PageAnalyzerState:
        """에이전트 그래프를 실행하고 최종 상태를 반환합니다.

        이 메서드는 슈퍼바이저가 호출하게 될 진입점입니다.

        Args:
            query (str): 사용자의 자연어 질문.
            html_content (str): 분석할 페이지의 HTML 콘텐츠.

        Returns:
            PageAnalyzerState: 작업 완료 후의 최종 상태.
        """
        initial_state = {"query": query, "content": html_content}
        # invoke의 두 번째 인자로 config를 전달하여 재귀 호출 제한 설정 가능
        return self.graph.invoke(initial_state, {"recursion_limit": 5})
