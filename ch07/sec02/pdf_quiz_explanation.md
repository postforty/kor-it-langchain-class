# PDF Quiz 챗봇 (`pdf_quiz.py`) 코드 분석 및 FAISS 활용 설명

본 문서는 `pdf_quiz.py` 파일에서 구현된 PDF 기반 퀴즈 챗봇의 **FAISS 벡터 데이터베이스** 활용 방식과 주요 기능별 데이터 처리 흐름을 설명합니다.

## 1. 개요

이 애플리케이션은 사용자가 PDF를 업로드하면 내용을 학습하여 **4지선다 퀴즈를 출제**하거나, 사용자의 **일반적인 질문에 답변**하는 기능을 제공합니다. 핵심 기술로는 구글의 Gemini 모델과 FAISS(Facebook AI Similarity Search) 벡터 저장소가 사용됩니다.

## 2. FAISS 벡터 데이터베이스의 역할

이 코드에서 FAISS는 **RAG (Retrieval-Augmented Generation, 검색 증강 생성)** 구현을 위한 핵심 저장소 역할을 합니다.

- **기능**: PDF 문서를 작은 청크(Chunk)로 나누고 임베딩(벡터화)하여 저장합니다.
- **목적**: 사용자의 질문과 의미적으로 유사한 텍스트 조각을 빠르게 검색하여 에이전트에게 제공함으로써, 할루시네이션을 줄이고 문서 기반의 정확한 답변을 유도합니다.

## 3. 기능별 구현 방식의 차이

가장 중요한 점은 **문제 출제**와 **일반 질의응답** 기능이 PDF 데이터를 참조하는 방식이 서로 다르다는 것입니다.

### A. 4지선다 문제 출제 (`question_generator`)
**→ FAISS를 사용하지 않습니다.**

- **데이터 소스**: `st.session_state.pdf_context` (PDF 전체 텍스트)
- **작동 방식**:
  - PDF 로드 시 추출해둔 **전체 텍스트 내용**을 프롬프트 입력값(`context`)으로 직접 전달합니다.
  - 검색 과정 없이 전체 내용을 LLM에게 제공하여, 문서의 전반적인 맥락을 파악하고 문제를 출제하도록 합니다.
- **코드 확인**:
  ```python
  # question_generator 함수 내
  ai_response = chain.invoke({"context": st.session_state.pdf_context})
  ```

### B. 일반 질의응답 (`general_response` / `agent`)
**→ FAISS를 적극적으로 사용합니다.**

- **데이터 소스**: `st.session_state.vectorstore` (FAISS 인덱스)
- **작동 방식**:
  - `create_agent`로 생성된 에이전트가 답변을 위해 `search_pdf_documents`라는 도구(Tool)를 호출합니다.
  - 이 도구는 FAISS에서 질문과 유사도가 높은 **상위 3개의 문서 조각(Chunk)** 만을 검색(`similarity_search`)하여 가져옵니다.
  - 에이전트는 검색된 일부 내용만을 근거로 사용자 질문에 답변합니다.
- **코드 확인**:
  ```python
  # search_pdf_documents 함수 내
  docs = st.session_state.vectorstore.similarity_search(query, k=3)
  ```

## 4. 요약

| 기능 | 사용 데이터 | FAISS 사용 여부 | 이유 |
| :--- | :--- | :---: | :--- |
| **퀴즈 생성** | PDF 전체 텍스트 | ❌ | 문맥의 흐름을 파악하여 문제를 출제하기 위함 |
| **일반 답변** | 벡터 검색된 일부 청크 | ⭕ | 특정 사실이나 정보를 정확하게 찾아 답변하기 위함 (RAG) |
