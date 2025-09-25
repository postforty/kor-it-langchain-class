# Implementation Plan

- [x] 1. 기본 데이터 구조 및 상태 정의

  - InstructionAnalyzerState TypedDict 클래스 생성
  - ExecutionStep 데이터클래스 구현
  - PageContext 데이터클래스 구현
  - 기본 상수 및 열거형 정의
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. 지시사항 분석 에이전트 기본 구조 구현

  - [x] 2.1 InstructionAnalyzer 클래스 기본 골격 생성

    - 클래스 초기화 메서드 구현
    - LLM 모델 설정 및 PageAnalyzer 연동
    - 기본 설정 및 상수 정의
    - _Requirements: 1.1, 3.1_

  - [x] 2.2 LangGraph 워크플로우 기본 구조 구현
    - StateGraph 기반 그래프 빌더 생성
    - 기본 노드들 정의 (analyze_instruction, analyze_page, validate_requirements)
    - 노드 간 연결 및 조건부 라우팅 로직 구현
    - _Requirements: 1.2, 1.3_

- [x] 3. 지시사항 해석 노드 구현

  - [x] 3.1 자연어 지시사항 파싱 로직 구현

    - 사용자 지시사항에서 의도 추출
    - 액션 타입 식별 (navigate, click, type, search 등)
    - 대상 요소 설명 추출
    - 매개변수 및 조건 파싱
    - _Requirements: 1.1, 1.2_

  - [x] 3.2 지시사항 검증 및 명확화 로직 구현
    - 모호한 지시사항 감지
    - 실행 불가능한 요청 식별
    - 명확화 질문 생성 로직
    - _Requirements: 1.4, 2.1_

- [x] 4. 페이지 분석 연동 노드 구현

  - [x] 4.1 현재 페이지 컨텍스트 분석 구현

    - HTML 구조 분석
    - 주요 UI 요소 식별 (폼, 버튼, 링크, 입력 필드)
    - 네비게이션 구조 파악
    - 콘텐츠 영역 식별
    - _Requirements: 3.1, 3.2_

  - [x] 4.2 PageAnalyzer와의 연동 로직 구현
    - 지시사항 기반 요소 검색 쿼리 생성
    - PageAnalyzer 호출 및 결과 처리
    - 여러 후보 요소 처리 로직
    - 요소 식별 실패시 대안 생성
    - _Requirements: 3.1, 3.3_

- [ ] 5. Human-in-the-Loop 노드 완성

  - [x] 5.1 정보 부족 감지 로직 구현

    - 필수 정보 누락 검사
    - 모호한 요소 식별 감지
    - 사용자 확인이 필요한 상황 판단
    - _Requirements: 2.1, 2.2_

  - [ ] 5.2 사용자 질문 생성 및 응답 처리 완성
    - 실제 사용자 입력 인터페이스 구현
    - 응답 검증 및 상태 업데이트 로직
    - 타임아웃 처리 메커니즘
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [ ] 6. 실행 계획 생성 노드 완성

  - [x] 6.1 단계별 실행 계획 생성 로직 구현

    - 지시사항을 실행 가능한 단계로 분해
    - 각 단계별 액션 타입 및 매개변수 설정
    - 단계 간 의존성 및 순서 관리
    - 예상 결과 및 검증 기준 설정
    - _Requirements: 1.2, 1.3_

  - [ ] 6.2 실행 계획 최적화 및 검증 완성
    - CSS 셀렉터 생성 및 검증 로직
    - 실행 가능성 검증 강화
    - 대안 액션 생성 로직 완성
    - _Requirements: 1.3, 3.4_

- [x] 7. 계획 검토 및 승인 노드 구현

  - [x] 7.1 사용자 검토 인터페이스 구현

    - 생성된 계획 표시 로직
    - 단계별 설명 및 예상 결과 표시
    - 승인/수정/재생성 옵션 제공
    - _Requirements: 4.1, 4.2_

  - [x] 7.2 계획 수정 및 재생성 로직 구현
    - 특정 단계 수정 기능
    - 전체 계획 재생성 기능
    - 수정 사항 반영 로직
    - _Requirements: 4.3, 4.4_

- [ ] 8. 오류 처리 및 복구 메커니즘 완성

  - [x] 8.1 포괄적인 오류 처리 로직 구현

    - 페이지 분석 실패 처리
    - 지시사항 해석 실패 처리
    - 실행 계획 생성 실패 처리
    - 네트워크 및 시스템 오류 처리
    - _Requirements: 5.1, 5.2, 5.3_

  - [ ] 8.2 오류 복구 및 대안 제시 완성
    - 자동 복구 메커니즘 강화
    - 대안 실행 방법 제시 로직 완성
    - 사용자 알림 및 선택권 제공 개선
    - _Requirements: 5.2, 5.3, 5.4_

- [x] 9. 브라우저 에이전트 통합

  - [x] 9.1 새로운 도구 함수 구현

    - analyze_and_execute_instruction 도구 함수 생성
    - get_execution_plan, execute_plan_step, execute_full_plan 도구 추가
    - 기존 브라우저 에이전트와의 인터페이스 정의
    - 실행 결과 피드백 처리
    - _Requirements: 1.4, 4.4_

  - [x] 9.2 브라우저 에이전트 워크플로우 수정

    - 지시사항 분석 에이전트 호출 로직 추가
    - 생성된 실행 계획 처리 로직
    - 기존 도구들과의 연동 개선
    - 컨텍스트 정보 제공 로직
    - _Requirements: 1.3, 4.4_

- [ ] 10. 워크플로우 노드 구현 완성

  - [ ] 10.1 누락된 워크플로우 노드 메서드 구현

    - \_analyze_instruction_node 메서드 완성
    - \_analyze_page_node 메서드 완성
    - \_validate_requirements_node 메서드 완성
    - \_human_interaction_node 메서드 완성
    - \_generate_plan_node 메서드 완성
    - \_review_plan_node 메서드 완성
    - _Requirements: 1.1, 1.2, 1.3, 2.1, 3.1, 4.1_

  - [ ] 10.2 라우팅 로직 메서드 구현
    - \_route_after_instruction_analysis 메서드 구현
    - \_route_after_page_analysis 메서드 구현
    - \_route_after_validation 메서드 구현
    - \_route_after_human_interaction 메서드 구현
    - \_route_after_plan_generation 메서드 구현
    - \_route_after_plan_review 메서드 구현
    - _Requirements: 1.2, 1.3_

- [ ] 11. 테스트 및 검증

  - [x] 11.1 기본 테스트 스크립트 작성

    - 기본 기능 테스트
    - Human-in-the-Loop 테스트
    - 실행 계획 생성 테스트
    - 오류 처리 테스트
    - _Requirements: 5.1, 5.2_

  - [ ] 11.2 통합 테스트 완성
    - End-to-End 워크플로우 테스트 완성
    - 다양한 웹사이트 시나리오 테스트
    - 브라우저 에이전트와의 통합 테스트
    - _Requirements: 1.1, 2.1, 3.1_

- [ ] 12. 문서화 및 예시

  - [ ] 12.1 실행 예시 스크립트 완성

    - 기본 사용법 예시 완성
    - 복잡한 시나리오 예시
    - 오류 상황 처리 예시
    - _Requirements: 4.1, 4.2_

  - [ ] 12.2 README 및 문서 업데이트
    - 새로운 기능 설명 추가
    - 사용법 가이드 작성
    - 아키텍처 다이어그램 업데이트
    - _Requirements: 1.1, 2.1, 3.1_
