"""
지시사항 분석 에이전트 테스트 스크립트
"""

from instruction_analyzer import InstructionAnalyzer


def test_instruction_analyzer():
    """기본 테스트"""
    print("=== 지시사항 분석 에이전트 테스트 ===")

    # 에이전트 생성
    analyzer = InstructionAnalyzer()

    # 테스트 데이터
    test_instruction = "네이버에서 오늘의 날씨를 검색해주세요"
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NAVER</title>
    </head>
    <body>
        <div class="search_area">
            <input type="search" id="query" name="query" placeholder="검색어를 입력해주세요" />
            <button type="submit" class="btn_search">검색</button>
        </div>
        <nav class="gnb">
            <ul>
                <li><a href="/mail">메일</a></li>
                <li><a href="/news">뉴스</a></li>
            </ul>
        </nav>
        <main class="content">
            <h1>네이버 메인</h1>
            <p>검색 포털 사이트</p>
        </main>
    </body>
    </html>
    """
    test_url = "https://www.naver.com"

    # 입력 검증
    validation_errors = analyzer.validate_input(
        test_instruction, test_html, test_url)
    print(f"입력 검증: {validation_errors}")

    if not validation_errors:
        # 분석 실행
        result = analyzer.analyze_instruction(
            test_instruction, test_html, test_url)

        print(f"\n=== 분석 결과 ===")
        print(f"처리 단계: {result['processing_stage']}")
        print(f"세션 ID: {result['session_id']}")

        if result.get('parsed_intent'):
            intent = result['parsed_intent']
            print(f"\n=== 파싱된 의도 ===")
            print(f"주요 목표: {intent.primary_goal}")
            print(f"대상 객체: {intent.target_objects}")
            print(f"신뢰도: {intent.confidence_score:.2f}")
            print(f"성공 기준: {intent.success_criteria}")

        if result.get('page_analysis'):
            page = result['page_analysis']
            print(f"\n=== 페이지 분석 ===")
            print(f"페이지 타입: {page.page_type}")
            print(f"제목: {page.title}")
            print(f"주요 요소: {len(page.main_elements)}개")
            print(f"폼: {len(page.forms)}개")
            print(f"네비게이션: {len(page.navigation)}개")

        if result.get('identified_elements'):
            elements = result['identified_elements']
            print(f"\n=== 식별된 요소들 ({len(elements)}개) ===")
            for i, elem in enumerate(elements[:5]):  # 처음 5개만 표시
                print(f"{i+1}. {elem.element_type}: {elem.description}")
                print(f"   셀렉터: {elem.selector}")
                print(f"   상호작용 가능: {elem.is_interactive}")

        if result.get('execution_steps'):
            steps = result['execution_steps']
            print(f"\n=== 실행 계획 ({len(steps)}개 단계) ===")
            for step in steps:
                print(
                    f"{step.step_id}. {step.action_type.value}: {step.target_description}")
                if step.parameters:
                    print(f"   매개변수: {step.parameters}")
                print(f"   예상 결과: {step.expected_outcome}")

        if result.get('validation_errors'):
            errors = result['validation_errors']
            print(f"\n=== 검증 오류 ({len(errors)}개) ===")
            for error in errors:
                print(f"- {error.error_type}: {error.message}")
                if error.suggested_fix:
                    print(f"  제안: {error.suggested_fix}")

        if result.get('user_questions'):
            questions = result['user_questions']
            print(f"\n=== 사용자 질문 ({len(questions)}개) ===")
            for q in questions:
                print(f"- {q.question_text}")
                if q.options:
                    print(f"  선택지: {q.options}")

    print("\n=== 테스트 완료 ===")


def test_human_interaction():
    """Human-in-the-Loop 기능 테스트"""
    print("\n=== Human-in-the-Loop 테스트 ===")

    analyzer = InstructionAnalyzer()

    # 모호한 지시사항으로 테스트
    ambiguous_instruction = "검색해줘"  # 검색어가 명시되지 않음
    test_html = """
    <html>
    <body>
        <input type="search" id="search1" placeholder="검색어 입력" />
        <input type="search" id="search2" placeholder="상품 검색" />
        <button>검색</button>
    </body>
    </html>
    """

    result = analyzer.analyze_instruction(
        ambiguous_instruction, test_html, "https://example.com")

    print(f"처리 단계: {result['processing_stage']}")
    print(f"부족한 정보: {result.get('missing_info', [])}")
    print(f"사용자 질문: {len(result.get('user_questions', []))}개")
    print(f"사용자 응답: {result.get('user_responses', {})}")


if __name__ == "__main__":
    test_instruction_analyzer()
    test_human_interaction()
    test_execution_plan_generation()
    test_error_handling()
    test_recovery_mechanisms()


def test_execution_plan_generation():
    """실행 계획 생성 테스트"""
    print("\n=== 실행 계획 생성 테스트 ===")

    analyzer = InstructionAnalyzer()

    # 명확한 검색 지시사항
    clear_instruction = "네이버에서 '파이썬 강의'를 검색해주세요"
    naver_html = """
    <html>
    <head><title>NAVER</title></head>
    <body>
        <div class="search_area">
            <input type="search" id="query" name="query" placeholder="검색어를 입력해주세요" />
            <button type="submit" class="btn_search">검색</button>
        </div>
        <nav>
            <a href="/mail">메일</a>
            <a href="/news">뉴스</a>
        </nav>
    </body>
    </html>
    """

    result = analyzer.analyze_instruction(
        clear_instruction, naver_html, "https://www.naver.com")

    print(f"처리 단계: {result['processing_stage']}")

    if result.get('execution_steps'):
        steps = result['execution_steps']
        print(f"\n=== 생성된 실행 계획 ({len(steps)}단계) ===")
        for step in steps:
            print(
                f"{step.step_id}. {step.action_type.value}: {step.target_description}")
            if step.parameters:
                print(f"   매개변수: {step.parameters}")
            print(f"   예상 결과: {step.expected_outcome}")
            if step.dependencies:
                print(f"   의존성: {step.dependencies}")
            if step.fallback_actions:
                print(f"   대안: {step.fallback_actions}")
            print()

    if result.get('validation_errors'):
        print(f"=== 검증 오류 ({len(result['validation_errors'])}개) ===")
        for error in result['validation_errors']:
            print(f"- {error.error_type}: {error.message}")

    if result.get('review_info'):
        review = result['review_info']
        print(f"\n=== 검토 정보 ===")
        print(
            f"위험도: {review.get('risk_assessment', {}).get('overall_risk', 'unknown')}")
        print(
            f"예상 시간: {review.get('estimated_duration', {}).get('total', 0)}초")
        print(
            f"검증 상태: {'통과' if review.get('validation_status', {}).get('is_valid') else '실패'}")

        alternatives = review.get('alternatives', [])
        if alternatives:
            print(f"대안 계획: {len(alternatives)}개")

    print(f"최종 승인: {'예' if result.get('is_approved') else '아니오'}")
    print(f"단계별 실행: {'예' if result.get('step_by_step_execution') else '아니오'}")


def test_error_handling():
    """오류 처리 기능 테스트"""
    print("\n=== 오류 처리 테스트 ===")

    analyzer = InstructionAnalyzer()

    # 잘못된 HTML로 오류 유발
    invalid_instruction = "이상한 지시사항 @@##$$"
    invalid_html = "<html><body><div>잘못된 HTML</div>"  # 닫는 태그 없음

    result = analyzer.analyze_instruction(
        invalid_instruction, invalid_html, "https://invalid-url")

    print(f"처리 단계: {result['processing_stage']}")
    print(f"검증 오류: {len(result.get('validation_errors', []))}개")

    if result.get('error_report'):
        error_report = result['error_report']
        print(f"\n=== 오류 보고서 ===")
        print(f"오류 수: {error_report['error_count']}")
        print(f"시스템 상태:")
        for key, value in error_report['system_state'].items():
            print(f"  {key}: {value}")

    # 오류 대안 제시 테스트
    alternatives = analyzer._suggest_error_alternatives(result)
    if alternatives:
        print(f"\n=== 제안된 대안 ({len(alternatives)}개) ===")
        for alt in alternatives[:3]:  # 처음 3개만 표시
            print(f"- {alt['title']}: {alt['description']}")
            print(
                f"  성공 확률: {alt['success_probability']}, 예상 시간: {alt['estimated_time']}")


def test_recovery_mechanisms():
    """복구 메커니즘 테스트"""
    print("\n=== 복구 메커니즘 테스트 ===")

    analyzer = InstructionAnalyzer()

    # 기본 상태 생성
    test_state = analyzer._create_initial_state(
        "테스트 지시사항",
        "<html><body>테스트</body></html>",
        "https://test.com"
    )

    # 의도적으로 오류 추가
    test_state["validation_errors"] = [
        ValidationError(
            error_type="llm_api_error",
            message="API 호출 실패",
            suggested_fix="대체 모델 사용"
        )
    ]

    # 복구 전략 테스트
    try:
        error = Exception("테스트 오류")
        recovered_state = analyzer._handle_workflow_error(
            error, test_state, "test_node")

        print(f"복구 후 처리 단계: {recovered_state['processing_stage']}")
        print(
            f"복구 후 오류 수: {len(recovered_state.get('validation_errors', []))}")

        # 대안 액션 실행 테스트
        recovered_state = analyzer._execute_alternative_action(
            "use_basic_mode", recovered_state)
        print(f"기본 모드 활성화: {recovered_state.get('basic_mode', False)}")

    except Exception as e:
        print(f"복구 테스트 중 오류: {e}")
