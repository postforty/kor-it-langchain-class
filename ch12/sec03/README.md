# Browser Agent with LangGraph & Page Analyzer

이 프로젝트는 Selenium과 LangGraph를 사용하여 웹 브라우저를 자동으로 제어하는 AI 에이전트를 구현합니다. 페이지 분석 서브 에이전트를 통합하여 더 스마트한 요소 찾기와 조작이 가능합니다.

## 파일 구조

- `browser_agent.py`: 브라우저 제어를 위한 메인 AI 에이전트 구현
- `page_analyzer.py`: HTML 페이지 분석 및 CSS 셀렉터 생성 서브 에이전트
- `auto_chrome.py`: 기본 에이전트 실행 스크립트
- `enhanced_auto_chrome.py`: 페이지 분석 기능이 통합된 향상된 실행 스크립트

## 주요 기능

### 1. 기본 브라우저 자동화 도구들

- **navigate_to_url**: 지정된 URL로 브라우저 이동
- **click_element**: CSS 선택자를 사용한 요소 클릭
- **type_text**: 입력 필드에 텍스트 입력
- **get_page_content**: 현재 페이지의 HTML 콘텐츠 추출

### 2. 스마트 브라우저 자동화 도구들 (NEW!)

페이지 분석 에이전트를 활용한 지능형 도구들:

- **analyze_page_elements**: 자연어 쿼리로 페이지 요소 분석 및 CSS 셀렉터 생성
- **smart_click**: 자연어 설명으로 요소를 찾아서 클릭
- **smart_type**: 자연어 설명으로 입력 필드를 찾아서 텍스트 입력

#### 사용 예시

```python
# 기존 방식 (CSS 셀렉터 필요)
click_element("#search-input")

# 새로운 스마트 방식 (자연어로 설명)
smart_click("검색창")
smart_type("검색어 입력 필드", "오늘의 날씨")
```

### 2. AI 에이전트 워크플로우

LangGraph를 사용하여 다음과 같은 노드들로 구성된 워크플로우를 구현:

```
agent → tools → agent → human_intervention → agent/exit
```

#### 노드 설명

- **agent**: LLM이 다음 동작을 결정하는 노드
- **tools**: 선택된 도구를 실행하는 노드
- **human_intervention**: 사용자 개입이 필요한 상황에서 실행되는 노드

### 3. Human-in-the-Loop 기능

에이전트 실행 중 사용자가 개입할 수 있는 옵션들:

- **continue**: 에이전트가 계속 진행
- **new instruction**: 새로운 지침 제공
- **exit**: 에이전트 종료

### 3. 페이지 분석 서브 에이전트

`PageAnalyzer` 클래스는 독립적인 LangGraph 에이전트로 구현되어:

1. **CSS 셀렉터 생성**: 자연어 쿼리를 분석하여 적절한 CSS 셀렉터 생성
2. **HTML 요소 추출**: 생성된 셀렉터로 실제 HTML 요소 추출
3. **지능형 분석**: LLM을 활용한 컨텍스트 기반 요소 식별

## 아키텍처 개선사항

### 역할 분리 (Separation of Concerns)

- **메인 에이전트**: 브라우저 제어 및 워크플로우 관리
- **페이지 분석 서브 에이전트**: HTML 분석 및 셀렉터 생성 전문화

### 성능 개선

1. **정확도 향상**: 전문화된 페이지 분석 에이전트로 더 정확한 요소 식별
2. **사용성 개선**: 자연어 기반 요소 조작으로 CSS 셀렉터 지식 불필요
3. **유지보수성**: 모듈화된 구조로 각 기능의 독립적 개선 가능
4. **확장성**: 새로운 분석 기능을 서브 에이전트에 쉽게 추가 가능

## 기술 스택

- **Selenium**: 웹 브라우저 자동화
- **LangGraph**: AI 에이전트 워크플로우 관리
- **LangChain**: LLM 통합 및 도구 바인딩
- **Google Gemini**: 언어 모델 (gemini-2.5-flash, gemini-2.0-flash)
- **BeautifulSoup**: HTML 파싱

## 설정 및 실행

### 필요한 환경 변수

`.env` 파일에 Google API 키를 설정해야 합니다:

```
GOOGLE_API_KEY=your_google_api_key_here
```

### 실행 방법

#### 기본 에이전트 실행

```python
python sec03/auto_chrome.py
```

#### 향상된 에이전트 실행 (페이지 분석 기능 포함)

```python
python sec03/enhanced_auto_chrome.py
```

## 코드 구조 분석

### AgentState 타입 정의

```python
class AgentState(TypedDict):
    driver: WebDriver          # Selenium WebDriver 인스턴스
    chat_history: List[BaseMessage]  # 대화 기록
    current_url: str          # 현재 브라우저 URL
    scratchpad: List[BaseMessage]    # 에이전트 작업 기록
```

### 도구 함수들

모든 도구 함수는 `@tool` 데코레이터를 사용하여 LangChain 도구로 등록됩니다:

```python
@tool
def navigate_to_url(url: str, **kwargs) -> str:
    """브라우저를 지정된 URL로 이동시킵니다."""
    driver = kwargs['driver']
    driver.get(url)
    return f"브라우저가 {url}로 이동했습니다."
```

### 워크플로우 제어

조건부 에지를 통해 에이전트의 다음 동작을 결정:

```python
def should_continue(state: AgentState):
    last_message = state["scratchpad"][-1]
    if "function_call" in last_message.additional_kwargs:
        return "tools"  # 도구 실행
    else:
        return "human_intervention"  # 사용자 개입 요청
```

## 사용 예시

### 기본 에이전트 (`auto_chrome.py`)

```python
initial_state = AgentState(
    driver=driver,
    chat_history=[HumanMessage(content="네이버에서 '오늘의 날씨'를 검색하고, 검색 결과를 읽어주세요.")],
    current_url=driver.current_url,
    scratchpad=[],
    user_input="continue"
)
```

### 향상된 에이전트 (`enhanced_auto_chrome.py`)

```python
initial_state = AgentState(
    driver=driver,
    chat_history=[HumanMessage(content="""
네이버에서 다음 작업을 수행해주세요:
1. 검색창을 찾아서 '오늘의 날씨'를 검색하세요
2. 검색 결과에서 날씨 정보를 찾아서 읽어주세요

스마트 도구들(smart_click, smart_type, analyze_page_elements)을 활용해서
자연어로 요소를 찾고 조작해보세요.
    """)],
    current_url=driver.current_url,
    scratchpad=[],
    user_input="continue"
)
```

## 주요 특징

### 기본 기능

1. **유연한 브라우저 제어**: CSS 선택자를 통한 정확한 요소 제어
2. **AI 기반 의사결정**: LLM이 상황에 맞는 적절한 도구 선택
3. **사용자 개입 지원**: 필요시 사용자가 직접 개입 가능
4. **에러 처리**: 도구 실행 실패시 적절한 에러 메시지 반환
5. **상태 관리**: 브라우저 상태와 대화 기록을 체계적으로 관리

### 향상된 기능 (페이지 분석 통합)

6. **자연어 기반 요소 조작**: CSS 셀렉터 지식 없이도 요소 조작 가능
7. **지능형 페이지 분석**: 컨텍스트를 이해하는 요소 식별
8. **모듈화된 아키텍처**: 서브 에이전트를 통한 역할 분리
9. **향상된 정확도**: 전문화된 분석 에이전트로 더 정확한 요소 찾기

## 워크플로우 비교

### 기존 방식

```
사용자 요청 → LLM 분석 → CSS 셀렉터 직접 사용 → 브라우저 조작
```

### 개선된 방식

```
사용자 요청 → 메인 에이전트 → 페이지 분석 서브 에이전트 → CSS 셀렉터 생성 → 브라우저 조작
```

## 확장 가능성

- **서브 에이전트 추가**: 스크린샷 분석, 폼 자동 완성 등 전문 에이전트
- **다중 브라우저 지원**: Firefox, Safari 등 다른 브라우저 지원
- **복잡한 워크플로우**: 다단계 작업 자동화
- **시각적 요소 인식**: 이미지 기반 요소 식별
- **성능 최적화**: 캐싱, 병렬 처리 등
