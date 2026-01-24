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

1. Do it! LLM을 활용한 AI 에이전트 개발 입문
2. 러닝 랭체인: 랭체인과 랭그래프로 구현하는 RAG, 에이전트, 인지 아키텍처
3. LangChain Academy: <https://academy.langchain.com/courses/intro-to-langgraph>
4. Gemini API Cookbook: <https://github.com/google-gemini/cookbook>
5. Anthropic 프롬프트 엔지니어링: <https://docs.anthropic.com/ko/docs/build-with-claude/prompt-engineering/overview>
6. 랭체인 허브 프롬프트: <https://smith.langchain.com/hub>
7. Learn Prompting: <https://learnprompting.org/docs/introduction>

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

---

### 10일차: LangGraph로 복잡한 뇌 만들기! (4시간)

#### Section 10-01

- LangChain과 LangGraph의 차이
- 챗봇의 생각 흐름을 그림처럼 그려보는 방법 배우기 (State, Node, Edge)
- 챗봇이 대화 기억하게 하기 (Checkpoint)

#### Section 10-02

- 복잡한 대화 흐름 만들기 (조건부 엣지)
- 질문에 따라 적절한 '생각' 흐름으로 갈아타게 하는 기술 배우기 (라우터)

#### Section 10-03

- 애매할 땐 사람에게 물어보게 하기 (휴먼 인 더 루프)
- 스스로 판단하여 웹 문서의 HTML 요소를 선택하게 하기 (에이전트)

---

### 11일차: 여러 AI 챗봇이 팀워크 하기! 멀티 에이전트 I (4시간)

#### Section 11-01

- 전문가 챗봇과 협력하여 답변하기 (멀티 에이전트)
- 슈퍼바이저 에이전트: AI 팀의 리더가 되어 전체 과정을 관리하는 챗봇 만들기

#### Section 11-02

- 계획 실행 반복: 챗봇이 목표를 세우고, 실행하고, 결과를 확인하며 반복적으로 개선하는 방법 배우기
- 성찰(Reflection): AI 팀이 스스로의 작업을 되돌아보고 개선하는 능력 배우기

---

### 12일차: AI 팀에게 RAG 주기! 멀티 에이전트 II (4시간)

- 스스로 판단하고 작업하는 AI 팀: AI 팀이 목표를 설정하고, 웹 검색과 RAG를 활용하여 정보를 찾고, 스스로 부족한 정보를 보완하며 작업을 완성하는 경험하기

---

### 13일차: 나만의 챗봇 최적화하기! (4시간)

#### Section 13-01

- 임베딩할 때 요약을 생성하여 검색의 정확성과 문맥적 이해를 높이기 (MultiVectorRetriever)

#### Section 13-02

- 누락된 그림으로된 표 전처리하기

#### Section 13-03

- 검색된 문서들 중 관련성이 높은 문서를 선별하여 순위 재조정하기 (re-ranker)

#### Section 13-04

- 부적절한 내용을 생성 방지하기 (guardrail)

---

### 14일차: 챗봇의 성능을 눈으로 확인하고 고치기! (4시간)

- 챗봇이 어떻게 동작하는지 속을 들여다보고, 문제점을 찾아 고치는 방법 배우기 (LangSmith)

---

### 15일차: 최종 프로젝트! 나만의 똑똑한 챗봇 서비스 완성! (4시간)

- RAG기반 법률 상담 멀티 에이전트 챗봇 완성

---

### 16일차: 나만의 챗봇 서비스 배포 및 운영! (4시간)

- 챗봇 서비스를 전 세계에 공개하기! (터널링으로 웹에 배포)
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
