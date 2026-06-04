# Python과 LangChain을 활용한 LLM 기반의 AI 서비스 개발 과정

## 1. 과정 개요

- 이 교육 과정은 갓 태어난 아기 챗봇이 똑똑한 전문가 챗봇으로 성장해가는 여정을 함께하는 동안 학습자도 능동적인 AI 애플리케이션 개발자로 발돋움하는 것을 목표로 한다.

### 학습 목표

- 랭체인, 랭그래프, RAG, 오픈 소스 LLM에 대한 이해 및 활용 능력을 향상한다.
- LLM 기반 서비스 및 AI 에이전트 개발 실무 능력을 배양한다.
- 다양한 실습을 통한 문제 해결 능력 및 창의적 사고력을 강화한다.

### 수업 일정

- 주말 / 일 4시간 16일 / 총 64시간

### 개발 환경

- **개발 OS**: Windows 10 이상
- **개발 도구(IDE)**: Visual Studio Code, Jupyter Notebook, Google Colab
- **기타(프레임워크)**: LangChain, LangGraph, LangSmith, Ollama, Streamlit, Gradio, Github, Docker

### 참고

1. 메이오 오신, 누노 캄포스, *러닝 랭체인: 랭체인과 랭그래프로 구현하는 RAG, 에이전트, 인지 아키텍처*, 강민혁 역. 한빛미디어, 2025.
2. 수하스 파이, *실무로 통하는 LLM 애플리케이션 설계*, 박조은 역. 한빛미디어, 2025.
3. LangChain Academy: <https://academy.langchain.com/courses/intro-to-langgraph>
4. Gemini API Cookbook: <https://github.com/google-gemini/cookbook>
5. 랭체인 허브 프롬프트: <https://smith.langchain.com/hub>
6. Prompt Engineering Guide: <https://www.promptingguide.ai/>
7. Learn Prompting: <https://learnprompting.org/docs/introduction>
8. Context Engineering: <https://www.philschmid.de/context-engineering>
9. OpenAI Evals(LLM 앱/시스템 평가 프레임워크): <https://github.com/openai/evals>

---

## 2. 커리큘럼

### 1일차: 첫 만남, LLM 챗봇과 인사하기! (4시간)

- 오리엔테이션, 강사 및 강의 소개

#### Section 01-01

- LLM 챗봇, 넌 누구니?
- LLM(거대 언어 모델)이란 무엇이고, 어떤 일을 할 수 있는지 알아보기
- 챗GPT 같은 생성형 AI 서비스가 어떻게 작동하는지 이해하기

#### Section 01-02

- 나만의 챗봇을 만들 개발 환경(Visual Studio Code, Python, Github) 세팅하기
- LangChain을 위한 Python 기본 문법 복습하기

---

### 2일차: 첫 챗봇 만들기! AI와 대화하는 법 배우기! (4시간)

#### Section 02-01

- LLM API 키를 발급받아 인공지능과 소통하는 문 열기

#### Section 02-02

- 프롬프트 엔지니어링: AI에게 질문하고 지시하는 가장 효과적인 방법 배우기("야, 너는 이제부터 친절한 로봇 비서야!")

#### Section 02-03

- 간단한 코드로 첫 챗봇을 만들어보고, 인공지능과 대화해보기

#### Section 02-04

- LLM 모델의 잠재 능력 체험해 보기
  - AI 도슨트: 그림 속 숨겨진 이야기를 들려주는 인공지능 해설사 만들기
  - AI 서기: 음성을 텍스트로 요약하기
  - AI 연구원: PDF 문서 요약 및 논문 정리 챗봇 만들기

---

### 3일차: 나만의 챗봇 얼굴 만들기! LangChain과 친해지기! (4시간)

#### Section 03-01

- LangChain이 무엇이고 왜 필요한지 이해하기("AI 서비스 개발의 만능 도구!")

#### Section 03-02

- Streamlit을 이용해 챗봇 얼굴 만들기

---

### 4일차: 챗봇이 대화를 기억하게 하기! (4시간)

#### Section 04-01

- 에이전트와 도구 이해하기 (Agents & Tools)
- 단기 메모리를 이용해 체계적으로 세션별 대화 기록 관리하기 (Short Term Memory)

#### Section 04-02

- 챗봇과 끝말 잊기 게임하기 (Gradio)

#### Section 04-03

- 구조화된 출력 얻기 (Structured Outputs)
- 챗봇과 끝말 잊기 게임 업그레이드!

---

### 5일차: 미들웨어로 기능 추가하기! (4시간)

#### Section 05-01

- 사전 구축된 미들웨어(Built-in Middleware) 이해하기
- 가짜 도구(Mock)를 사용하여 에이전트 프로토타이핑 및 테스트 (LLM Tool Emulator)
- 복잡한 작업을 체계적으로 관리하는 할 일 목록(Todo List) 생성 및 관리 (TodoListMiddleware)
- 도구 실행 전 사람의 승인을 받는 워크플로우 (Human-in-the-loop)
- 주민등록번호 등 민감한 개인정보 자동 감지 및 마스킹 처리 (PIIMiddleware)

#### Section 05-02

- 에이전트가 이메일 전송 전 사용자에게 허락 받도록 하기 (HITL)

---

### 6일차: 챗봇에게 지식 주기! RAG (4시간)

#### Section 06-01

- 챗봇이 정보를 찾아보고 답변하는 과정 배우기 (Retrieval Augmented Generation, RAG)
- 챗봇에게 책 읽히기! (Document Loader)
- 긴 문서를 챗봇이 읽기 좋은 작은 조각으로 나누는 방법 배우기 (Text Splitter)
- 텍스트를 숫자로 변환하여 인공지능이 이해하는 언어로 바꾸는 마법 배우기 (Embedding)
- 챗봇이 정보를 저장하고 빠르게 찾아볼 수 있는 특별한 도서관 만들기 (Faiss Vector Store)

#### Section 06-02

- LCEL 활용 문서 로드 및 저장 RAG 파이프라인 구축하기
- 에이전트가 스스로 판단하여 정보를 검색하고 답변하는 에이전틱 RAG(Agentic RAG) 구현하기

---

### 7일차: 챗봇이 지식으로 답변하게 하기! (4시간)

#### Section 07-01

- 챗봇의 독서법: PDF 문서를 가장 정확하게 읽어오는 다양한 도구(Document Loader) 비교하기
- AI 출제위원: 문서 내용을 바탕으로 4지선다형 퀴즈와 주관식 문제를 스스로 만드는 인공지능 만들기

#### Section 07-02

- 퀴즈 선생님 챗봇: Streamlit을 활용해 사용자와 실시간으로 퀴즈를 풀고 해설해주는 대화형 학습 서비스 구축하기
- 검색의 달인, FAISS: 방대한 지식 속에서 필요한 정보만 쏙쏙 찾아 답변하는 실전 RAG 챗봇 완성하기

---

### 8일차: 로컬 LLM의 세계, Ollama! (4시간)

#### Section 08-01

- Ollama: 인터넷 연결 없이 내 컴퓨터에서 직접 LLM을 돌려보기(비용 절감, 개인 정보 보호)
- 로컬 LLM 모델을 활용해 나만의 챗봇 만들어보기

#### Section 08-02

- RAG 기반 추억을 공유하는 펫봇 만들기 (PGVector, Docker)

---

### 9일차: 챗봇에게 팔다리 달기! (4시간)

#### Section 09-01

- 챗봇을 위한 시계와 주가 검색 능력 만들기
- 툴 콜링(Tool Calling)으로 챗봇이 외부 도구를 사용하는 방법 배우기

#### Section 09-02

- 챗봇에게 여러 가지 편리한 도구들 연결하기
- 표준화된 도구 사용하게 하기 (MCP)


#### Section 09-03

- 챗봇에게 여러 가지 편리한 도구들 연결하기

---

### 10일차: 나만의 미들웨어와 가드레일 만들기! (4시간)

#### Section 10-01

- 데이터를 깔끔하게 포장하는 기술 `Dataclass`와 컨텍스트(Context)
- 챗봇이 대답하기 전후에 몰래 개입하기 (`Node Style` 미들웨어)
- 챗봇의 실행 흐름을 완전히 감싸서 조종하기 (`Wrap Style` 미들웨어)

#### Section 10-02

- 챗봇을 바른 길로 인도하는 가드레일(Guardrails) 만들기
- 입력과 출력을 검사하여 나쁜 말을 걸러내고, 정답 유출 막기 (`before_agent`, `after_agent`)
- 학생 안전 지킴이: 개인정보 가리기와 위험 감지 시 선생님 부르기

---

### 11일차: 메모리 이식과 똑똑한 PDF AI 튜터 만들기! (4시간)

#### Section 11-01

- 챗봇에게 '장기 기억' 뇌 이식하기 (Long Term Memory)
- `Store`를 이용해 사용자의 특징과 취향을 스스로 기록하고 영원히 기억하기
- 대화할 때 자연스럽게 옛날 기억을 찾아보는 하이브리드 메모리 검색 배우기

#### Section 11-02

- 외부 프롬프트 파일(YAML)을 활용하여 깔끔하게 프롬프트 관리하기
- 코드 내 하드코딩 없이 유연하게 시스템 프롬프트 로드 및 적용하기

#### Section 11-03

- 캡스톤 프로젝트: Streamlit 기반 종합 PDF AI 튜터 챗봇 만들기
- RAG, 단기/장기 기억, 다중 가드레일 미들웨어를 하나의 에이전트로 결합하기
- FAISS를 활용한 문서 기반 퀴즈 출제 및 맞춤형 학습 도우미 완성

---

### 12일차: LangGraph로 복잡한 뇌 만들기! (4시간)

#### Section 12-01

- LangGraph 핵심 개념 배우기: 상태(State), 노드(Node), 엣지(Edge)
- 조건에 따라 다른 길로 보내기 (조건부 엣지, 라우터)
- 여러 작업을 동시에 처리하기 (병렬 실행)

#### Section 12-02

- LangChain과 LangGraph의 차이 이해하기
- LLM 모델을 연동한 조건부 라우팅 구현하기 (감정 분석 챗봇)

#### Section 12-03

- LangGraph로 대화 기억하는 챗봇 만들기 (MessagesState, Checkpoint)
- 터미널에서 동작하는 대화형 챗봇 완성하기

---

### 13일차: LangGraph 심화! 도구, 기억, 그리고 사람의 개입! (4시간)

#### Section 13-01

- LangGraph에서 도구(Tool) 사용하기: 사칙 연산 도구를 만들고 LLM에 바인딩하기
- 도구 호출 여부에 따라 반복하는 조건부 엣지 구현하기

#### Section 13-02

- 챗봇이 대화를 기억하게 하기 (InMemorySaver Checkpoint)
- 체크포인트 히스토리 조회 및 상태 추적하기
- SQLite로 대화 기록 영구 저장하기

#### Section 13-03

- 애매할 땐 사람에게 물어보게 하기 (Human-in-the-Loop)
- 도구 실행 전 사람의 승인을 받는 워크플로우 구현하기

#### Section 13-04

- 과거로 돌아가기! 타임 트래블(Time Travel)로 체크포인트 탐색 및 상태 되돌리기
- 번역 워크플로우에서 타임 트래블 실습하기

---

### 14일차: 더 똑똑하게 대답하는 RAG 만들기! (Advanced RAG) (4시간)

#### Section 14-01

- LangGraph로 RAG 구현하기
- 질문을 더 명확하게 다시 쓰는 챗봇 만들기 (Query Rewrite)

#### Section 14-02

- 스스로 질문하고 검증하기: 생성된 답변을 여러 번 평가하는 챗봇 (Self-RAG)

#### Section 14-03

- 검색 결과가 부족하면 웹 검색으로 보완하기 (Corrective RAG, CRAG)

---

### 15일차: 여러 AI 챗봇이 팀워크 하기! 멀티 에이전트 (4시간)

#### Section 15-01

- 에이전트(Agent)의 기본과 하위 그래프(Subgraph) 구성
- 여러 에이전트가 협력해서 문제 해결하기

#### Section 15-02

- 챗봇이 먼저 목표를 세우고 실행하며 결과를 개선하는 방법 (Plan and Execute)

#### Section 15-03

- AI 팀의 리더 만들기: 전체 과정을 관리하는 슈퍼바이저(Supervisor) 에이전트
- 작업 할당과 인수인계(Handoff/Delegation) 워크플로우

#### Section 15-04

- 자연어로 데이터베이스 조회하기 (SQL 어시스턴트)

---

### 16일차: 최종 프로젝트! 나만의 똑똑한 챗봇 서비스 완성! (4시간)

#### Section 16-01

- RAG 기반 멀티 에이전트 챗봇 완성하기

#### Section 16-02

- Streamlit을 활용해 대화형 챗봇 웹 UI 개발하기
- 챗봇 서비스를 전 세계에 공개하기! (Ngrok 터널링으로 웹 배포)
- 내 스마트폰에서 챗봇 사용해 보기!

---

## 3. 빠른 시작

### UV 실습 환경 구성

- **요구 사항**

  - Windows 10 이상, Git, PowerShell 환경이 필요하다.
  - Python 3.13 이상이 권장된다. Python 설치/버전 관리는 uv로 진행하면 된다(자세한 사용법은 [`ch01\\sec02\\uv\\cheat_sheet.md`](ch01/sec02/uv/cheat_sheet.md) 참고).

- **uv 설치**
  - PowerShell에서 다음 명령으로 설치하면 된다.

```powershell
powershell -ExecutionPolicy Bypass -NoProfile -Command "irm https://astral.sh/uv/install.ps1 | iex"
```

- **Python 설치/버전 관리(uv)**
  - 각 챕터의 `pyproject.toml`에 `requires-python = ">=3.13"`가 설정되어 있으므로 `uv sync` 시 자동으로 적합한 버전을 사용한다.
  - 수동 설치 또는 확인 예시:

```powershell
uv python install 3.13
uv run python --version
```

- **레포 클론 및 .env 준비**
  - 저장소를 클론하고 루트 위치에 `.env` 파일을 만든다.
  - `.env`는 `.gitignore`에 추가하여 외부에 노출되지 않도록 한다.

```env
GEMINI_API_KEY=여기에_본인_API_키
```

- **설치/실행 기본 원칙**
  - 각 챕터 디렉터리로 이동한 뒤 `uv sync`로 의존성을 설치하고, `uv run ...`으로 실행하면 된다.

---

## 4. 자주 묻는 질문(FAQ)

- **키 관련 오류가 발생한다.**

  - `.env`에 `GEMINI_API_KEY`가 설정되어 있는지 확인하면 된다.

- **패키지 설치 오류가 발생한다.**

  - 관리자 권한 PowerShell로 `uv sync`를 다시 실행하거나, 네트워크 프록시/방화벽을 점검하면 된다.

- **import 코드에 노란줄이 생긴다.**
  - 모듈을 설치했음에도 불구하고 노란줄이 생기는 경우에는 단축키 `ctrl + shift + p` 입력 후, `Python: Restart Language Server`를 검색 후 실행하면 된다.
