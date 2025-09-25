"""
지시사항 분석 에이전트 - 추상적인 지시사항을 구체적인 실행 계획으로 변환
"""

# gRPC 경고 메시지 억제
from page_analyzer import PageAnalyzer
from instruction_analyzer_types import (
    InstructionAnalyzerState,
    ExecutionStep,
    PageContext,
    PageElement,
    UserIntent,
    ValidationError,
    UserQuestion,
    ActionType,
    ValidationStatus,
    PlanStatus,
    DEFAULT_USER_RESPONSE_TIMEOUT,
    DEFAULT_LLM_TIMEOUT,
    MIN_CONFIDENCE_THRESHOLD,
    MAX_RETRY_ATTEMPTS,
    ERROR_MESSAGES
)
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables.graph_mermaid import MermaidDrawMethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import uuid
import json
import os
import asyncio
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GRPC_TRACE'] = ''


# 로컬 모듈 임포트

# 환경 변수 로드
load_dotenv()


class InstructionAnalyzer:
    """
    지시사항 분석 에이전트

    사용자의 추상적인 지시사항을 받아서 현재 웹페이지 상황을 분석하고,
    브라우저 에이전트가 실행할 수 있는 구체적이고 순차적인 단계별 지시사항으로 변환합니다.
    """

    def __init__(self, model_name: str = "gemini-2.0-flash", temperature: float = 0.1):
        """
        지시사항 분석 에이전트 초기화

        Args:
            model_name: 사용할 LLM 모델명
            temperature: LLM 온도 설정 (0.0 ~ 1.0)
        """
        # LLM 모델 초기화
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temperature,
            timeout=DEFAULT_LLM_TIMEOUT
        )

        # 페이지 분석 에이전트 연동
        self.page_analyzer = PageAnalyzer()

        # 설정값들
        self.max_retry_attempts = MAX_RETRY_ATTEMPTS
        self.min_confidence_threshold = MIN_CONFIDENCE_THRESHOLD
        self.user_response_timeout = DEFAULT_USER_RESPONSE_TIMEOUT

        # LangGraph 워크플로우 구축
        self.graph = self._build_graph()

        # 세션 관리
        self.current_session_id = None

        # 그래프 시각화를 비동기로 처리
        self._schedule_graph_visualization()

        print("🤖 InstructionAnalyzer 초기화 완료")

    def analyze_instruction(
        self,
        user_instruction: str,
        html_content: str,
        current_url: str
    ) -> InstructionAnalyzerState:
        """
        지시사항 분석의 메인 진입점

        Args:
            user_instruction: 사용자의 자연어 지시사항
            html_content: 현재 페이지의 HTML 콘텐츠
            current_url: 현재 페이지 URL

        Returns:
            InstructionAnalyzerState: 분석 완료된 상태
        """
        print(f"🔍 지시사항 분석 시작: '{user_instruction[:50]}...'")

        # 초기 상태 생성
        initial_state = self._create_initial_state(
            user_instruction, html_content, current_url
        )

        # LangGraph 워크플로우 실행
        try:
            result = self.graph.invoke(initial_state, {"recursion_limit": 10})
            print("✅ 워크플로우 실행 완료")

            # 최종 오류 보고서 생성
            if result.get("validation_errors"):
                error_report = self._create_error_report(result)
                result["error_report"] = error_report
                print(f"📊 오류 보고서 생성 - {error_report['error_count']}개 오류")

            return result
        except Exception as e:
            print(f"❌ 워크플로우 실행 실패: {e}")
            # 포괄적인 오류 처리 적용
            failed_state = self._handle_workflow_error(
                e, initial_state, "workflow")

            # 오류 보고서 생성
            error_report = self._create_error_report(failed_state)
            failed_state["error_report"] = error_report

            return failed_state

    def _create_initial_state(
        self,
        user_instruction: str,
        html_content: str,
        current_url: str
    ) -> InstructionAnalyzerState:
        """
        초기 상태 생성

        Args:
            user_instruction: 사용자 지시사항
            html_content: HTML 콘텐츠
            current_url: 현재 URL

        Returns:
            InstructionAnalyzerState: 초기화된 상태
        """
        session_id = str(uuid.uuid4())
        current_time = datetime.now().isoformat()

        self.current_session_id = session_id

        return InstructionAnalyzerState(
            # 입력 데이터
            user_instruction=user_instruction,
            html_content=html_content,
            current_url=current_url,

            # 분석 결과 (초기값)
            parsed_intent=None,
            page_analysis=None,
            identified_elements=[],

            # 실행 계획 (초기값)
            execution_steps=[],
            plan_status=PlanStatus.DRAFT,

            # 검증 및 오류 처리 (초기값)
            validation_errors=[],
            missing_info=[],

            # Human-in-the-Loop (초기값)
            user_questions=[],
            user_responses={},
            awaiting_user_input=False,

            # 상태 관리
            current_step=0,
            processing_stage="analyzing_instruction",
            action_parameters={},

            # 모드 설정
            basic_mode=False,
            manual_mode=False,
            offline_mode=False,
            auto_proceed=False,
            fallback_model_active=False,

            # 결과 및 승인 (초기값)
            is_approved=False,
            final_plan=None,
            selected_element=None,
            review_info=None,
            step_by_step_execution=False,

            # 메타데이터
            created_at=current_time,
            last_updated=current_time,
            session_id=session_id,
            error_report=None
        )

    def get_session_info(self) -> Dict[str, Any]:
        """
        현재 세션 정보 반환

        Returns:
            Dict: 세션 정보
        """
        return {
            "session_id": self.current_session_id,
            "model_name": self.llm.model_name if hasattr(self.llm, 'model_name') else "unknown",
            "temperature": getattr(self.llm, 'temperature', 0.1),
            "max_retry_attempts": self.max_retry_attempts,
            "min_confidence_threshold": self.min_confidence_threshold,
            "user_response_timeout": self.user_response_timeout
        }

    def validate_input(self, user_instruction: str, html_content: str, current_url: str) -> List[str]:
        """
        입력값 검증

        Args:
            user_instruction: 사용자 지시사항
            html_content: HTML 콘텐츠
            current_url: 현재 URL

        Returns:
            List[str]: 검증 오류 메시지 목록 (빈 리스트면 검증 통과)
        """
        errors = []

        if not user_instruction or not user_instruction.strip():
            errors.append("사용자 지시사항이 비어있습니다")

        if not html_content or not html_content.strip():
            errors.append("HTML 콘텐츠가 비어있습니다")

        if not current_url or not current_url.strip():
            errors.append("현재 URL이 비어있습니다")

        if len(user_instruction) > 1000:
            errors.append("지시사항이 너무 깁니다 (최대 1000자)")

        return errors

    def reset_session(self):
        """세션 초기화"""
        self.current_session_id = None
        print("🔄 세션이 초기화되었습니다")

    def get_supported_actions(self) -> List[str]:
        """
        지원되는 액션 타입 목록 반환

        Returns:
            List[str]: 지원되는 액션 타입들
        """
        return [action.value for action in ActionType]

    def get_error_message(self, error_type: str, **kwargs) -> str:
        """
        오류 메시지 생성

        Args:
            error_type: 오류 타입
            **kwargs: 메시지 포맷팅을 위한 추가 인자들

        Returns:
            str: 포맷팅된 오류 메시지
        """
        template = ERROR_MESSAGES.get(error_type, "알 수 없는 오류가 발생했습니다")
        try:
            return template.format(**kwargs)
        except KeyError as e:
            return f"오류 메시지 포맷팅 실패: {e}"

    def _build_graph(self) -> StateGraph:
        """
        LangGraph 워크플로우 구축

        Returns:
            StateGraph: 컴파일된 상태 그래프
        """
        print("🔧 LangGraph 워크플로우 구축 중...")

        # StateGraph 생성
        graph_builder = StateGraph(InstructionAnalyzerState)

        # 노드 추가
        graph_builder.add_node("analyze_instruction",
                               self._analyze_instruction_node)
        graph_builder.add_node("analyze_page", self._analyze_page_node)
        graph_builder.add_node("validate_requirements",
                               self._validate_requirements_node)
        graph_builder.add_node("human_interaction",
                               self._human_interaction_node)
        graph_builder.add_node("generate_plan", self._generate_plan_node)
        graph_builder.add_node("review_plan", self._review_plan_node)

        # 진입점 설정
        graph_builder.set_entry_point("analyze_instruction")

        # 조건부 엣지 추가
        graph_builder.add_conditional_edges(
            "analyze_instruction",
            self._route_after_instruction_analysis,
            {
                "analyze_page": "analyze_page",
                "failed": END
            }
        )

        graph_builder.add_conditional_edges(
            "analyze_page",
            self._route_after_page_analysis,
            {
                "validate_requirements": "validate_requirements",
                "failed": END
            }
        )

        graph_builder.add_conditional_edges(
            "validate_requirements",
            self._route_after_validation,
            {
                "human_interaction": "human_interaction",
                "generate_plan": "generate_plan",
                "failed": END
            }
        )

        graph_builder.add_conditional_edges(
            "human_interaction",
            self._route_after_human_interaction,
            {
                "validate_requirements": "validate_requirements",
                "generate_plan": "generate_plan",
                "failed": END
            }
        )

        graph_builder.add_conditional_edges(
            "generate_plan",
            self._route_after_plan_generation,
            {
                "review_plan": "review_plan",
                "failed": END
            }
        )

        graph_builder.add_conditional_edges(
            "review_plan",
            self._route_after_plan_review,
            {
                "human_interaction": "human_interaction",
                "completed": END
            }
        )

        # 그래프 컴파일
        compiled_graph = graph_builder.compile()
        print("✅ LangGraph 워크플로우 구축 완료")

        return compiled_graph

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
            print("🔄 InstructionAnalyzer 그래프 시각화 생성 중...")

            # 절대 경로로 파일 저장 위치 설정
            current_dir = os.path.dirname(os.path.abspath(__file__))
            output_path = os.path.join(
                current_dir, "instruction_analyzer_graph.png")

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

            print(f"✅ InstructionAnalyzer 그래프 시각화 저장: {output_path}")
        except Exception as e:
            print(f"⚠️ InstructionAnalyzer 그래프 시각화 실패: {e}")
            # 최후의 수단으로 동기 방식 시도
            try:
                print("🔄 동기 방식으로 그래프 시각화 재시도...")
                current_dir = os.path.dirname(os.path.abspath(__file__))
                output_path = os.path.join(
                    current_dir, "instruction_analyzer_graph.png")

                mermaid_png = self.graph.get_graph().draw_mermaid_png()
                with open(output_path, "wb") as f:
                    f.write(mermaid_png)
                print(f"✅ InstructionAnalyzer 그래프 시각화 저장 (동기): {output_path}")
            except Exception as sync_e:
                print(f"⚠️ 동기 방식도 실패: {sync_e}")

    # === 지시사항 파싱 메서드 ===

    def _parse_user_instruction(self, user_instruction: str) -> UserIntent:
        """
        사용자 지시사항을 파싱하여 의도를 추출

        Args:
            user_instruction: 사용자의 자연어 지시사항

        Returns:
            UserIntent: 파싱된 사용자 의도
        """
        print(f"🔍 지시사항 파싱 중: '{user_instruction}'")

        try:
            # LLM을 사용한 지시사항 분석 프롬프트
            analysis_prompt = ChatPromptTemplate.from_messages([
                ("system", """당신은 사용자의 웹 브라우저 조작 지시사항을 분석하는 전문가입니다.

사용자의 지시사항을 분석하여 다음 정보를 JSON 형태로 추출해주세요:

1. primary_goal: 주요 목표 (예: "search", "login", "navigate", "purchase", "read", "download" 등)
2. target_objects: 대상 객체들의 배열 (예: ["날씨", "검색창", "로그인 버튼"] 등)
3. actions_sequence: 예상되는 액션 시퀀스 배열 (예: ["find_search_box", "type_text", "click_search"] 등)
4. constraints: 제약 조건들의 배열 (예: ["네이버 사이트에서만", "로그인 후에만"] 등)
5. success_criteria: 성공 기준 (예: "검색 결과가 표시됨", "로그인이 완료됨" 등)
6. confidence_score: 해석 신뢰도 (0.0 ~ 1.0)

응답은 반드시 유효한 JSON 형태로만 제공해주세요. 다른 설명은 포함하지 마세요.

예시:
사용자 지시사항: "네이버에서 오늘의 날씨를 검색해주세요"
응답:
{{
  "primary_goal": "search",
  "target_objects": ["날씨", "검색창", "검색 버튼"],
  "actions_sequence": ["find_search_box", "type_weather_query", "click_search", "read_results"],
  "constraints": ["네이버 사이트에서"],
  "success_criteria": "날씨 정보가 검색 결과에 표시됨",
  "confidence_score": 0.9
}}"""),
                ("user", "사용자 지시사항: {instruction}")
            ])

            # LLM 호출
            chain = analysis_prompt | self.llm
            response = chain.invoke({"instruction": user_instruction})

            # JSON 파싱
            try:
                parsed_data = json.loads(response.content.strip())
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON 파싱 실패, 기본값 사용: {e}")
                # JSON 파싱 실패시 기본값 사용
                parsed_data = self._create_fallback_intent(user_instruction)

            # UserIntent 객체 생성
            intent = UserIntent(
                primary_goal=parsed_data.get("primary_goal", "unknown"),
                target_objects=parsed_data.get("target_objects", []),
                actions_sequence=parsed_data.get("actions_sequence", []),
                constraints=parsed_data.get("constraints", []),
                success_criteria=parsed_data.get("success_criteria", ""),
                confidence_score=float(
                    parsed_data.get("confidence_score", 0.5))
            )

            print(
                f"✅ 파싱 완료 - 목표: {intent.primary_goal}, 대상: {intent.target_objects}")
            return intent

        except Exception as e:
            print(f"❌ 지시사항 파싱 실패: {e}")
            # 오류 발생시 폴백 의도 생성
            return self._create_fallback_intent(user_instruction)

    def _create_fallback_intent(self, user_instruction: str) -> UserIntent:
        """
        파싱 실패시 폴백 의도 생성

        Args:
            user_instruction: 원본 지시사항

        Returns:
            UserIntent: 기본 의도 객체
        """
        print("🔄 폴백 의도 생성 중...")

        # 간단한 키워드 기반 분석
        instruction_lower = user_instruction.lower()

        # 기본 목표 추정
        if any(keyword in instruction_lower for keyword in ["검색", "찾", "search"]):
            primary_goal = "search"
        elif any(keyword in instruction_lower for keyword in ["로그인", "login", "signin"]):
            primary_goal = "login"
        elif any(keyword in instruction_lower for keyword in ["이동", "가", "navigate", "go"]):
            primary_goal = "navigate"
        elif any(keyword in instruction_lower for keyword in ["클릭", "click", "누르"]):
            primary_goal = "click"
        elif any(keyword in instruction_lower for keyword in ["입력", "type", "쓰"]):
            primary_goal = "type"
        else:
            primary_goal = "unknown"

        # 기본 대상 객체 추정
        target_objects = []
        common_targets = {
            "검색창": ["검색창", "search", "입력"],
            "버튼": ["버튼", "button", "클릭"],
            "링크": ["링크", "link", "연결"],
            "날씨": ["날씨", "weather", "기상"],
            "뉴스": ["뉴스", "news", "기사"]
        }

        for target, keywords in common_targets.items():
            if any(keyword in instruction_lower for keyword in keywords):
                target_objects.append(target)

        return UserIntent(
            primary_goal=primary_goal,
            target_objects=target_objects,
            actions_sequence=[
                primary_goal] if primary_goal != "unknown" else [],
            constraints=[],
            success_criteria="작업이 성공적으로 완료됨",
            confidence_score=0.3  # 낮은 신뢰도
        )

    def _extract_action_parameters(self, user_instruction: str, intent: UserIntent) -> Dict[str, Any]:
        """
        지시사항에서 액션 매개변수 추출

        Args:
            user_instruction: 원본 지시사항
            intent: 파싱된 의도

        Returns:
            Dict: 추출된 매개변수들
        """
        parameters = {}

        # 텍스트 입력 매개변수 추출
        if intent.primary_goal in ["search", "type"]:
            # 따옴표 안의 텍스트 추출
            import re
            quoted_text = re.findall(r'["\']([^"\']+)["\']', user_instruction)
            if quoted_text:
                parameters["text"] = quoted_text[0]
            else:
                # 일반적인 검색어 패턴 추출
                search_patterns = [
                    r'검색해?\s*[:\-]?\s*(.+?)(?:\s|$)',
                    r'찾아?\s*[:\-]?\s*(.+?)(?:\s|$)',
                    r'입력해?\s*[:\-]?\s*(.+?)(?:\s|$)'
                ]
                for pattern in search_patterns:
                    match = re.search(pattern, user_instruction)
                    if match:
                        parameters["text"] = match.group(1).strip()
                        break

        # URL 매개변수 추출
        if intent.primary_goal == "navigate":
            import re
            url_pattern = r'https?://[^\s]+'
            urls = re.findall(url_pattern, user_instruction)
            if urls:
                parameters["url"] = urls[0]

        return parameters

    def _validate_and_clarify_instruction(self, intent: UserIntent, user_instruction: str) -> tuple[bool, List[ValidationError], List[UserQuestion]]:
        """
        지시사항 검증 및 명확화 필요 사항 확인

        Args:
            intent: 파싱된 사용자 의도
            user_instruction: 원본 지시사항

        Returns:
            tuple: (is_valid, validation_errors, clarification_questions)
        """
        print("🔍 지시사항 검증 및 명확화 검사 중...")

        validation_errors = []
        clarification_questions = []

        # 1. 신뢰도 검사
        if intent.confidence_score < self.min_confidence_threshold:
            validation_errors.append(
                ValidationError(
                    error_type="low_confidence",
                    message=f"지시사항 해석 신뢰도가 낮습니다 ({intent.confidence_score:.2f})",
                    suggested_fix="더 구체적인 지시사항을 제공해주세요",
                    requires_user_input=True
                )
            )

            clarification_questions.append(
                UserQuestion(
                    question_id="clarify_intent",
                    question_text=f"'{user_instruction}'를 더 구체적으로 설명해주세요. 어떤 작업을 원하시나요?",
                    question_type="text",
                    timeout_seconds=60
                )
            )

        # 2. 모호한 목표 검사
        if intent.primary_goal == "unknown":
            validation_errors.append(
                ValidationError(
                    error_type="ambiguous_goal",
                    message="지시사항의 목표를 파악할 수 없습니다",
                    suggested_fix="구체적인 동작을 명시해주세요 (예: 검색, 클릭, 입력 등)",
                    requires_user_input=True
                )
            )

            clarification_questions.append(
                UserQuestion(
                    question_id="specify_goal",
                    question_text="어떤 작업을 수행하고 싶으신가요?",
                    question_type="choice",
                    options=["검색하기", "클릭하기", "텍스트 입력하기", "페이지 이동하기", "기타"],
                    timeout_seconds=30
                )
            )

        # 3. 대상 객체 부족 검사
        if not intent.target_objects:
            validation_errors.append(
                ValidationError(
                    error_type="missing_target",
                    message="작업 대상을 찾을 수 없습니다",
                    suggested_fix="구체적인 대상을 명시해주세요 (예: 검색창, 버튼, 링크 등)",
                    requires_user_input=True
                )
            )

            clarification_questions.append(
                UserQuestion(
                    question_id="specify_target",
                    question_text=f"'{intent.primary_goal}' 작업을 어떤 요소에 대해 수행하시겠습니까?",
                    question_type="text",
                    timeout_seconds=30
                )
            )

        # 4. 필수 매개변수 검사
        missing_params = self._check_missing_parameters(
            intent, user_instruction)
        if missing_params:
            for param_name, param_description in missing_params.items():
                validation_errors.append(
                    ValidationError(
                        error_type="missing_parameter",
                        message=f"필수 매개변수 '{param_name}'가 누락되었습니다",
                        suggested_fix=f"{param_description}를 제공해주세요",
                        requires_user_input=True
                    )
                )

                clarification_questions.append(
                    UserQuestion(
                        question_id=f"provide_{param_name}",
                        question_text=f"{param_description}를 입력해주세요:",
                        question_type="text",
                        timeout_seconds=30
                    )
                )

        # 5. 실행 불가능한 요청 검사
        impossible_reasons = self._check_impossible_requests(intent)
        if impossible_reasons:
            for reason in impossible_reasons:
                validation_errors.append(
                    ValidationError(
                        error_type="impossible_request",
                        message=f"실행 불가능한 요청: {reason}",
                        suggested_fix="다른 방법을 시도해보세요",
                        requires_user_input=False
                    )
                )

        is_valid = len(
            [e for e in validation_errors if e.requires_user_input]) == 0

        print(
            f"✅ 검증 완료 - 유효: {is_valid}, 오류: {len(validation_errors)}개, 질문: {len(clarification_questions)}개")

        return is_valid, validation_errors, clarification_questions

    def _check_missing_parameters(self, intent: UserIntent, user_instruction: str) -> Dict[str, str]:
        """
        필수 매개변수 누락 검사

        Args:
            intent: 파싱된 의도
            user_instruction: 원본 지시사항

        Returns:
            Dict: 누락된 매개변수들 {param_name: description}
        """
        missing_params = {}

        # 검색/입력 작업에 텍스트 필요
        if intent.primary_goal in ["search", "type"]:
            # 텍스트 추출 시도
            import re
            has_text = bool(
                re.search(r'["\']([^"\']+)["\']', user_instruction))
            if not has_text:
                # 일반적인 검색어 패턴 확인
                search_patterns = [
                    r'검색해?\s*[:\-]?\s*(.+?)(?:\s|$)',
                    r'찾아?\s*[:\-]?\s*(.+?)(?:\s|$)',
                    r'입력해?\s*[:\-]?\s*(.+?)(?:\s|$)'
                ]
                has_search_term = any(re.search(pattern, user_instruction)
                                      for pattern in search_patterns)

                if not has_search_term:
                    if intent.primary_goal == "search":
                        missing_params["search_text"] = "검색할 내용"
                    else:
                        missing_params["input_text"] = "입력할 텍스트"

        # 네비게이션에 URL 필요
        if intent.primary_goal == "navigate":
            import re
            has_url = bool(re.search(r'https?://[^\s]+', user_instruction))
            if not has_url:
                # 사이트 이름이라도 있는지 확인
                site_patterns = [
                    r'(네이버|구글|다음|유튜브|페이스북)',
                    r'([a-zA-Z0-9-]+\.(com|net|org|co\.kr))',
                ]
                has_site = any(re.search(pattern, user_instruction)
                               for pattern in site_patterns)

                if not has_site:
                    missing_params["target_url"] = "이동할 웹사이트 주소 또는 사이트명"

        return missing_params

    def _check_impossible_requests(self, intent: UserIntent) -> List[str]:
        """
        실행 불가능한 요청 검사

        Args:
            intent: 파싱된 의도

        Returns:
            List[str]: 불가능한 이유들
        """
        impossible_reasons = []

        # 너무 복잡한 작업
        if len(intent.actions_sequence) > 10:
            impossible_reasons.append("작업이 너무 복잡합니다. 단계를 나누어 요청해주세요")

        # 지원하지 않는 액션
        unsupported_actions = []
        supported_actions = [action.value for action in ActionType]

        for action in intent.actions_sequence:
            if action not in supported_actions and action not in ["find_search_box", "read_results", "click_search"]:
                unsupported_actions.append(action)

        if unsupported_actions:
            impossible_reasons.append(
                f"지원하지 않는 작업: {', '.join(unsupported_actions)}")

        # 모순된 제약 조건
        if len(intent.constraints) > 1:
            # 예: "네이버에서만" + "구글에서만"
            site_constraints = [c for c in intent.constraints if any(
                site in c for site in ["네이버", "구글", "다음"])]
            if len(site_constraints) > 1:
                impossible_reasons.append("상충되는 사이트 제약 조건이 있습니다")

        return impossible_reasons

    # === 페이지 분석 메서드 ===

    def _analyze_page_context(self, html_content: str, current_url: str) -> PageContext:
        """
        현재 페이지의 컨텍스트를 분석

        Args:
            html_content: 페이지 HTML 콘텐츠
            current_url: 현재 페이지 URL

        Returns:
            PageContext: 분석된 페이지 컨텍스트
        """
        print(f"🔍 페이지 컨텍스트 분석 중: {current_url}")

        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # 기본 정보 추출
            title = self._extract_page_title(soup)
            page_type = self._determine_page_type(soup, current_url)

            # 주요 UI 요소들 분석
            main_elements = self._extract_main_elements(soup)
            forms = self._extract_forms(soup)
            navigation = self._extract_navigation(soup)
            content_areas = self._extract_content_areas(soup)
            interactive_elements = self._extract_interactive_elements(soup)

            page_context = PageContext(
                url=current_url,
                title=title,
                main_elements=main_elements,
                forms=forms,
                navigation=navigation,
                content_areas=content_areas,
                interactive_elements=interactive_elements,
                page_type=page_type
            )

            print(f"✅ 페이지 분석 완료 - 타입: {page_type}, 요소: {len(main_elements)}개")
            return page_context

        except Exception as e:
            print(f"❌ 페이지 분석 실패: {e}")
            # 기본 페이지 컨텍스트 반환
            return PageContext(
                url=current_url,
                title="분석 실패",
                page_type="unknown"
            )

    def _extract_page_title(self, soup: BeautifulSoup) -> str:
        """페이지 제목 추출"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()

        # title 태그가 없으면 h1 태그 확인
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()

        return "제목 없음"

    def _determine_page_type(self, soup: BeautifulSoup, url: str) -> str:
        """페이지 타입 결정"""
        url_lower = url.lower()

        # URL 기반 판단
        if 'search' in url_lower or 'query' in url_lower:
            return "search"
        elif 'login' in url_lower or 'signin' in url_lower:
            return "login"
        elif 'shop' in url_lower or 'store' in url_lower or 'buy' in url_lower:
            return "e-commerce"
        elif 'news' in url_lower or 'article' in url_lower:
            return "news"
        elif 'social' in url_lower or 'facebook' in url_lower or 'twitter' in url_lower:
            return "social_media"

        # HTML 구조 기반 판단
        # 검색 페이지 특징
        search_indicators = soup.find_all(
            ['input'], {'type': ['search', 'text']})
        if len(search_indicators) > 0:
            search_buttons = soup.find_all(['button', 'input'], string=lambda text: text and (
                '검색' in text or 'search' in text.lower()))
            if search_buttons:
                return "search"

        # 폼 페이지 특징
        forms = soup.find_all('form')
        if len(forms) > 0:
            # 로그인 폼 확인
            login_inputs = soup.find_all(['input'], {'type': ['password']})
            if login_inputs:
                return "form"

            # 일반 폼
            if len(forms) >= 2:
                return "form"

        # 대시보드 특징
        dashboard_indicators = soup.find_all(['div'], class_=lambda x: x and any(
            keyword in x.lower() for keyword in ['dashboard', 'panel', 'admin', 'control']
        ))
        if dashboard_indicators:
            return "dashboard"

        # 기사/콘텐츠 페이지 특징
        article_tags = soup.find_all(['article', 'main'])
        if article_tags:
            return "article"

        return "unknown"

    def _extract_main_elements(self, soup: BeautifulSoup) -> List[PageElement]:
        """주요 UI 요소들 추출"""
        elements = []

        # 검색 관련 요소들
        search_inputs = soup.find_all(['input'], {'type': ['search', 'text']})
        for i, input_elem in enumerate(search_inputs):
            if self._is_search_input(input_elem):
                selector = self._generate_css_selector(input_elem)
                elements.append(PageElement(
                    element_type="search_input",
                    selector=selector,
                    description=f"검색 입력창 {i+1}",
                    attributes=dict(input_elem.attrs),
                    is_visible=self._is_visible(input_elem),
                    is_interactive=True
                ))

        # 버튼들
        buttons = soup.find_all(['button', 'input'], {
                                'type': ['submit', 'button']})
        for i, button in enumerate(buttons):
            selector = self._generate_css_selector(button)
            button_text = self._get_element_text(button)
            elements.append(PageElement(
                element_type="button",
                selector=selector,
                description=f"버튼: {button_text}" if button_text else f"버튼 {i+1}",
                attributes=dict(button.attrs),
                text_content=button_text,
                is_visible=self._is_visible(button),
                is_interactive=True
            ))

        # 링크들 (주요한 것만)
        links = soup.find_all('a', href=True)
        important_links = []
        for link in links:
            link_text = self._get_element_text(link).strip()
            if len(link_text) > 2 and len(link_text) < 50:  # 적절한 길이의 링크만
                important_links.append(link)

        for i, link in enumerate(important_links[:10]):  # 최대 10개만
            selector = self._generate_css_selector(link)
            link_text = self._get_element_text(link)
            elements.append(PageElement(
                element_type="link",
                selector=selector,
                description=f"링크: {link_text}",
                attributes=dict(link.attrs),
                text_content=link_text,
                is_visible=self._is_visible(link),
                is_interactive=True
            ))

        return elements

    def _extract_forms(self, soup: BeautifulSoup) -> List[PageElement]:
        """폼 요소들 추출"""
        elements = []

        forms = soup.find_all('form')
        for i, form in enumerate(forms):
            selector = self._generate_css_selector(form)
            form_inputs = form.find_all(['input', 'textarea', 'select'])

            elements.append(PageElement(
                element_type="form",
                selector=selector,
                description=f"폼 {i+1} ({len(form_inputs)}개 입력 필드)",
                attributes=dict(form.attrs),
                is_visible=self._is_visible(form),
                is_interactive=True
            ))

        return elements

    def _extract_navigation(self, soup: BeautifulSoup) -> List[PageElement]:
        """네비게이션 요소들 추출"""
        elements = []

        # nav 태그
        nav_elements = soup.find_all('nav')
        for i, nav in enumerate(nav_elements):
            selector = self._generate_css_selector(nav)
            elements.append(PageElement(
                element_type="navigation",
                selector=selector,
                description=f"네비게이션 {i+1}",
                attributes=dict(nav.attrs),
                is_visible=self._is_visible(nav),
                is_interactive=True
            ))

        # 메뉴 클래스를 가진 요소들
        menu_elements = soup.find_all(['div', 'ul'], class_=lambda x: x and any(
            keyword in x.lower() for keyword in ['menu', 'nav', 'navigation']
        ))
        for i, menu in enumerate(menu_elements):
            selector = self._generate_css_selector(menu)
            elements.append(PageElement(
                element_type="menu",
                selector=selector,
                description=f"메뉴 {i+1}",
                attributes=dict(menu.attrs),
                is_visible=self._is_visible(menu),
                is_interactive=True
            ))

        return elements

    def _extract_content_areas(self, soup: BeautifulSoup) -> List[PageElement]:
        """콘텐츠 영역들 추출"""
        elements = []

        # main, article 태그
        content_tags = soup.find_all(['main', 'article', 'section'])
        for i, content in enumerate(content_tags):
            selector = self._generate_css_selector(content)
            elements.append(PageElement(
                element_type="content_area",
                selector=selector,
                description=f"{content.name} 콘텐츠 영역 {i+1}",
                attributes=dict(content.attrs),
                is_visible=self._is_visible(content),
                is_interactive=False
            ))

        return elements

    def _extract_interactive_elements(self, soup: BeautifulSoup) -> List[PageElement]:
        """상호작용 가능한 요소들 추출"""
        elements = []

        # 클릭 가능한 요소들
        clickable_selectors = [
            'button', 'a[href]', 'input[type="submit"]', 'input[type="button"]',
            '[onclick]', '[role="button"]'
        ]

        for selector_str in clickable_selectors:
            clickable_elements = soup.select(selector_str)
            for elem in clickable_elements[:5]:  # 각 타입별로 최대 5개
                selector = self._generate_css_selector(elem)
                elem_text = self._get_element_text(elem)
                elements.append(PageElement(
                    element_type="interactive",
                    selector=selector,
                    description=f"클릭 가능: {elem_text}" if elem_text else f"클릭 가능 요소",
                    attributes=dict(elem.attrs),
                    text_content=elem_text,
                    is_visible=self._is_visible(elem),
                    is_interactive=True
                ))

        return elements

    # === 헬퍼 메서드들 ===

    def _is_search_input(self, input_elem) -> bool:
        """입력 요소가 검색창인지 판단"""
        attrs = input_elem.attrs

        # type이 search인 경우
        if attrs.get('type') == 'search':
            return True

        # name이나 id에 search 포함
        name = attrs.get('name', '').lower()
        id_attr = attrs.get('id', '').lower()
        placeholder = attrs.get('placeholder', '').lower()

        search_keywords = ['search', 'query', '검색', 'q']

        return any(keyword in name or keyword in id_attr or keyword in placeholder
                   for keyword in search_keywords)

    def _generate_css_selector(self, element) -> str:
        """요소에 대한 CSS 셀렉터 생성"""
        # ID가 있으면 ID 사용
        if element.get('id'):
            return f"#{element['id']}"

        # 클래스가 있으면 클래스 사용
        if element.get('class'):
            classes = ' '.join(element['class'])
            return f"{element.name}.{'.'.join(element['class'])}"

        # name 속성이 있으면 사용
        if element.get('name'):
            return f"{element.name}[name='{element['name']}']"

        # type 속성이 있으면 사용
        if element.get('type'):
            return f"{element.name}[type='{element['type']}']"

        # 기본적으로 태그명만 사용
        return element.name

    def _get_element_text(self, element) -> str:
        """요소의 텍스트 내용 추출"""
        # value 속성 확인 (input 요소의 경우)
        if element.get('value'):
            return element['value']

        # placeholder 확인
        if element.get('placeholder'):
            return element['placeholder']

        # 텍스트 내용 확인
        text = element.get_text().strip()
        if text:
            return text[:100]  # 최대 100자

        # alt 속성 확인 (img 요소의 경우)
        if element.get('alt'):
            return element['alt']

        # title 속성 확인
        if element.get('title'):
            return element['title']

        return ""

    def _is_visible(self, element) -> bool:
        """요소가 가시적인지 판단 (간단한 휴리스틱)"""
        style = element.get('style', '').lower()

        # display: none 또는 visibility: hidden 확인
        if 'display:none' in style.replace(' ', '') or 'visibility:hidden' in style.replace(' ', ''):
            return False

        # hidden 속성 확인
        if element.get('hidden') is not None:
            return False

        # 클래스명으로 숨김 여부 추정
        classes = ' '.join(element.get('class', [])).lower()
        hidden_keywords = ['hidden', 'invisible', 'hide', 'none']
        if any(keyword in classes for keyword in hidden_keywords):
            return False

        return True

    # === PageAnalyzer 연동 메서드 ===

    def _enhance_elements_with_page_analyzer(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """
        PageAnalyzer를 사용하여 요소 식별을 향상시킴

        Args:
            state: 현재 상태

        Returns:
            InstructionAnalyzerState: 향상된 상태
        """
        print("🔗 PageAnalyzer와 연동하여 요소 식별 향상 중...")

        try:
            parsed_intent = state.get("parsed_intent")
            if not parsed_intent:
                print("⚠️ 파싱된 의도가 없어 PageAnalyzer 연동을 건너뜁니다")
                return state

            # 사용자 의도에 기반한 요소 검색 쿼리 생성
            search_queries = self._generate_element_search_queries(
                parsed_intent)

            enhanced_elements = []
            for query in search_queries:
                print(f"🔍 PageAnalyzer로 '{query}' 검색 중...")

                # PageAnalyzer 실행
                analyzer_result = self.page_analyzer.run(
                    query=query,
                    html_content=state["html_content"]
                )

                if analyzer_result.get("selector") and analyzer_result.get("extracted_elements"):
                    # PageAnalyzer 결과를 PageElement로 변환
                    page_elements = self._convert_analyzer_results_to_elements(
                        query, analyzer_result
                    )
                    enhanced_elements.extend(page_elements)
                    print(f"✅ '{query}'로 {len(page_elements)}개 요소 발견")
                else:
                    print(f"⚠️ '{query}'에 해당하는 요소를 찾지 못했습니다")

            # 기존 요소들과 중복 제거하여 병합
            existing_selectors = {
                elem.selector for elem in state["identified_elements"]}
            new_elements = [
                elem for elem in enhanced_elements if elem.selector not in existing_selectors]

            if new_elements:
                state["identified_elements"].extend(new_elements)
                print(f"✅ PageAnalyzer로 {len(new_elements)}개 새로운 요소 추가")
            else:
                print("ℹ️ PageAnalyzer로 새로운 요소를 찾지 못했습니다")

        except Exception as e:
            print(f"❌ PageAnalyzer 연동 실패: {e}")
            # 연동 실패해도 기존 분석 결과는 유지

        return state

    def _generate_element_search_queries(self, intent: UserIntent) -> List[str]:
        """
        사용자 의도에 기반한 요소 검색 쿼리 생성

        Args:
            intent: 파싱된 사용자 의도

        Returns:
            List[str]: 검색 쿼리 목록
        """
        queries = []

        # 1. 대상 객체 기반 쿼리
        for target_obj in intent.target_objects:
            queries.append(target_obj)

        # 2. 주요 목표 기반 쿼리
        goal_to_queries = {
            "search": ["검색창", "검색 버튼", "search box", "search button"],
            "login": ["로그인", "로그인 버튼", "아이디 입력", "비밀번호 입력"],
            "navigate": ["메뉴", "네비게이션", "링크"],
            "click": ["버튼", "링크", "클릭 가능한 요소"],
            "type": ["입력창", "텍스트 필드", "input field"],
            "scroll": ["스크롤", "더보기", "페이지 하단"],
            "wait": [],  # 대기는 특별한 요소가 필요 없음
            "analyze": ["주요 콘텐츠", "메인 영역"]
        }

        if intent.primary_goal in goal_to_queries:
            queries.extend(goal_to_queries[intent.primary_goal])

        # 3. 액션 시퀀스 기반 쿼리
        action_to_queries = {
            "find_search_box": ["검색창", "검색 입력창"],
            "type_text": ["입력창", "텍스트 필드"],
            "click_search": ["검색 버튼", "검색"],
            "click_button": ["버튼"],
            "read_results": ["결과", "검색 결과", "콘텐츠"],
            "find_login": ["로그인", "로그인 폼"],
            "enter_credentials": ["아이디", "비밀번호", "사용자명"]
        }

        for action in intent.actions_sequence:
            if action in action_to_queries:
                queries.extend(action_to_queries[action])

        # 4. 제약 조건 기반 쿼리 (특정 사이트의 특별한 요소들)
        for constraint in intent.constraints:
            if "네이버" in constraint:
                queries.extend(["네이버 검색창", "통합검색"])
            elif "구글" in constraint:
                queries.extend(["Google 검색", "검색창"])
            elif "유튜브" in constraint:
                queries.extend(["동영상 검색", "검색창"])

        # 중복 제거 및 빈 문자열 제거
        unique_queries = list(set(query.strip()
                              for query in queries if query.strip()))

        print(f"📋 생성된 검색 쿼리: {unique_queries}")
        return unique_queries

    def _convert_analyzer_results_to_elements(self, query: str, analyzer_result: dict) -> List[PageElement]:
        """
        PageAnalyzer 결과를 PageElement 객체로 변환

        Args:
            query: 검색 쿼리
            analyzer_result: PageAnalyzer 결과

        Returns:
            List[PageElement]: 변환된 PageElement 목록
        """
        elements = []

        selector = analyzer_result.get("selector")
        extracted_elements = analyzer_result.get("extracted_elements", [])

        if not selector:
            return elements

        # 요소 타입 추정
        element_type = self._estimate_element_type(query, selector)

        # 각 추출된 요소에 대해 PageElement 생성
        for i, html_content in enumerate(extracted_elements):
            try:
                from bs4 import BeautifulSoup
                elem_soup = BeautifulSoup(html_content, 'html.parser')
                elem = elem_soup.find()

                if elem:
                    text_content = self._get_element_text(elem)

                    page_element = PageElement(
                        element_type=element_type,
                        selector=selector,
                        description=f"{query} - {text_content}" if text_content else f"{query} {i+1}",
                        attributes=dict(elem.attrs) if elem.attrs else {},
                        text_content=text_content,
                        is_visible=True,  # PageAnalyzer가 찾은 요소는 일반적으로 가시적
                        is_interactive=self._is_interactive_element_type(
                            element_type)
                    )

                    elements.append(page_element)

            except Exception as e:
                print(f"⚠️ 요소 변환 실패: {e}")
                continue

        return elements

    def _estimate_element_type(self, query: str, selector: str) -> str:
        """
        쿼리와 셀렉터를 기반으로 요소 타입 추정

        Args:
            query: 검색 쿼리
            selector: CSS 셀렉터

        Returns:
            str: 추정된 요소 타입
        """
        query_lower = query.lower()
        selector_lower = selector.lower()

        # 쿼리 기반 타입 추정
        if any(keyword in query_lower for keyword in ["검색창", "search", "입력"]):
            return "search_input"
        elif any(keyword in query_lower for keyword in ["버튼", "button"]):
            return "button"
        elif any(keyword in query_lower for keyword in ["링크", "link"]):
            return "link"
        elif any(keyword in query_lower for keyword in ["폼", "form", "로그인"]):
            return "form"
        elif any(keyword in query_lower for keyword in ["메뉴", "menu", "네비게이션", "nav"]):
            return "navigation"
        elif any(keyword in query_lower for keyword in ["콘텐츠", "content", "결과", "result"]):
            return "content_area"

        # 셀렉터 기반 타입 추정
        if "input" in selector_lower:
            if "search" in selector_lower:
                return "search_input"
            else:
                return "input"
        elif "button" in selector_lower:
            return "button"
        elif "a[" in selector_lower or "link" in selector_lower:
            return "link"
        elif "form" in selector_lower:
            return "form"
        elif "nav" in selector_lower:
            return "navigation"

        return "unknown"

    def _is_interactive_element_type(self, element_type: str) -> bool:
        """요소 타입이 상호작용 가능한지 판단"""
        interactive_types = {
            "search_input", "button", "link", "form", "input",
            "navigation", "menu", "interactive"
        }
        return element_type in interactive_types

    def _find_best_matching_elements(self, intent: UserIntent, identified_elements: List[PageElement]) -> List[PageElement]:
        """
        사용자 의도에 가장 적합한 요소들을 찾음

        Args:
            intent: 사용자 의도
            identified_elements: 식별된 요소들

        Returns:
            List[PageElement]: 매칭되는 요소들 (우선순위 순)
        """
        matching_elements = []

        # 목표별 우선순위 요소 타입
        goal_priorities = {
            "search": ["search_input", "input", "button"],
            "login": ["form", "input", "button"],
            "navigate": ["link", "navigation", "menu"],
            "click": ["button", "link", "interactive"],
            "type": ["input", "search_input", "form"]
        }

        priority_types = goal_priorities.get(intent.primary_goal, [])

        # 우선순위 타입별로 요소 수집
        for element_type in priority_types:
            type_elements = [
                elem for elem in identified_elements if elem.element_type == element_type]
            matching_elements.extend(type_elements)

        # 대상 객체와 매칭되는 요소들 추가
        for target_obj in intent.target_objects:
            target_lower = target_obj.lower()
            for elem in identified_elements:
                if (target_lower in elem.description.lower() or
                        target_lower in elem.text_content.lower()):
                    if elem not in matching_elements:
                        matching_elements.append(elem)

        return matching_elements

    # === 정보 부족 감지 메서드 ===

    def _detect_missing_information(self, state: InstructionAnalyzerState) -> tuple[List[str], List[UserQuestion]]:
        """
        실행에 필요한 정보 부족 감지

        Args:
            state: 현재 상태

        Returns:
            tuple: (missing_info_list, clarification_questions)
        """
        print("🔍 정보 부족 감지 중...")

        missing_info = []
        questions = []

        parsed_intent = state.get("parsed_intent")
        page_analysis = state.get("page_analysis")
        identified_elements = state.get("identified_elements", [])
        action_parameters = state.get("action_parameters", {})

        # 1. 기본 분석 결과 부족 검사
        basic_missing, basic_questions = self._check_basic_analysis_completeness(
            parsed_intent, page_analysis
        )
        missing_info.extend(basic_missing)
        questions.extend(basic_questions)

        # 2. 실행 가능한 요소 부족 검사
        if parsed_intent:
            element_missing, element_questions = self._check_executable_elements(
                parsed_intent, identified_elements
            )
            missing_info.extend(element_missing)
            questions.extend(element_questions)

        # 3. 액션별 필수 매개변수 검사
        if parsed_intent:
            param_missing, param_questions = self._check_action_parameters(
                parsed_intent, action_parameters
            )
            missing_info.extend(param_missing)
            questions.extend(param_questions)

        # 4. 컨텍스트 일치성 검사
        if parsed_intent and page_analysis:
            context_missing, context_questions = self._check_context_compatibility(
                parsed_intent, page_analysis
            )
            missing_info.extend(context_missing)
            questions.extend(context_questions)

        # 5. 모호한 선택지 검사
        if parsed_intent and identified_elements:
            ambiguity_missing, ambiguity_questions = self._check_ambiguous_choices(
                parsed_intent, identified_elements
            )
            missing_info.extend(ambiguity_missing)
            questions.extend(ambiguity_questions)

        print(f"✅ 정보 부족 감지 완료 - {len(missing_info)}개 부족, {len(questions)}개 질문")

        return missing_info, questions

    def _check_basic_analysis_completeness(self, parsed_intent: UserIntent, page_analysis: PageContext) -> tuple[List[str], List[UserQuestion]]:
        """기본 분석 결과 완성도 검사"""
        missing_info = []
        questions = []

        # 의도 파싱 실패
        if not parsed_intent:
            missing_info.append("사용자 의도를 파악할 수 없습니다")
            questions.append(UserQuestion(
                question_id="clarify_intent",
                question_text="어떤 작업을 수행하고 싶으신가요? 구체적으로 설명해주세요.",
                question_type="text",
                timeout_seconds=60
            ))
        elif parsed_intent.confidence_score < self.min_confidence_threshold:
            missing_info.append(
                f"의도 해석 신뢰도가 낮습니다 ({parsed_intent.confidence_score:.2f})")
            questions.append(UserQuestion(
                question_id="confirm_intent",
                question_text=f"다음과 같이 이해했습니다: '{parsed_intent.primary_goal}' 작업을 수행하시겠습니까?",
                question_type="confirmation",
                options=["예", "아니오"],
                timeout_seconds=30
            ))

        # 페이지 분석 실패
        if not page_analysis:
            missing_info.append("페이지 구조를 분석할 수 없습니다")
            questions.append(UserQuestion(
                question_id="page_info",
                question_text="현재 페이지에 대해 알려주세요. 어떤 종류의 페이지인가요?",
                question_type="choice",
                options=["검색 페이지", "로그인 페이지", "쇼핑몰", "뉴스 사이트", "기타"],
                timeout_seconds=30
            ))
        elif page_analysis.page_type == "unknown":
            missing_info.append("페이지 타입을 확정할 수 없습니다")
            questions.append(UserQuestion(
                question_id="confirm_page_type",
                question_text="현재 페이지의 주요 기능은 무엇인가요?",
                question_type="choice",
                options=["검색", "로그인", "쇼핑", "정보 읽기", "기타"],
                timeout_seconds=30
            ))

        return missing_info, questions

    def _check_executable_elements(self, intent: UserIntent, elements: List[PageElement]) -> tuple[List[str], List[UserQuestion]]:
        """실행 가능한 요소 존재 여부 검사"""
        missing_info = []
        questions = []

        # 목표별 필수 요소 타입
        required_elements = {
            "search": ["search_input", "input"],
            "login": ["form", "input"],
            "click": ["button", "link", "interactive"],
            "type": ["input", "search_input"],
            "navigate": ["link", "navigation"]
        }

        if intent.primary_goal in required_elements:
            required_types = required_elements[intent.primary_goal]
            available_elements = [
                elem for elem in elements if elem.element_type in required_types]

            if not available_elements:
                missing_info.append(
                    f"'{intent.primary_goal}' 작업에 필요한 요소를 찾을 수 없습니다")
                questions.append(UserQuestion(
                    question_id="find_elements",
                    question_text=f"'{intent.primary_goal}' 작업을 위한 요소(버튼, 입력창 등)가 페이지에 있나요?",
                    question_type="choice",
                    options=["예, 있습니다", "아니오, 없습니다", "잘 모르겠습니다"],
                    timeout_seconds=30
                ))
            elif len(available_elements) > 5:
                # 너무 많은 선택지가 있는 경우
                missing_info.append(
                    f"'{intent.primary_goal}' 작업 가능한 요소가 너무 많습니다 ({len(available_elements)}개)")
                questions.append(UserQuestion(
                    question_id="specify_element",
                    question_text="어떤 요소를 사용하시겠습니까? 더 구체적으로 설명해주세요.",
                    question_type="text",
                    timeout_seconds=45
                ))

        # 대상 객체별 요소 매칭 검사
        for target_obj in intent.target_objects:
            matching_elements = [
                elem for elem in elements
                if target_obj.lower() in elem.description.lower() or
                target_obj.lower() in elem.text_content.lower()
            ]

            if not matching_elements:
                missing_info.append(f"'{target_obj}' 요소를 찾을 수 없습니다")
                questions.append(UserQuestion(
                    question_id=f"locate_{target_obj}",
                    question_text=f"'{target_obj}' 요소가 페이지의 어디에 있는지 알려주세요.",
                    question_type="text",
                    timeout_seconds=30
                ))

        return missing_info, questions

    def _check_action_parameters(self, intent: UserIntent, parameters: Dict[str, Any]) -> tuple[List[str], List[UserQuestion]]:
        """액션별 필수 매개변수 검사"""
        missing_info = []
        questions = []

        # 검색/입력 작업에 텍스트 필요
        if intent.primary_goal in ["search", "type"]:
            if not parameters.get("text") and not any("text" in obj.lower() for obj in intent.target_objects):
                missing_info.append("입력할 텍스트가 지정되지 않았습니다")

                if intent.primary_goal == "search":
                    questions.append(UserQuestion(
                        question_id="search_text",
                        question_text="무엇을 검색하시겠습니까?",
                        question_type="text",
                        timeout_seconds=30
                    ))
                else:
                    questions.append(UserQuestion(
                        question_id="input_text",
                        question_text="어떤 텍스트를 입력하시겠습니까?",
                        question_type="text",
                        timeout_seconds=30
                    ))

        # 네비게이션에 URL 또는 대상 필요
        if intent.primary_goal == "navigate":
            if not parameters.get("url") and not intent.target_objects:
                missing_info.append("이동할 대상이 지정되지 않았습니다")
                questions.append(UserQuestion(
                    question_id="navigation_target",
                    question_text="어디로 이동하시겠습니까? (URL 또는 링크명)",
                    question_type="text",
                    timeout_seconds=30
                ))

        # 클릭 작업에 대상 필요
        if intent.primary_goal == "click":
            if not intent.target_objects:
                missing_info.append("클릭할 대상이 지정되지 않았습니다")
                questions.append(UserQuestion(
                    question_id="click_target",
                    question_text="무엇을 클릭하시겠습니까?",
                    question_type="text",
                    timeout_seconds=30
                ))

        return missing_info, questions

    def _check_context_compatibility(self, intent: UserIntent, page_analysis: PageContext) -> tuple[List[str], List[UserQuestion]]:
        """컨텍스트 일치성 검사"""
        missing_info = []
        questions = []

        # 페이지 타입과 의도 일치성 검사
        compatibility_map = {
            "search": ["search", "unknown"],
            "login": ["form", "login", "unknown"],
            "navigate": ["unknown"],  # 모든 페이지에서 가능
            "click": ["unknown"],     # 모든 페이지에서 가능
            "type": ["form", "search", "unknown"]
        }

        if intent.primary_goal in compatibility_map:
            compatible_types = compatibility_map[intent.primary_goal]
            if page_analysis.page_type not in compatible_types:
                missing_info.append(
                    f"현재 페이지({page_analysis.page_type})에서 '{intent.primary_goal}' 작업이 적절하지 않을 수 있습니다")
                questions.append(UserQuestion(
                    question_id="confirm_compatibility",
                    question_text=f"현재 페이지에서 '{intent.primary_goal}' 작업을 계속 진행하시겠습니까?",
                    question_type="confirmation",
                    options=["예", "아니오"],
                    timeout_seconds=30
                ))

        # 제약 조건과 페이지 URL 일치성 검사
        for constraint in intent.constraints:
            if "네이버" in constraint and "naver.com" not in page_analysis.url.lower():
                missing_info.append("네이버 사이트가 아닌 곳에서 네이버 관련 작업을 요청했습니다")
                questions.append(UserQuestion(
                    question_id="site_mismatch",
                    question_text="네이버 사이트로 이동한 후 작업을 진행하시겠습니까?",
                    question_type="confirmation",
                    options=["예", "아니오"],
                    timeout_seconds=30
                ))
            elif "구글" in constraint and "google.com" not in page_analysis.url.lower():
                missing_info.append("구글 사이트가 아닌 곳에서 구글 관련 작업을 요청했습니다")
                questions.append(UserQuestion(
                    question_id="site_mismatch_google",
                    question_text="구글 사이트로 이동한 후 작업을 진행하시겠습니까?",
                    question_type="confirmation",
                    options=["예", "아니오"],
                    timeout_seconds=30
                ))

        return missing_info, questions

    def _check_ambiguous_choices(self, intent: UserIntent, elements: List[PageElement]) -> tuple[List[str], List[UserQuestion]]:
        """모호한 선택지 검사"""
        missing_info = []
        questions = []

        # 동일한 타입의 요소가 여러 개 있는 경우
        element_type_counts = {}
        for elem in elements:
            if elem.is_interactive:
                element_type_counts[elem.element_type] = element_type_counts.get(
                    elem.element_type, 0) + 1

        # 목표에 따른 모호성 검사
        if intent.primary_goal == "search":
            search_inputs = [elem for elem in elements if elem.element_type in [
                "search_input", "input"]]
            if len(search_inputs) > 1:
                missing_info.append(
                    f"검색 입력창이 {len(search_inputs)}개 있어 어느 것을 사용할지 모호합니다")

                input_descriptions = [
                    f"{i+1}. {elem.description}" for i, elem in enumerate(search_inputs[:5])]
                questions.append(UserQuestion(
                    question_id="choose_search_input",
                    question_text="어떤 검색창을 사용하시겠습니까?",
                    question_type="choice",
                    options=input_descriptions + ["첫 번째 것 사용"],
                    timeout_seconds=30
                ))

        elif intent.primary_goal == "click":
            if not intent.target_objects:
                clickable_elements = [
                    elem for elem in elements if elem.element_type in ["button", "link"]]
                if len(clickable_elements) > 10:
                    missing_info.append(
                        f"클릭 가능한 요소가 {len(clickable_elements)}개로 너무 많습니다")
                    questions.append(UserQuestion(
                        question_id="specify_click_target",
                        question_text="클릭할 요소를 더 구체적으로 설명해주세요 (예: '검색 버튼', '로그인 링크')",
                        question_type="text",
                        timeout_seconds=45
                    ))

        # 대상 객체가 여러 요소와 매칭되는 경우
        for target_obj in intent.target_objects:
            matching_elements = [
                elem for elem in elements
                if target_obj.lower() in elem.description.lower() or
                target_obj.lower() in elem.text_content.lower()
            ]

            if len(matching_elements) > 3:
                missing_info.append(
                    f"'{target_obj}'와 매칭되는 요소가 {len(matching_elements)}개로 너무 많습니다")

                element_options = [
                    f"{elem.element_type}: {elem.description}" for elem in matching_elements[:5]]
                questions.append(UserQuestion(
                    question_id=f"choose_{target_obj}",
                    question_text=f"'{target_obj}' 중 어떤 것을 선택하시겠습니까?",
                    question_type="choice",
                    options=element_options + ["첫 번째 것 사용"],
                    timeout_seconds=30
                ))

        return missing_info, questions

    # === 사용자 상호작용 메서드 ===

    def _generate_contextual_questions(self, state: InstructionAnalyzerState) -> List[UserQuestion]:
        """
        현재 상황에 맞는 컨텍스트 기반 질문 생성

        Args:
            state: 현재 상태

        Returns:
            List[UserQuestion]: 생성된 질문들
        """
        print("❓ 컨텍스트 기반 질문 생성 중...")

        questions = []
        parsed_intent = state.get("parsed_intent")
        page_analysis = state.get("page_analysis")
        identified_elements = state.get("identified_elements", [])

        # 1. 진행 상황 기반 질문
        if state["processing_stage"] == "validating_requirements":
            questions.extend(self._generate_validation_questions(state))
        elif state["processing_stage"] == "generating_plan":
            questions.extend(self._generate_planning_questions(state))
        elif state["processing_stage"] == "awaiting_review":
            questions.extend(self._generate_review_questions(state))

        # 2. 의도 불명확시 명확화 질문
        if parsed_intent and parsed_intent.confidence_score < 0.6:
            questions.append(UserQuestion(
                question_id="low_confidence_clarification",
                question_text=f"다음과 같이 이해했는데 맞나요? '{parsed_intent.primary_goal}' 작업을 {', '.join(parsed_intent.target_objects)}에 대해 수행하시겠습니까?",
                question_type="confirmation",
                options=["맞습니다", "다릅니다", "다시 설명하겠습니다"],
                timeout_seconds=45
            ))

        # 3. 요소 선택 질문
        if parsed_intent and len(identified_elements) > 0:
            choice_questions = self._generate_element_choice_questions(
                parsed_intent, identified_elements)
            questions.extend(choice_questions)

        print(f"✅ {len(questions)}개 컨텍스트 질문 생성")
        return questions

    def _generate_validation_questions(self, state: InstructionAnalyzerState) -> List[UserQuestion]:
        """검증 단계 질문 생성"""
        questions = []
        missing_info = state.get("missing_info", [])

        if missing_info:
            # 가장 중요한 누락 정보에 대한 질문
            priority_missing = missing_info[0]  # 첫 번째가 가장 중요

            if "의도" in priority_missing:
                questions.append(UserQuestion(
                    question_id="clarify_main_intent",
                    question_text="정확히 어떤 작업을 수행하고 싶으신가요? 단계별로 설명해주세요.",
                    question_type="text",
                    timeout_seconds=60
                ))
            elif "요소" in priority_missing:
                questions.append(UserQuestion(
                    question_id="describe_target_element",
                    question_text="작업하려는 요소(버튼, 링크, 입력창 등)에 대해 더 자세히 설명해주세요.",
                    question_type="text",
                    timeout_seconds=45
                ))
            elif "텍스트" in priority_missing:
                questions.append(UserQuestion(
                    question_id="provide_text_input",
                    question_text="입력하거나 검색할 텍스트를 알려주세요.",
                    question_type="text",
                    timeout_seconds=30
                ))

        return questions

    def _generate_planning_questions(self, state: InstructionAnalyzerState) -> List[UserQuestion]:
        """계획 생성 단계 질문 생성"""
        questions = []
        parsed_intent = state.get("parsed_intent")

        if parsed_intent and len(parsed_intent.actions_sequence) > 5:
            questions.append(UserQuestion(
                question_id="simplify_plan",
                question_text="작업이 복잡해 보입니다. 단계를 나누어 진행하시겠습니까?",
                question_type="choice",
                options=["예, 단계별로 진행", "아니오, 한 번에 진행", "일부만 먼저 진행"],
                timeout_seconds=30
            ))

        return questions

    def _generate_review_questions(self, state: InstructionAnalyzerState) -> List[UserQuestion]:
        """검토 단계 질문 생성"""
        questions = []
        execution_steps = state.get("execution_steps", [])

        if execution_steps:
            questions.append(UserQuestion(
                question_id="approve_execution_plan",
                question_text=f"생성된 {len(execution_steps)}단계 실행 계획을 검토해주세요. 진행하시겠습니까?",
                question_type="choice",
                options=["승인하고 진행", "수정 요청", "다시 생성", "취소"],
                timeout_seconds=60
            ))

        return questions

    def _generate_element_choice_questions(self, intent: UserIntent, elements: List[PageElement]) -> List[UserQuestion]:
        """요소 선택 질문 생성"""
        questions = []

        # 목표에 맞는 요소들 필터링
        relevant_elements = self._find_best_matching_elements(intent, elements)

        if len(relevant_elements) > 1:
            # 여러 선택지가 있는 경우
            element_options = []
            for i, elem in enumerate(relevant_elements[:5]):  # 최대 5개
                option_text = f"{elem.element_type}: {elem.description}"
                if elem.text_content:
                    option_text += f" ('{elem.text_content[:20]}...')"
                element_options.append(option_text)

            questions.append(UserQuestion(
                question_id="choose_target_element",
                question_text=f"'{intent.primary_goal}' 작업을 위해 어떤 요소를 사용하시겠습니까?",
                question_type="choice",
                options=element_options + ["자동으로 선택"],
                timeout_seconds=45
            ))

        return questions

    def _process_user_responses(self, state: InstructionAnalyzerState, responses: Dict[str, str]) -> InstructionAnalyzerState:
        """
        사용자 응답 처리 및 상태 업데이트

        Args:
            state: 현재 상태
            responses: 사용자 응답들 {question_id: response}

        Returns:
            InstructionAnalyzerState: 업데이트된 상태
        """
        print(f"📝 사용자 응답 처리 중... ({len(responses)}개 응답)")

        # 응답을 상태에 저장
        state["user_responses"].update(responses)

        for question_id, response in responses.items():
            print(f"  - {question_id}: {response}")

            # 응답에 따른 상태 업데이트
            if question_id == "clarify_intent" or question_id == "clarify_main_intent":
                # 의도 재분석
                updated_intent = self._reanalyze_intent_with_clarification(
                    state.get("parsed_intent"), response
                )
                if updated_intent:
                    state["parsed_intent"] = updated_intent
                    print(f"  → 의도 업데이트: {updated_intent.primary_goal}")

            elif question_id == "provide_text_input" or question_id.startswith("search_text") or question_id.startswith("input_text"):
                # 액션 매개변수 업데이트
                if "action_parameters" not in state:
                    state["action_parameters"] = {}
                state["action_parameters"]["text"] = response
                print(f"  → 텍스트 매개변수 추가: {response}")

            elif question_id.startswith("choose_") and "element" in question_id:
                # 요소 선택 처리
                selected_element = self._process_element_selection(
                    state.get("identified_elements", []), response
                )
                if selected_element:
                    state["selected_element"] = selected_element
                    print(f"  → 요소 선택: {selected_element.description}")

            elif question_id == "approve_execution_plan":
                # 실행 계획 승인 처리
                if "승인" in response:
                    state["is_approved"] = True
                    state["plan_status"] = PlanStatus.APPROVED
                    print("  → 실행 계획 승인됨")
                elif "수정" in response:
                    # 계획 수정 실행
                    modification_requests = ["위험도 감소", "검증 단계 추가"]  # 기본 수정 요청
                    modified_steps = self._modify_execution_plan(
                        state, modification_requests)
                    state["execution_steps"] = modified_steps
                    state["plan_status"] = PlanStatus.UNDER_REVIEW
                    print("  → 실행 계획 수정 완료")
                elif "다시" in response:
                    # 계획 재생성 실행
                    regeneration_options = {
                        "strategy": "default", "focus": "accuracy", "complexity": "normal"}
                    regenerated_steps = self._regenerate_execution_plan(
                        state, regeneration_options)
                    state["execution_steps"] = regenerated_steps
                    state["plan_status"] = PlanStatus.DRAFT
                    print("  → 실행 계획 재생성 완료")

            elif question_id.endswith("_confirmation") or "confirm" in question_id:
                # 확인 질문 처리
                if response in ["예", "맞습니다", "yes"]:
                    print("  → 확인됨")
                else:
                    state["missing_info"].append(f"사용자가 {question_id}에 대해 거부함")
                    print("  → 거부됨, 추가 명확화 필요")

        # 응답 처리 후 missing_info 재검토
        self._update_missing_info_after_responses(state)

        print("✅ 사용자 응답 처리 완료")
        return state

    def _reanalyze_intent_with_clarification(self, original_intent: UserIntent, clarification: str) -> Optional[UserIntent]:
        """명확화 정보를 바탕으로 의도 재분석"""
        try:
            # 원본 지시사항과 명확화 정보를 결합하여 재분석
            combined_instruction = f"{original_intent.primary_goal if original_intent else ''} {clarification}"
            return self._parse_user_instruction(combined_instruction)
        except Exception as e:
            print(f"⚠️ 의도 재분석 실패: {e}")
            return original_intent

    def _process_element_selection(self, elements: List[PageElement], selection_response: str) -> Optional[PageElement]:
        """요소 선택 응답 처리"""
        try:
            # 숫자 선택 (예: "1", "첫 번째")
            if selection_response.isdigit():
                index = int(selection_response) - 1
                if 0 <= index < len(elements):
                    return elements[index]

            # 텍스트 매칭
            for element in elements:
                if (selection_response.lower() in element.description.lower() or
                        selection_response.lower() in element.text_content.lower()):
                    return element

            # 자동 선택
            if "자동" in selection_response:
                return elements[0] if elements else None

        except Exception as e:
            print(f"⚠️ 요소 선택 처리 실패: {e}")

        return None

    def _update_missing_info_after_responses(self, state: InstructionAnalyzerState):
        """응답 처리 후 missing_info 업데이트"""
        responses = state.get("user_responses", {})

        # 해결된 missing_info 제거
        resolved_items = []
        for item in state.get("missing_info", []):
            if "의도" in item and any("clarify" in qid for qid in responses.keys()):
                resolved_items.append(item)
            elif "텍스트" in item and any("text" in qid for qid in responses.keys()):
                resolved_items.append(item)
            elif "요소" in item and any("choose" in qid or "element" in qid for qid in responses.keys()):
                resolved_items.append(item)

        # 해결된 항목들 제거
        for item in resolved_items:
            if item in state["missing_info"]:
                state["missing_info"].remove(item)
                print(f"  → 해결됨: {item}")

    def _handle_user_timeout(self, state: InstructionAnalyzerState, timed_out_questions: List[str]) -> InstructionAnalyzerState:
        """사용자 응답 타임아웃 처리"""
        print(f"⏰ 사용자 응답 타임아웃: {len(timed_out_questions)}개 질문")

        for question_id in timed_out_questions:
            # 타임아웃된 질문에 대한 기본 처리
            question = next((q for q in state.get(
                "user_questions", []) if q.question_id == question_id), None)

            if question and question.default_answer:
                # 기본 답변 사용
                state["user_responses"][question_id] = question.default_answer
                print(f"  → {question_id}: 기본값 '{question.default_answer}' 사용")
            else:
                # 타임아웃으로 인한 자동 진행
                if "approve" in question_id:
                    state["is_approved"] = False
                    state["missing_info"].append("사용자 승인 타임아웃")
                elif "choose" in question_id:
                    # 첫 번째 선택지 자동 선택
                    if state.get("identified_elements"):
                        state["selected_element"] = state["identified_elements"][0]
                        print(
                            f"  → 자동 선택: {state['selected_element'].description}")

                print(f"  → {question_id}: 타임아웃으로 자동 처리")

        return state

    # === 워크플로우 노드 구현 ===

    def _analyze_instruction_node(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """
        지시사항 분석 노드 - 사용자 지시사항을 파싱하고 의도를 추출
        """
        print("📝 지시사항 분석 중...")

        try:
            state["processing_stage"] = "analyzing_instruction"
            state["last_updated"] = datetime.now().isoformat()

            # 자연어 지시사항 파싱 실행
            parsed_intent = self._parse_user_instruction(
                state["user_instruction"])
            state["parsed_intent"] = parsed_intent

            # 액션 매개변수 추출
            action_parameters = self._extract_action_parameters(
                state["user_instruction"], parsed_intent)
            if action_parameters:
                print(f"📋 추출된 매개변수: {action_parameters}")
                # 상태에 매개변수 저장 (나중에 실행 계획 생성시 사용)
                state["action_parameters"] = action_parameters

            # 지시사항 검증 및 명확화 검사
            is_valid, validation_errors, clarification_questions = self._validate_and_clarify_instruction(
                parsed_intent, state["user_instruction"]
            )

            # 검증 결과를 상태에 저장
            state["validation_errors"].extend(validation_errors)
            state["user_questions"].extend(clarification_questions)

            if not is_valid:
                print(
                    f"⚠️ 지시사항 검증 실패 - {len(validation_errors)}개 오류, {len(clarification_questions)}개 질문")
                # 명확화가 필요한 경우 missing_info에 추가
                for error in validation_errors:
                    if error.requires_user_input:
                        state["missing_info"].append(error.message)

            print(
                f"✅ 지시사항 분석 완료 - 목표: {parsed_intent.primary_goal}, 신뢰도: {parsed_intent.confidence_score:.2f}, 유효: {is_valid}")

        except Exception as e:
            print(f"❌ 지시사항 분석 실패: {e}")
            state = self._handle_workflow_error(
                e, state, "analyze_instruction")

        return state

    def _analyze_page_node(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """
        페이지 분석 노드 - 현재 페이지의 구조와 요소들을 분석
        """
        print("🔍 페이지 분석 중...")

        try:
            state["processing_stage"] = "analyzing_page"
            state["last_updated"] = datetime.now().isoformat()

            # 실제 페이지 컨텍스트 분석 실행
            page_context = self._analyze_page_context(
                state["html_content"],
                state["current_url"]
            )
            state["page_analysis"] = page_context

            # 식별된 요소들을 상태에 저장
            all_elements = (
                page_context.main_elements +
                page_context.forms +
                page_context.navigation +
                page_context.content_areas +
                page_context.interactive_elements
            )
            state["identified_elements"] = all_elements

            # PageAnalyzer와 연동하여 요소 식별 향상
            state = self._enhance_elements_with_page_analyzer(state)

            final_element_count = len(state["identified_elements"])
            print(
                f"✅ 페이지 분석 완료 - 타입: {page_context.page_type}, 총 {final_element_count}개 요소 식별")

        except Exception as e:
            print(f"❌ 페이지 분석 실패: {e}")
            state = self._handle_workflow_error(e, state, "analyze_page")

        return state

    def _validate_requirements_node(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """
        요구사항 검증 노드 - 지시사항 실행에 필요한 정보가 충분한지 검증
        """
        print("✅ 요구사항 검증 중...")

        try:
            state["processing_stage"] = "validating_requirements"
            state["last_updated"] = datetime.now().isoformat()

            # 정보 부족 감지 실행
            missing_info, clarification_questions = self._detect_missing_information(
                state)

            # 기존 missing_info와 병합 (중복 제거)
            existing_missing = set(state.get("missing_info", []))
            new_missing = [
                info for info in missing_info if info not in existing_missing]
            state["missing_info"].extend(new_missing)

            # 기존 질문과 병합 (중복 제거)
            existing_question_ids = {
                q.question_id for q in state.get("user_questions", [])}
            new_questions = [
                q for q in clarification_questions if q.question_id not in existing_question_ids]
            state["user_questions"].extend(new_questions)

            # 검증 결과 요약
            total_missing = len(state["missing_info"])
            total_questions = len(state["user_questions"])

            if total_missing > 0:
                print(
                    f"⚠️ 정보 부족 감지 - {total_missing}개 항목, {total_questions}개 질문")
                state["awaiting_user_input"] = total_questions > 0
            else:
                print("✅ 모든 필수 정보가 충족되었습니다")
                state["awaiting_user_input"] = False

            print("✅ 요구사항 검증 완료")

        except Exception as e:
            print(f"❌ 요구사항 검증 실패: {e}")
            state = self._handle_workflow_error(
                e, state, "validate_requirements")

        return state

    def _human_interaction_node(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """
        Human-in-the-Loop 노드 - 사용자와의 상호작용 처리
        """
        print("👤 사용자 상호작용 처리 중...")

        try:
            state["processing_stage"] = "awaiting_review"
            state["awaiting_user_input"] = True
            state["last_updated"] = datetime.now().isoformat()

            # 기존 질문이 없으면 컨텍스트 기반 질문 생성
            if not state.get("user_questions"):
                contextual_questions = self._generate_contextual_questions(
                    state)
                state["user_questions"].extend(contextual_questions)

            # 사용자 질문이 있는 경우 상호작용 시뮬레이션
            if state.get("user_questions"):
                print(f"📋 사용자에게 {len(state['user_questions'])}개 질문 제시:")

                # 실제 구현에서는 UI를 통해 사용자 입력을 받아야 함
                # 여기서는 테스트를 위해 자동 응답 시뮬레이션
                simulated_responses = self._simulate_user_responses(
                    state["user_questions"])

                if simulated_responses:
                    # 사용자 응답 처리
                    state = self._process_user_responses(
                        state, simulated_responses)
                    state["awaiting_user_input"] = False
                    print("✅ 사용자 응답 처리 완료")
                else:
                    # 응답이 없으면 타임아웃 처리
                    timed_out_questions = [
                        q.question_id for q in state["user_questions"]]
                    state = self._handle_user_timeout(
                        state, timed_out_questions)
                    state["awaiting_user_input"] = False
                    print("⏰ 타임아웃으로 자동 처리")
            else:
                # 질문이 없으면 바로 진행
                state["awaiting_user_input"] = False
                print("ℹ️ 추가 질문 없음, 진행")

            print("✅ 사용자 상호작용 완료")

        except Exception as e:
            print(f"❌ 사용자 상호작용 실패: {e}")
            state = self._handle_workflow_error(e, state, "human_interaction")

        return state

    def _simulate_user_responses(self, questions: List[UserQuestion]) -> Dict[str, str]:
        """
        테스트를 위한 사용자 응답 시뮬레이션
        실제 구현에서는 UI를 통해 실제 사용자 입력을 받아야 함
        """
        responses = {}

        for question in questions:
            print(f"  Q: {question.question_text}")

            # 질문 타입별 시뮬레이션 응답
            if question.question_type == "confirmation":
                responses[question.question_id] = "예"
                print(f"  A: 예")
            elif question.question_type == "choice" and question.options:
                responses[question.question_id] = question.options[0]
                print(f"  A: {question.options[0]}")
            elif question.question_type == "text":
                if "검색" in question.question_text:
                    responses[question.question_id] = "오늘의 날씨"
                elif "텍스트" in question.question_text:
                    responses[question.question_id] = "테스트 입력"
                else:
                    responses[question.question_id] = "자동 응답"
                print(f"  A: {responses[question.question_id]}")

        return responses

    # === 실행 계획 생성 메서드 ===

    def _generate_execution_plan(self, state: InstructionAnalyzerState) -> List[ExecutionStep]:
        """
        사용자 의도와 페이지 분석 결과를 바탕으로 실행 계획 생성

        Args:
            state: 현재 상태

        Returns:
            List[ExecutionStep]: 생성된 실행 단계들
        """
        print("📋 실행 계획 생성 중...")

        parsed_intent = state.get("parsed_intent")
        page_analysis = state.get("page_analysis")
        identified_elements = state.get("identified_elements", [])
        action_parameters = state.get("action_parameters", {})
        selected_element = state.get("selected_element")

        if not parsed_intent:
            print("❌ 파싱된 의도가 없어 계획 생성 불가")
            return []

        # 목표별 계획 생성 전략
        if parsed_intent.primary_goal == "search":
            steps = self._generate_search_plan(
                parsed_intent, identified_elements, action_parameters, selected_element)
        elif parsed_intent.primary_goal == "login":
            steps = self._generate_login_plan(
                parsed_intent, identified_elements, action_parameters)
        elif parsed_intent.primary_goal == "navigate":
            steps = self._generate_navigation_plan(
                parsed_intent, identified_elements, action_parameters)
        elif parsed_intent.primary_goal == "click":
            steps = self._generate_click_plan(
                parsed_intent, identified_elements, selected_element)
        elif parsed_intent.primary_goal == "type":
            steps = self._generate_type_plan(
                parsed_intent, identified_elements, action_parameters, selected_element)
        else:
            # 일반적인 계획 생성
            steps = self._generate_generic_plan(
                parsed_intent, identified_elements, action_parameters)

        # 단계 ID 할당 및 의존성 설정
        steps = self._assign_step_ids_and_dependencies(steps)

        # 검증 기준 및 대안 액션 추가
        steps = self._enhance_steps_with_validation(steps, parsed_intent)

        print(f"✅ {len(steps)}단계 실행 계획 생성 완료")
        return steps

    def _generate_search_plan(self, intent: UserIntent, elements: List[PageElement], parameters: Dict[str, Any], selected_element: Optional[PageElement]) -> List[ExecutionStep]:
        """검색 작업 계획 생성"""
        steps = []

        # 1. 검색 입력창 찾기 및 클릭
        search_input = selected_element if selected_element and selected_element.element_type in [
            "search_input", "input"] else None
        if not search_input:
            search_inputs = [elem for elem in elements if elem.element_type in [
                "search_input", "input"]]
            search_input = search_inputs[0] if search_inputs else None

        if search_input:
            steps.append(ExecutionStep(
                step_id=1,
                action_type=ActionType.CLICK,
                target_description=search_input.description,
                target_selector=search_input.selector,
                expected_outcome="검색 입력창이 활성화됨",
                validation_criteria="입력창에 커서가 표시됨"
            ))

            # 2. 검색어 입력
            search_text = parameters.get("text", "")
            if not search_text and intent.target_objects:
                search_text = " ".join(intent.target_objects)

            if search_text:
                steps.append(ExecutionStep(
                    step_id=2,
                    action_type=ActionType.TYPE,
                    target_description=search_input.description,
                    target_selector=search_input.selector,
                    parameters={"text": search_text},
                    expected_outcome=f"'{search_text}'가 입력됨",
                    validation_criteria="입력창에 텍스트가 표시됨",
                    dependencies=[1]
                ))

                # 3. 검색 실행 (Enter 키 또는 검색 버튼)
                search_buttons = [elem for elem in elements if elem.element_type == "button" and
                                  ("검색" in elem.description.lower() or "search" in elem.description.lower())]

                if search_buttons:
                    steps.append(ExecutionStep(
                        step_id=3,
                        action_type=ActionType.CLICK,
                        target_description=search_buttons[0].description,
                        target_selector=search_buttons[0].selector,
                        expected_outcome="검색이 실행됨",
                        validation_criteria="검색 결과 페이지로 이동",
                        dependencies=[2],
                        fallback_actions=["press_enter"]
                    ))
                else:
                    # 검색 버튼이 없으면 Enter 키 사용
                    steps.append(ExecutionStep(
                        step_id=3,
                        action_type=ActionType.VERIFY,  # Enter 키는 별도 처리 필요
                        target_description="검색 실행 (Enter 키)",
                        target_selector=search_input.selector,
                        parameters={"action": "press_enter"},
                        expected_outcome="검색이 실행됨",
                        validation_criteria="검색 결과 페이지로 이동",
                        dependencies=[2]
                    ))

                # 4. 결과 확인
                steps.append(ExecutionStep(
                    step_id=4,
                    action_type=ActionType.WAIT,
                    target_description="검색 결과 로딩 대기",
                    parameters={"duration": 3},
                    expected_outcome="검색 결과가 표시됨",
                    validation_criteria="검색 결과 요소가 페이지에 존재",
                    dependencies=[3]
                ))

        return steps

    def _generate_click_plan(self, intent: UserIntent, elements: List[PageElement], selected_element: Optional[PageElement]) -> List[ExecutionStep]:
        """클릭 작업 계획 생성"""
        steps = []

        target_element = selected_element
        if not target_element and intent.target_objects:
            # 대상 객체와 매칭되는 요소 찾기
            for target_obj in intent.target_objects:
                matching_elements = [elem for elem in elements if
                                     target_obj.lower() in elem.description.lower() or
                                     target_obj.lower() in elem.text_content.lower()]
                if matching_elements:
                    target_element = matching_elements[0]
                    break

        if not target_element:
            # 클릭 가능한 요소 중 첫 번째 선택
            clickable_elements = [
                elem for elem in elements if elem.is_interactive]
            target_element = clickable_elements[0] if clickable_elements else None

        if target_element:
            steps.append(ExecutionStep(
                step_id=1,
                action_type=ActionType.CLICK,
                target_description=target_element.description,
                target_selector=target_element.selector,
                expected_outcome=f"{target_element.description}이(가) 클릭됨",
                validation_criteria="클릭 후 상태 변화 확인"
            ))

        return steps

    def _generate_type_plan(self, intent: UserIntent, elements: List[PageElement], parameters: Dict[str, Any], selected_element: Optional[PageElement]) -> List[ExecutionStep]:
        """텍스트 입력 작업 계획 생성"""
        steps = []

        target_input = selected_element if selected_element and selected_element.element_type in [
            "input", "search_input"] else None
        if not target_input:
            input_elements = [elem for elem in elements if elem.element_type in [
                "input", "search_input"]]
            target_input = input_elements[0] if input_elements else None

        if target_input:
            # 1. 입력창 클릭
            steps.append(ExecutionStep(
                step_id=1,
                action_type=ActionType.CLICK,
                target_description=target_input.description,
                target_selector=target_input.selector,
                expected_outcome="입력창이 활성화됨"
            ))

            # 2. 텍스트 입력
            input_text = parameters.get("text", "")
            if not input_text and intent.target_objects:
                input_text = " ".join(intent.target_objects)

            if input_text:
                steps.append(ExecutionStep(
                    step_id=2,
                    action_type=ActionType.TYPE,
                    target_description=target_input.description,
                    target_selector=target_input.selector,
                    parameters={"text": input_text},
                    expected_outcome=f"'{input_text}'가 입력됨",
                    validation_criteria="입력창에 텍스트가 표시됨",
                    dependencies=[1]
                ))

        return steps

    def _generate_generic_plan(self, intent: UserIntent, elements: List[PageElement], parameters: Dict[str, Any]) -> List[ExecutionStep]:
        """일반적인 작업 계획 생성"""
        steps = []

        # 액션 시퀀스 기반 계획 생성
        for i, action in enumerate(intent.actions_sequence):
            if action == "find_search_box":
                search_inputs = [elem for elem in elements if elem.element_type in [
                    "search_input", "input"]]
                if search_inputs:
                    steps.append(ExecutionStep(
                        step_id=i+1,
                        action_type=ActionType.ANALYZE,
                        target_description="검색창 찾기",
                        target_selector=search_inputs[0].selector,
                        expected_outcome="검색창이 식별됨"
                    ))
            elif action == "click_button":
                buttons = [
                    elem for elem in elements if elem.element_type == "button"]
                if buttons:
                    steps.append(ExecutionStep(
                        step_id=i+1,
                        action_type=ActionType.CLICK,
                        target_description=buttons[0].description,
                        target_selector=buttons[0].selector,
                        expected_outcome="버튼이 클릭됨"
                    ))

        return steps

    def _assign_step_ids_and_dependencies(self, steps: List[ExecutionStep]) -> List[ExecutionStep]:
        """단계 ID 재할당 및 의존성 정리"""
        for i, step in enumerate(steps):
            step.step_id = i + 1

            # 의존성 업데이트 (이전 단계들과의 논리적 연결)
            if i > 0 and not step.dependencies:
                # 기본적으로 이전 단계에 의존
                step.dependencies = [i]

        return steps

    def _enhance_steps_with_validation(self, steps: List[ExecutionStep], intent: UserIntent) -> List[ExecutionStep]:
        """단계별 검증 기준 및 대안 액션 추가"""
        for step in steps:
            # 검증 기준 강화
            if not step.validation_criteria:
                if step.action_type == ActionType.CLICK:
                    step.validation_criteria = "요소가 클릭되고 상태가 변경됨"
                elif step.action_type == ActionType.TYPE:
                    step.validation_criteria = "텍스트가 정확히 입력됨"
                elif step.action_type == ActionType.NAVIGATE:
                    step.validation_criteria = "페이지 URL이 변경됨"
                elif step.action_type == ActionType.WAIT:
                    step.validation_criteria = "대기 시간이 완료됨"

            # 대안 액션 추가
            if not step.fallback_actions:
                if step.action_type == ActionType.CLICK:
                    step.fallback_actions = [
                        "retry_click", "scroll_to_element"]
                elif step.action_type == ActionType.TYPE:
                    step.fallback_actions = [
                        "clear_and_retype", "use_different_input"]
                elif step.action_type == ActionType.NAVIGATE:
                    step.fallback_actions = [
                        "refresh_page", "try_alternative_url"]

        return steps

    # === 실행 계획 최적화 및 검증 메서드 ===

    def _optimize_execution_plan(self, steps: List[ExecutionStep], intent: UserIntent) -> List[ExecutionStep]:
        """
        실행 계획 최적화

        Args:
            steps: 원본 실행 단계들
            intent: 사용자 의도

        Returns:
            List[ExecutionStep]: 최적화된 실행 단계들
        """
        print("⚡ 실행 계획 최적화 중...")

        if not steps:
            return steps

        # 1. 중복 단계 제거
        optimized_steps = self._remove_duplicate_steps(steps)

        # 2. 불필요한 단계 제거
        optimized_steps = self._remove_unnecessary_steps(
            optimized_steps, intent)

        # 3. 단계 순서 최적화
        optimized_steps = self._optimize_step_order(optimized_steps)

        # 4. 단계 병합 가능성 검토
        optimized_steps = self._merge_compatible_steps(optimized_steps)

        # 5. 성능 최적화 (대기 시간 조정 등)
        optimized_steps = self._optimize_performance(optimized_steps)

        # 단계 ID 재할당
        optimized_steps = self._assign_step_ids_and_dependencies(
            optimized_steps)

        print(f"✅ 최적화 완료 - {len(steps)}단계 → {len(optimized_steps)}단계")
        return optimized_steps

    def _remove_duplicate_steps(self, steps: List[ExecutionStep]) -> List[ExecutionStep]:
        """중복 단계 제거"""
        unique_steps = []
        seen_combinations = set()

        for step in steps:
            # 액션 타입, 대상, 매개변수 조합으로 중복 판단
            combination = (
                step.action_type,
                step.target_selector,
                str(step.parameters) if step.parameters else ""
            )

            if combination not in seen_combinations:
                unique_steps.append(step)
                seen_combinations.add(combination)
            else:
                print(f"  중복 단계 제거: {step.target_description}")

        return unique_steps

    def _remove_unnecessary_steps(self, steps: List[ExecutionStep], intent: UserIntent) -> List[ExecutionStep]:
        """불필요한 단계 제거"""
        necessary_steps = []

        for step in steps:
            is_necessary = True

            # ANALYZE 액션이 너무 많은 경우 제거
            if step.action_type == ActionType.ANALYZE:
                analyze_count = sum(
                    1 for s in steps if s.action_type == ActionType.ANALYZE)
                if analyze_count > 2:
                    is_necessary = False
                    print(f"  불필요한 분석 단계 제거: {step.target_description}")

            # 의도와 관련 없는 WAIT 단계 제거
            elif step.action_type == ActionType.WAIT:
                wait_duration = step.parameters.get(
                    "duration", 0) if step.parameters else 0
                if wait_duration > 10:  # 10초 이상 대기는 제거
                    is_necessary = False
                    print(f"  과도한 대기 단계 제거: {step.target_description}")

            # 의도와 맞지 않는 단계 제거
            elif not self._is_step_relevant_to_intent(step, intent):
                is_necessary = False
                print(f"  의도와 무관한 단계 제거: {step.target_description}")

            if is_necessary:
                necessary_steps.append(step)

        return necessary_steps

    def _is_step_relevant_to_intent(self, step: ExecutionStep, intent: UserIntent) -> bool:
        """단계가 사용자 의도와 관련있는지 판단"""
        # 대상 객체와 매칭 확인
        for target_obj in intent.target_objects:
            if target_obj.lower() in step.target_description.lower():
                return True

        # 액션 타입과 의도 일치성 확인
        intent_action_map = {
            "search": [ActionType.CLICK, ActionType.TYPE, ActionType.VERIFY, ActionType.WAIT],
            "login": [ActionType.CLICK, ActionType.TYPE],
            "navigate": [ActionType.NAVIGATE, ActionType.CLICK],
            "click": [ActionType.CLICK],
            "type": [ActionType.CLICK, ActionType.TYPE]
        }

        if intent.primary_goal in intent_action_map:
            return step.action_type in intent_action_map[intent.primary_goal]

        return True  # 기본적으로 관련있다고 가정

    def _optimize_step_order(self, steps: List[ExecutionStep]) -> List[ExecutionStep]:
        """단계 순서 최적화"""
        if len(steps) <= 1:
            return steps

        # 의존성 기반 정렬
        sorted_steps = []
        remaining_steps = steps.copy()

        while remaining_steps:
            # 의존성이 없거나 이미 처리된 단계들 찾기
            ready_steps = []
            for step in remaining_steps:
                if not step.dependencies or all(dep <= len(sorted_steps) for dep in step.dependencies):
                    ready_steps.append(step)

            if not ready_steps:
                # 순환 의존성이 있는 경우 첫 번째 단계 강제 추가
                ready_steps = [remaining_steps[0]]

            # 우선순위에 따라 정렬 (CLICK → TYPE → VERIFY → WAIT 순서)
            priority_order = {
                ActionType.CLICK: 1,
                ActionType.TYPE: 2,
                ActionType.VERIFY: 3,
                ActionType.WAIT: 4,
                ActionType.NAVIGATE: 0,
                ActionType.ANALYZE: 5,
                ActionType.SCROLL: 6
            }

            ready_steps.sort(
                key=lambda s: priority_order.get(s.action_type, 10))

            # 첫 번째 준비된 단계 추가
            next_step = ready_steps[0]
            sorted_steps.append(next_step)
            remaining_steps.remove(next_step)

        return sorted_steps

    def _merge_compatible_steps(self, steps: List[ExecutionStep]) -> List[ExecutionStep]:
        """호환 가능한 단계들 병합"""
        if len(steps) <= 1:
            return steps

        merged_steps = []
        i = 0

        while i < len(steps):
            current_step = steps[i]

            # 다음 단계와 병합 가능한지 확인
            if i + 1 < len(steps):
                next_step = steps[i + 1]

                # CLICK → TYPE 패턴을 하나의 단계로 병합 가능
                if (current_step.action_type == ActionType.CLICK and
                    next_step.action_type == ActionType.TYPE and
                        current_step.target_selector == next_step.target_selector):

                    # 병합된 단계 생성
                    merged_step = ExecutionStep(
                        step_id=current_step.step_id,
                        action_type=ActionType.TYPE,  # TYPE이 주 액션
                        target_description=f"{current_step.target_description} (클릭 후 입력)",
                        target_selector=current_step.target_selector,
                        parameters=next_step.parameters,
                        expected_outcome=next_step.expected_outcome,
                        validation_criteria=next_step.validation_criteria,
                        dependencies=current_step.dependencies,
                        fallback_actions=current_step.fallback_actions + next_step.fallback_actions
                    )

                    merged_steps.append(merged_step)
                    i += 2  # 두 단계를 건너뜀
                    print(
                        f"  단계 병합: {current_step.target_description} + {next_step.target_description}")
                    continue

            # 병합하지 않고 그대로 추가
            merged_steps.append(current_step)
            i += 1

        return merged_steps

    def _optimize_performance(self, steps: List[ExecutionStep]) -> List[ExecutionStep]:
        """성능 최적화"""
        for step in steps:
            # 대기 시간 최적화
            if step.action_type == ActionType.WAIT:
                duration = step.parameters.get(
                    "duration", 3) if step.parameters else 3
                if duration > 5:
                    # 긴 대기 시간을 줄임
                    step.parameters["duration"] = min(duration, 5)
                    print(
                        f"  대기 시간 최적화: {duration}초 → {step.parameters['duration']}초")

            # 타임아웃 설정 최적화
            if not hasattr(step, 'timeout'):
                if step.action_type == ActionType.CLICK:
                    step.timeout = 10
                elif step.action_type == ActionType.TYPE:
                    step.timeout = 15
                elif step.action_type == ActionType.NAVIGATE:
                    step.timeout = 30
                else:
                    step.timeout = 20

        return steps

    def _validate_execution_plan(self, steps: List[ExecutionStep], state: InstructionAnalyzerState) -> tuple[bool, List[ValidationError]]:
        """
        실행 계획 검증

        Args:
            steps: 검증할 실행 단계들
            state: 현재 상태

        Returns:
            tuple: (is_valid, validation_errors)
        """
        print("🔍 실행 계획 검증 중...")

        validation_errors = []

        # 1. 기본 검증
        basic_errors = self._validate_basic_plan_structure(steps)
        validation_errors.extend(basic_errors)

        # 2. 의존성 검증
        dependency_errors = self._validate_step_dependencies(steps)
        validation_errors.extend(dependency_errors)

        # 3. 실행 가능성 검증
        feasibility_errors = self._validate_plan_feasibility(steps, state)
        validation_errors.extend(feasibility_errors)

        # 4. 완성도 검증
        completeness_errors = self._validate_plan_completeness(
            steps, state.get("parsed_intent"))
        validation_errors.extend(completeness_errors)

        is_valid = len(validation_errors) == 0

        print(f"✅ 계획 검증 완료 - 유효: {is_valid}, 오류: {len(validation_errors)}개")

        return is_valid, validation_errors

    def _validate_basic_plan_structure(self, steps: List[ExecutionStep]) -> List[ValidationError]:
        """기본 계획 구조 검증"""
        errors = []

        if not steps:
            errors.append(ValidationError(
                error_type="empty_plan",
                message="실행 계획이 비어있습니다",
                suggested_fix="최소 하나의 실행 단계를 추가하세요"
            ))
            return errors

        # 단계 ID 중복 검사
        step_ids = [step.step_id for step in steps]
        if len(step_ids) != len(set(step_ids)):
            errors.append(ValidationError(
                error_type="duplicate_step_ids",
                message="중복된 단계 ID가 있습니다",
                suggested_fix="단계 ID를 고유하게 설정하세요"
            ))

        # 필수 필드 검사
        for step in steps:
            if not step.target_description:
                errors.append(ValidationError(
                    error_type="missing_target_description",
                    message=f"단계 {step.step_id}에 대상 설명이 없습니다",
                    suggested_fix="대상 설명을 추가하세요"
                ))

            if not step.expected_outcome:
                errors.append(ValidationError(
                    error_type="missing_expected_outcome",
                    message=f"단계 {step.step_id}에 예상 결과가 없습니다",
                    suggested_fix="예상 결과를 추가하세요"
                ))

        return errors

    def _validate_step_dependencies(self, steps: List[ExecutionStep]) -> List[ValidationError]:
        """단계 의존성 검증"""
        errors = []

        step_ids = {step.step_id for step in steps}

        for step in steps:
            if step.dependencies:
                for dep_id in step.dependencies:
                    if dep_id not in step_ids:
                        errors.append(ValidationError(
                            error_type="invalid_dependency",
                            message=f"단계 {step.step_id}가 존재하지 않는 단계 {dep_id}에 의존합니다",
                            suggested_fix="의존성을 올바른 단계 ID로 수정하세요"
                        ))
                    elif dep_id >= step.step_id:
                        errors.append(ValidationError(
                            error_type="circular_dependency",
                            message=f"단계 {step.step_id}에 순환 의존성이 있습니다",
                            suggested_fix="의존성 순서를 수정하세요"
                        ))

        return errors

    def _validate_plan_feasibility(self, steps: List[ExecutionStep], state: InstructionAnalyzerState) -> List[ValidationError]:
        """계획 실행 가능성 검증"""
        errors = []

        identified_elements = state.get("identified_elements", [])
        element_selectors = {elem.selector for elem in identified_elements}

        for step in steps:
            # 대상 요소 존재 여부 확인
            if step.target_selector and step.target_selector not in element_selectors:
                errors.append(ValidationError(
                    error_type="target_element_not_found",
                    message=f"단계 {step.step_id}의 대상 요소를 찾을 수 없습니다: {step.target_selector}",
                    suggested_fix="페이지에 존재하는 요소를 대상으로 설정하세요"
                ))

            # 액션 타입별 매개변수 검증
            if step.action_type == ActionType.TYPE and not step.parameters.get("text"):
                errors.append(ValidationError(
                    error_type="missing_text_parameter",
                    message=f"단계 {step.step_id}의 TYPE 액션에 텍스트 매개변수가 없습니다",
                    suggested_fix="입력할 텍스트를 매개변수에 추가하세요"
                ))

            if step.action_type == ActionType.NAVIGATE and not step.parameters.get("url"):
                errors.append(ValidationError(
                    error_type="missing_url_parameter",
                    message=f"단계 {step.step_id}의 NAVIGATE 액션에 URL 매개변수가 없습니다",
                    suggested_fix="이동할 URL을 매개변수에 추가하세요"
                ))

        return errors

    def _validate_plan_completeness(self, steps: List[ExecutionStep], intent: Optional[UserIntent]) -> List[ValidationError]:
        """계획 완성도 검증"""
        errors = []

        if not intent:
            return errors

        # 목표별 필수 액션 검증
        required_actions = {
            "search": [ActionType.TYPE],  # 검색어 입력은 필수
            "login": [ActionType.TYPE],   # 로그인 정보 입력은 필수
            "click": [ActionType.CLICK],  # 클릭은 필수
            "type": [ActionType.TYPE],    # 텍스트 입력은 필수
            "navigate": [ActionType.NAVIGATE, ActionType.CLICK]  # 둘 중 하나는 필수
        }

        if intent.primary_goal in required_actions:
            required = required_actions[intent.primary_goal]
            step_actions = {step.action_type for step in steps}

            if intent.primary_goal == "navigate":
                # NAVIGATE 또는 CLICK 중 하나만 있으면 됨
                if not (ActionType.NAVIGATE in step_actions or ActionType.CLICK in step_actions):
                    errors.append(ValidationError(
                        error_type="incomplete_plan",
                        message=f"'{intent.primary_goal}' 목표에 필요한 액션이 없습니다",
                        suggested_fix="네비게이션 또는 클릭 액션을 추가하세요"
                    ))
            else:
                # 다른 목표들은 모든 필수 액션이 있어야 함
                missing_actions = [
                    action for action in required if action not in step_actions]
                if missing_actions:
                    errors.append(ValidationError(
                        error_type="incomplete_plan",
                        message=f"'{intent.primary_goal}' 목표에 필요한 액션이 누락되었습니다: {missing_actions}",
                        suggested_fix="누락된 액션들을 추가하세요"
                    ))

        return errors

    # === 사용자 검토 인터페이스 메서드 ===

    def _present_plan_for_review(self, state: InstructionAnalyzerState) -> Dict[str, Any]:
        """
        사용자 검토를 위한 계획 표시

        Args:
            state: 현재 상태

        Returns:
            Dict: 검토용 계획 정보
        """
        print("📋 실행 계획 검토 준비 중...")

        execution_steps = state.get("execution_steps", [])
        parsed_intent = state.get("parsed_intent")
        page_analysis = state.get("page_analysis")
        validation_errors = state.get("validation_errors", [])

        # 검토용 계획 정보 구성
        review_info = {
            "summary": self._create_plan_summary(execution_steps, parsed_intent),
            "detailed_steps": self._format_steps_for_review(execution_steps),
            "estimated_duration": self._estimate_execution_duration(execution_steps),
            "risk_assessment": self._assess_execution_risks(execution_steps, validation_errors),
            "alternatives": self._suggest_plan_alternatives(execution_steps, parsed_intent),
            "validation_status": {
                "is_valid": len(validation_errors) == 0,
                "error_count": len(validation_errors),
                "errors": [{"type": err.error_type, "message": err.message, "fix": err.suggested_fix}
                           for err in validation_errors]
            }
        }

        return review_info

    def _create_plan_summary(self, steps: List[ExecutionStep], intent: Optional[UserIntent]) -> Dict[str, Any]:
        """계획 요약 생성"""
        if not steps:
            return {"description": "실행 계획이 없습니다", "step_count": 0, "main_actions": []}

        # 주요 액션 타입 집계
        action_counts = {}
        for step in steps:
            action_type = step.action_type.value
            action_counts[action_type] = action_counts.get(action_type, 0) + 1

        # 요약 설명 생성
        goal = intent.primary_goal if intent else "unknown"
        target_objects = intent.target_objects if intent else []

        if goal == "search" and target_objects:
            description = f"'{' '.join(target_objects)}'를 검색합니다"
        elif goal == "login":
            description = "로그인을 수행합니다"
        elif goal == "navigate" and target_objects:
            description = f"'{' '.join(target_objects)}'로 이동합니다"
        elif goal == "click" and target_objects:
            description = f"'{' '.join(target_objects)}'를 클릭합니다"
        elif goal == "type" and target_objects:
            description = f"'{' '.join(target_objects)}'를 입력합니다"
        else:
            description = f"{len(steps)}단계의 작업을 수행합니다"

        return {
            "description": description,
            "step_count": len(steps),
            "main_actions": list(action_counts.keys()),
            "action_breakdown": action_counts,
            "primary_goal": goal,
            "target_objects": target_objects
        }

    def _format_steps_for_review(self, steps: List[ExecutionStep]) -> List[Dict[str, Any]]:
        """검토용 단계 포맷팅"""
        formatted_steps = []

        for step in steps:
            formatted_step = {
                "step_number": step.step_id,
                "action": step.action_type.value,
                "description": step.target_description,
                "expected_result": step.expected_outcome,
                "details": {
                    "selector": step.target_selector,
                    "parameters": step.parameters or {},
                    "dependencies": step.dependencies or [],
                    "validation": step.validation_criteria,
                    "fallbacks": step.fallback_actions or []
                },
                "risk_level": self._assess_step_risk(step),
                "estimated_time": self._estimate_step_duration(step)
            }

            # 사용자 친화적 설명 추가
            formatted_step["user_friendly_description"] = self._create_user_friendly_description(
                step)

            formatted_steps.append(formatted_step)

        return formatted_steps

    def _create_user_friendly_description(self, step: ExecutionStep) -> str:
        """사용자 친화적 단계 설명 생성"""
        action = step.action_type.value
        target = step.target_description

        if action == "click":
            return f"'{target}'을(를) 클릭합니다"
        elif action == "type":
            text = step.parameters.get(
                "text", "[텍스트]") if step.parameters else "[텍스트]"
            return f"'{target}'에 '{text}'을(를) 입력합니다"
        elif action == "navigate":
            url = step.parameters.get(
                "url", "[URL]") if step.parameters else "[URL]"
            return f"'{url}'로 이동합니다"
        elif action == "wait":
            duration = step.parameters.get(
                "duration", 3) if step.parameters else 3
            return f"{duration}초 동안 대기합니다"
        elif action == "scroll":
            return f"페이지를 스크롤합니다"
        elif action == "verify":
            return f"'{target}' 상태를 확인합니다"
        elif action == "analyze":
            return f"'{target}'을(를) 분석합니다"
        else:
            return f"'{target}'에 대해 {action} 작업을 수행합니다"

    def _assess_step_risk(self, step: ExecutionStep) -> str:
        """단계별 위험도 평가"""
        risk_factors = 0

        # 셀렉터가 없으면 위험도 증가
        if not step.target_selector:
            risk_factors += 2

        # 복잡한 셀렉터는 위험도 증가
        if step.target_selector and len(step.target_selector) > 50:
            risk_factors += 1

        # 매개변수가 필요한데 없으면 위험도 증가
        if step.action_type in [ActionType.TYPE, ActionType.NAVIGATE] and not step.parameters:
            risk_factors += 2

        # 대안 액션이 없으면 위험도 증가
        if not step.fallback_actions:
            risk_factors += 1

        # 검증 기준이 없으면 위험도 증가
        if not step.validation_criteria:
            risk_factors += 1

        if risk_factors >= 4:
            return "high"
        elif risk_factors >= 2:
            return "medium"
        else:
            return "low"

    def _estimate_step_duration(self, step: ExecutionStep) -> float:
        """단계별 예상 실행 시간 (초)"""
        base_times = {
            ActionType.CLICK: 1.0,
            ActionType.TYPE: 2.0,
            ActionType.NAVIGATE: 5.0,
            ActionType.WAIT: 3.0,
            ActionType.SCROLL: 1.5,
            ActionType.VERIFY: 2.0,
            ActionType.ANALYZE: 1.0
        }

        base_time = base_times.get(step.action_type, 2.0)

        # 매개변수에 따른 시간 조정
        if step.parameters:
            if step.action_type == ActionType.TYPE:
                text_length = len(step.parameters.get("text", ""))
                base_time += text_length * 0.1  # 글자당 0.1초 추가
            elif step.action_type == ActionType.WAIT:
                base_time = step.parameters.get("duration", 3.0)

        return base_time

    def _estimate_execution_duration(self, steps: List[ExecutionStep]) -> Dict[str, float]:
        """전체 실행 시간 추정"""
        if not steps:
            return {"total": 0.0, "breakdown": {}}

        total_time = 0.0
        breakdown = {}

        for step in steps:
            step_time = self._estimate_step_duration(step)
            total_time += step_time

            action_type = step.action_type.value
            breakdown[action_type] = breakdown.get(
                action_type, 0.0) + step_time

        # 네트워크 지연 및 페이지 로딩 시간 추가
        network_overhead = len(steps) * 0.5  # 단계당 0.5초 오버헤드
        total_time += network_overhead

        return {
            "total": round(total_time, 1),
            "breakdown": {k: round(v, 1) for k, v in breakdown.items()},
            "network_overhead": round(network_overhead, 1)
        }

    def _assess_execution_risks(self, steps: List[ExecutionStep], validation_errors: List[ValidationError]) -> Dict[str, Any]:
        """실행 위험도 평가"""
        risk_assessment = {
            "overall_risk": "low",
            "risk_factors": [],
            "mitigation_suggestions": []
        }

        # 검증 오류 기반 위험도
        if validation_errors:
            risk_assessment["risk_factors"].append(
                f"검증 오류 {len(validation_errors)}개")
            risk_assessment["overall_risk"] = "high"
            risk_assessment["mitigation_suggestions"].append(
                "검증 오류를 수정한 후 실행하세요")

        # 단계별 위험도 집계
        high_risk_steps = [
            step for step in steps if self._assess_step_risk(step) == "high"]
        medium_risk_steps = [
            step for step in steps if self._assess_step_risk(step) == "medium"]

        if high_risk_steps:
            risk_assessment["risk_factors"].append(
                f"고위험 단계 {len(high_risk_steps)}개")
            risk_assessment["overall_risk"] = "high"
            risk_assessment["mitigation_suggestions"].append(
                "고위험 단계를 수동으로 검토하세요")
        elif medium_risk_steps:
            risk_assessment["risk_factors"].append(
                f"중위험 단계 {len(medium_risk_steps)}개")
            if risk_assessment["overall_risk"] == "low":
                risk_assessment["overall_risk"] = "medium"

        # 복잡도 기반 위험도
        if len(steps) > 10:
            risk_assessment["risk_factors"].append("복잡한 다단계 작업")
            risk_assessment["mitigation_suggestions"].append(
                "단계를 나누어 실행하는 것을 고려하세요")

        # 의존성 복잡도
        complex_dependencies = [
            step for step in steps if len(step.dependencies) > 2]
        if complex_dependencies:
            risk_assessment["risk_factors"].append("복잡한 단계 의존성")
            risk_assessment["mitigation_suggestions"].append(
                "의존성을 단순화하는 것을 고려하세요")

        return risk_assessment

    def _suggest_plan_alternatives(self, steps: List[ExecutionStep], intent: Optional[UserIntent]) -> List[Dict[str, Any]]:
        """대안 계획 제안"""
        alternatives = []

        if not steps or not intent:
            return alternatives

        # 1. 단순화된 계획
        if len(steps) > 3:
            alternatives.append({
                "type": "simplified",
                "title": "단순화된 계획",
                "description": "핵심 단계만으로 구성된 간소화된 계획",
                "benefits": ["실행 시간 단축", "오류 가능성 감소"],
                "trade_offs": ["일부 검증 단계 생략"]
            })

        # 2. 수동 확인 포함 계획
        alternatives.append({
            "type": "manual_verification",
            "title": "수동 확인 포함 계획",
            "description": "각 주요 단계 후 사용자 확인을 포함하는 계획",
            "benefits": ["높은 정확도", "오류 즉시 감지"],
            "trade_offs": ["실행 시간 증가", "사용자 개입 필요"]
        })

        # 3. 단계별 실행 계획
        if len(steps) > 5:
            alternatives.append({
                "type": "step_by_step",
                "title": "단계별 실행 계획",
                "description": "한 번에 하나씩 단계를 실행하는 계획",
                "benefits": ["세밀한 제어", "문제 발생시 즉시 중단"],
                "trade_offs": ["전체 실행 시간 증가"]
            })

        # 4. 목표별 특화 대안
        if intent.primary_goal == "search":
            alternatives.append({
                "type": "direct_search",
                "title": "직접 검색",
                "description": "URL 파라미터를 사용한 직접 검색",
                "benefits": ["빠른 실행", "UI 의존성 없음"],
                "trade_offs": ["사이트별 URL 구조 필요"]
            })

        return alternatives

    def _generate_review_questions(self, review_info: Dict[str, Any]) -> List[UserQuestion]:
        """검토 기반 질문 생성"""
        questions = []

        # 기본 승인 질문
        plan_summary = review_info.get("summary", {})
        step_count = plan_summary.get("step_count", 0)
        estimated_time = review_info.get(
            "estimated_duration", {}).get("total", 0)

        questions.append(UserQuestion(
            question_id="review_approval",
            question_text=f"{step_count}단계 실행 계획 (예상 시간: {estimated_time}초)을 검토했습니다. 어떻게 진행하시겠습니까?",
            question_type="choice",
            options=[
                "승인하고 실행",
                "수정 후 실행",
                "대안 계획 선택",
                "단계별 실행",
                "취소"
            ],
            timeout_seconds=60
        ))

        # 위험도가 높은 경우 추가 질문
        risk_info = review_info.get("risk_assessment", {})
        if risk_info.get("overall_risk") == "high":
            questions.append(UserQuestion(
                question_id="high_risk_confirmation",
                question_text="이 계획은 높은 위험도를 가지고 있습니다. 정말 실행하시겠습니까?",
                question_type="confirmation",
                options=["예, 실행합니다", "아니오, 수정이 필요합니다"],
                timeout_seconds=30
            ))

        # 검증 오류가 있는 경우 질문
        validation_status = review_info.get("validation_status", {})
        if not validation_status.get("is_valid"):
            error_count = validation_status.get("error_count", 0)
            questions.append(UserQuestion(
                question_id="validation_error_handling",
                question_text=f"{error_count}개의 검증 오류가 있습니다. 어떻게 처리하시겠습니까?",
                question_type="choice",
                options=[
                    "오류 무시하고 실행",
                    "오류 수정 후 실행",
                    "계획 재생성",
                    "취소"
                ],
                timeout_seconds=45
            ))

        # 대안이 있는 경우 질문
        alternatives = review_info.get("alternatives", [])
        if alternatives:
            alt_options = [alt["title"] for alt in alternatives[:3]]  # 최대 3개
            alt_options.append("현재 계획 유지")

            questions.append(UserQuestion(
                question_id="alternative_selection",
                question_text="다음 대안 계획들을 고려해보세요:",
                question_type="choice",
                options=alt_options,
                timeout_seconds=45
            ))

        return questions

    def _display_review_summary(self, review_info: Dict[str, Any]):
        """검토 정보 요약 출력"""
        print("\n" + "="*60)
        print("📋 실행 계획 검토")
        print("="*60)

        # 계획 요약
        summary = review_info.get("summary", {})
        print(f"📝 작업 설명: {summary.get('description', 'N/A')}")
        print(f"📊 총 단계: {summary.get('step_count', 0)}단계")

        # 예상 시간
        duration = review_info.get("estimated_duration", {})
        print(f"⏱️  예상 시간: {duration.get('total', 0)}초")

        # 위험도
        risk = review_info.get("risk_assessment", {})
        risk_level = risk.get("overall_risk", "unknown")
        risk_emoji = {"low": "🟢", "medium": "🟡",
                      "high": "🔴"}.get(risk_level, "⚪")
        print(f"{risk_emoji} 위험도: {risk_level}")

        # 검증 상태
        validation = review_info.get("validation_status", {})
        if validation.get("is_valid"):
            print("✅ 검증: 통과")
        else:
            error_count = validation.get("error_count", 0)
            print(f"❌ 검증: {error_count}개 오류")

        # 단계별 상세 정보
        steps = review_info.get("detailed_steps", [])
        if steps:
            print(f"\n📋 단계별 계획:")
            for step in steps[:5]:  # 처음 5단계만 표시
                risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(
                    step.get("risk_level", "low"), "⚪")
                print(
                    f"  {step['step_number']}. {step['user_friendly_description']} {risk_emoji}")

            if len(steps) > 5:
                print(f"  ... 및 {len(steps) - 5}개 추가 단계")

        print("="*60)

    def _simulate_review_responses(self, questions: List[UserQuestion], review_info: Dict[str, Any]) -> Dict[str, str]:
        """검토 질문에 대한 시뮬레이션 응답"""
        responses = {}

        for question in questions:
            print(f"\n❓ {question.question_text}")

            if question.question_id == "review_approval":
                # 위험도에 따른 응답 결정
                risk_level = review_info.get(
                    "risk_assessment", {}).get("overall_risk", "low")
                validation_valid = review_info.get(
                    "validation_status", {}).get("is_valid", True)

                if risk_level == "high" or not validation_valid:
                    responses[question.question_id] = "수정 후 실행"
                    print("💭 자동 응답: 수정 후 실행 (위험도/검증 문제)")
                else:
                    responses[question.question_id] = "승인하고 실행"
                    print("💭 자동 응답: 승인하고 실행")

            elif question.question_id == "high_risk_confirmation":
                responses[question.question_id] = "아니오, 수정이 필요합니다"
                print("💭 자동 응답: 수정 필요 (고위험)")

            elif question.question_id == "validation_error_handling":
                responses[question.question_id] = "오류 수정 후 실행"
                print("💭 자동 응답: 오류 수정 후 실행")

            elif question.question_id == "alternative_selection":
                if question.options:
                    # "현재 계획 유지"
                    responses[question.question_id] = question.options[-1]
                    print(f"💭 자동 응답: {question.options[-1]}")

            else:
                # 기본 응답
                if question.question_type == "confirmation":
                    responses[question.question_id] = "예"
                elif question.options:
                    responses[question.question_id] = question.options[0]
                else:
                    responses[question.question_id] = "자동 응답"
                print(f"💭 자동 응답: {responses[question.question_id]}")

        return responses

    def _process_review_responses(self, state: InstructionAnalyzerState, responses: Dict[str, str]) -> InstructionAnalyzerState:
        """검토 응답 처리"""
        print(f"\n📝 검토 응답 처리 중... ({len(responses)}개 응답)")

        # 응답을 상태에 저장
        state["user_responses"].update(responses)

        # 주요 승인 응답 처리
        approval_response = responses.get("review_approval", "")

        if "승인하고 실행" in approval_response:
            state["is_approved"] = True
            state["final_plan"] = state["execution_steps"]
            state["plan_status"] = PlanStatus.APPROVED
            state["processing_stage"] = "completed"
            print("✅ 계획 승인됨 - 실행 준비 완료")

        elif "수정 후 실행" in approval_response:
            state["is_approved"] = False
            state["plan_status"] = PlanStatus.REJECTED
            state["missing_info"].append("계획 수정 요청")
            print("🔄 계획 수정 요청 - 재생성 필요")

        elif "대안 계획 선택" in approval_response:
            # 대안 선택 처리
            alt_response = responses.get("alternative_selection", "")
            if "현재 계획 유지" not in alt_response:
                state["plan_status"] = PlanStatus.REJECTED
                state["missing_info"].append(f"대안 계획 요청: {alt_response}")
                print(f"🔀 대안 계획 선택: {alt_response}")
            else:
                state["is_approved"] = True
                state["final_plan"] = state["execution_steps"]
                state["plan_status"] = PlanStatus.APPROVED
                state["processing_stage"] = "completed"
                print("✅ 현재 계획 유지로 승인")

        elif "단계별 실행" in approval_response:
            state["is_approved"] = True
            state["final_plan"] = state["execution_steps"]
            state["plan_status"] = PlanStatus.APPROVED
            state["processing_stage"] = "completed"
            # 단계별 실행 플래그 추가
            state["step_by_step_execution"] = True
            print("✅ 단계별 실행으로 승인")

        elif "취소" in approval_response:
            state["is_approved"] = False
            state["plan_status"] = PlanStatus.REJECTED
            state["processing_stage"] = "failed"
            print("❌ 사용자가 계획을 취소함")

        # 고위험 확인 응답 처리
        high_risk_response = responses.get("high_risk_confirmation", "")
        if "아니오" in high_risk_response:
            state["is_approved"] = False
            state["plan_status"] = PlanStatus.REJECTED
            state["missing_info"].append("고위험으로 인한 계획 거부")
            print("⚠️ 고위험으로 인한 계획 거부")

        # 검증 오류 처리 응답
        validation_response = responses.get("validation_error_handling", "")
        if "오류 수정 후 실행" in validation_response:
            state["plan_status"] = PlanStatus.REJECTED
            state["missing_info"].append("검증 오류 수정 요청")
            print("🔧 검증 오류 수정 요청")
        elif "오류 무시하고 실행" in validation_response:
            state["is_approved"] = True
            state["final_plan"] = state["execution_steps"]
            state["plan_status"] = PlanStatus.APPROVED
            state["processing_stage"] = "completed"
            print("⚠️ 검증 오류 무시하고 실행 승인")

        return state

    # === 계획 수정 및 재생성 메서드 ===

    def _modify_execution_plan(self, state: InstructionAnalyzerState, modification_requests: List[str]) -> List[ExecutionStep]:
        """
        실행 계획 수정

        Args:
            state: 현재 상태
            modification_requests: 수정 요청 목록

        Returns:
            List[ExecutionStep]: 수정된 실행 단계들
        """
        print(f"🔧 실행 계획 수정 중... ({len(modification_requests)}개 요청)")

        current_steps = state.get("execution_steps", [])
        if not current_steps:
            print("❌ 수정할 계획이 없습니다")
            return []

        modified_steps = current_steps.copy()

        for request in modification_requests:
            print(f"  처리 중: {request}")

            if "위험도" in request or "안전" in request:
                modified_steps = self._reduce_plan_risks(modified_steps)
            elif "단순화" in request or "간소화" in request:
                modified_steps = self._simplify_plan(modified_steps)
            elif "검증" in request or "확인" in request:
                modified_steps = self._add_verification_steps(modified_steps)
            elif "속도" in request or "빠르게" in request:
                modified_steps = self._optimize_for_speed(modified_steps)
            elif "단계별" in request:
                modified_steps = self._add_manual_confirmations(modified_steps)
            elif "오류" in request:
                modified_steps = self._fix_validation_errors(
                    modified_steps, state)
            else:
                # 일반적인 수정 요청
                modified_steps = self._apply_generic_modifications(
                    modified_steps, request)

        # 수정 후 재최적화
        parsed_intent = state.get("parsed_intent")
        if parsed_intent:
            modified_steps = self._optimize_execution_plan(
                modified_steps, parsed_intent)

        print(f"✅ 계획 수정 완료 - {len(current_steps)}단계 → {len(modified_steps)}단계")
        return modified_steps

    def _reduce_plan_risks(self, steps: List[ExecutionStep]) -> List[ExecutionStep]:
        """계획 위험도 감소"""
        print("    🛡️ 위험도 감소 적용")

        safer_steps = []
        for step in steps:
            # 고위험 단계에 대안 추가
            if self._assess_step_risk(step) == "high":
                # 더 안전한 셀렉터 사용
                if step.target_selector and not step.target_selector.startswith("#"):
                    # ID 기반 셀렉터가 아니면 더 구체적으로 만들기
                    step.validation_criteria = f"{step.validation_criteria} (안전 모드)"

                # 대안 액션 추가
                if not step.fallback_actions:
                    step.fallback_actions = [
                        "manual_intervention", "skip_step"]
                else:
                    step.fallback_actions.append("manual_intervention")

            # 대기 시간 추가
            if step.action_type in [ActionType.CLICK, ActionType.TYPE]:
                # 다음 단계 전에 짧은 대기 추가
                safer_steps.append(step)
                if step != steps[-1]:  # 마지막 단계가 아니면
                    wait_step = ExecutionStep(
                        step_id=step.step_id + 0.5,  # 임시 ID
                        action_type=ActionType.WAIT,
                        target_description="안전 대기",
                        parameters={"duration": 1},
                        expected_outcome="안전한 실행을 위한 대기 완료"
                    )
                    safer_steps.append(wait_step)
            else:
                safer_steps.append(step)

        return safer_steps

    def _simplify_plan(self, steps: List[ExecutionStep]) -> List[ExecutionStep]:
        """계획 단순화"""
        print("    ⚡ 계획 단순화 적용")

        # 불필요한 단계 제거
        essential_steps = []
        for step in steps:
            # ANALYZE, VERIFY 단계 제거
            if step.action_type in [ActionType.ANALYZE, ActionType.VERIFY]:
                continue

            # 과도한 WAIT 단계 제거
            if step.action_type == ActionType.WAIT:
                duration = step.parameters.get(
                    "duration", 0) if step.parameters else 0
                if duration > 2:
                    continue

            essential_steps.append(step)

        # 연속된 동일 타입 단계 병합
        merged_steps = []
        i = 0
        while i < len(essential_steps):
            current_step = essential_steps[i]

            # TYPE 단계들 병합
            if (current_step.action_type == ActionType.TYPE and
                i + 1 < len(essential_steps) and
                essential_steps[i + 1].action_type == ActionType.TYPE and
                    current_step.target_selector == essential_steps[i + 1].target_selector):

                # 텍스트 병합
                text1 = current_step.parameters.get(
                    "text", "") if current_step.parameters else ""
                text2 = essential_steps[i + 1].parameters.get(
                    "text", "") if essential_steps[i + 1].parameters else ""

                merged_step = ExecutionStep(
                    step_id=current_step.step_id,
                    action_type=ActionType.TYPE,
                    target_description=current_step.target_description,
                    target_selector=current_step.target_selector,
                    parameters={"text": f"{text1} {text2}".strip()},
                    expected_outcome=f"{text1} {text2}가 입력됨",
                    validation_criteria=current_step.validation_criteria
                )
                merged_steps.append(merged_step)
                i += 2  # 두 단계 건너뜀
            else:
                merged_steps.append(current_step)
                i += 1

        return merged_steps

    def _add_verification_steps(self, steps: List[ExecutionStep]) -> List[ExecutionStep]:
        """검증 단계 추가"""
        print("    ✅ 검증 단계 추가")

        enhanced_steps = []
        for i, step in enumerate(steps):
            enhanced_steps.append(step)

            # 중요한 단계 후에 검증 추가
            if step.action_type in [ActionType.CLICK, ActionType.TYPE, ActionType.NAVIGATE]:
                verify_step = ExecutionStep(
                    step_id=step.step_id + 0.1,  # 임시 ID
                    action_type=ActionType.VERIFY,
                    target_description=f"{step.target_description} 결과 확인",
                    target_selector=step.target_selector,
                    expected_outcome=f"{step.expected_outcome} 확인됨",
                    validation_criteria="단계 실행 결과가 예상과 일치함",
                    dependencies=[step.step_id]
                )
                enhanced_steps.append(verify_step)

        return enhanced_steps

    def _optimize_for_speed(self, steps: List[ExecutionStep]) -> List[ExecutionStep]:
        """속도 최적화"""
        print("    🚀 속도 최적화 적용")

        speed_optimized = []
        for step in steps:
            # WAIT 단계 최소화
            if step.action_type == ActionType.WAIT:
                duration = step.parameters.get(
                    "duration", 3) if step.parameters else 3
                if duration > 1:
                    step.parameters["duration"] = 1
                    step.expected_outcome = "최소 대기 완료"

            # 불필요한 검증 단계 제거
            elif step.action_type == ActionType.VERIFY:
                continue

            # 병렬 실행 가능한 단계 표시
            elif step.action_type in [ActionType.ANALYZE]:
                step.parameters = step.parameters or {}
                step.parameters["async"] = True

            speed_optimized.append(step)

        return speed_optimized

    def _add_manual_confirmations(self, steps: List[ExecutionStep]) -> List[ExecutionStep]:
        """수동 확인 단계 추가"""
        print("    👤 수동 확인 단계 추가")

        confirmed_steps = []
        for i, step in enumerate(steps):
            confirmed_steps.append(step)

            # 중요한 단계 후에 수동 확인 추가
            if step.action_type in [ActionType.CLICK, ActionType.NAVIGATE] or i == len(steps) - 1:
                confirm_step = ExecutionStep(
                    step_id=step.step_id + 0.2,  # 임시 ID
                    action_type=ActionType.VERIFY,
                    target_description="사용자 확인 대기",
                    expected_outcome="사용자가 다음 단계 진행을 승인함",
                    validation_criteria="사용자 승인 확인",
                    parameters={"manual_confirmation": True}
                )
                confirmed_steps.append(confirm_step)

        return confirmed_steps

    def _fix_validation_errors(self, steps: List[ExecutionStep], state: InstructionAnalyzerState) -> List[ExecutionStep]:
        """검증 오류 수정"""
        print("    🔧 검증 오류 수정")

        validation_errors = state.get("validation_errors", [])
        identified_elements = state.get("identified_elements", [])

        fixed_steps = []
        for step in steps:
            fixed_step = step

            # 대상 요소를 찾을 수 없는 경우
            if step.target_selector:
                element_exists = any(
                    elem.selector == step.target_selector for elem in identified_elements)
                if not element_exists:
                    # 유사한 요소 찾기
                    similar_elements = [elem for elem in identified_elements
                                        if elem.element_type == step.action_type.value or
                                        step.target_description.lower() in elem.description.lower()]

                    if similar_elements:
                        fixed_step.target_selector = similar_elements[0].selector
                        fixed_step.target_description = f"{step.target_description} (수정됨)"
                        print(
                            f"      셀렉터 수정: {step.target_selector} → {fixed_step.target_selector}")

            # 매개변수 누락 수정
            if step.action_type == ActionType.TYPE and not step.parameters.get("text"):
                parsed_intent = state.get("parsed_intent")
                if parsed_intent and parsed_intent.target_objects:
                    fixed_step.parameters = {
                        "text": " ".join(parsed_intent.target_objects)}
                    print(
                        f"      텍스트 매개변수 추가: {fixed_step.parameters['text']}")

            fixed_steps.append(fixed_step)

        return fixed_steps

    def _apply_generic_modifications(self, steps: List[ExecutionStep], request: str) -> List[ExecutionStep]:
        """일반적인 수정 요청 적용"""
        print(f"    🔄 일반 수정 적용: {request}")

        # 요청에 따른 기본적인 수정
        modified_steps = steps.copy()

        # 특정 단계 제거 요청
        if "제거" in request or "삭제" in request:
            # 마지막 단계 제거
            if modified_steps:
                removed_step = modified_steps.pop()
                print(f"      단계 제거: {removed_step.target_description}")

        # 단계 추가 요청
        elif "추가" in request:
            if modified_steps:
                last_step = modified_steps[-1]
                additional_step = ExecutionStep(
                    step_id=last_step.step_id + 1,
                    action_type=ActionType.WAIT,
                    target_description="추가 대기",
                    parameters={"duration": 2},
                    expected_outcome="추가 대기 완료"
                )
                modified_steps.append(additional_step)
                print(f"      단계 추가: {additional_step.target_description}")

        return modified_steps

    def _regenerate_execution_plan(self, state: InstructionAnalyzerState, regeneration_options: Dict[str, Any]) -> List[ExecutionStep]:
        """
        실행 계획 재생성

        Args:
            state: 현재 상태
            regeneration_options: 재생성 옵션

        Returns:
            List[ExecutionStep]: 재생성된 실행 단계들
        """
        print("🔄 실행 계획 재생성 중...")

        # 재생성 옵션 적용
        strategy = regeneration_options.get("strategy", "default")
        focus = regeneration_options.get("focus", "accuracy")
        complexity = regeneration_options.get("complexity", "normal")

        print(f"  전략: {strategy}, 초점: {focus}, 복잡도: {complexity}")

        # 기존 정보 활용
        parsed_intent = state.get("parsed_intent")
        identified_elements = state.get("identified_elements", [])
        action_parameters = state.get("action_parameters", {})

        if not parsed_intent:
            print("❌ 의도 정보가 없어 재생성 불가")
            return []

        # 전략별 재생성
        if strategy == "simplified":
            new_steps = self._generate_simplified_plan(
                parsed_intent, identified_elements, action_parameters)
        elif strategy == "detailed":
            new_steps = self._generate_detailed_plan(
                parsed_intent, identified_elements, action_parameters)
        elif strategy == "safe":
            new_steps = self._generate_safe_plan(
                parsed_intent, identified_elements, action_parameters)
        elif strategy == "fast":
            new_steps = self._generate_fast_plan(
                parsed_intent, identified_elements, action_parameters)
        else:
            # 기본 재생성
            new_steps = self._generate_execution_plan(state)

        # 초점별 후처리
        if focus == "accuracy":
            new_steps = self._add_verification_steps(new_steps)
        elif focus == "speed":
            new_steps = self._optimize_for_speed(new_steps)
        elif focus == "safety":
            new_steps = self._reduce_plan_risks(new_steps)

        # 복잡도 조정
        if complexity == "simple":
            new_steps = self._simplify_plan(new_steps)
        elif complexity == "detailed":
            new_steps = self._add_verification_steps(new_steps)

        # 최종 최적화
        new_steps = self._optimize_execution_plan(new_steps, parsed_intent)

        print(f"✅ 계획 재생성 완료 - {len(new_steps)}단계")
        return new_steps

    def _generate_simplified_plan(self, intent: UserIntent, elements: List[PageElement], parameters: Dict[str, Any]) -> List[ExecutionStep]:
        """단순화된 계획 생성"""
        if intent.primary_goal == "search":
            # 최대 3단계
            return self._generate_search_plan(intent, elements, parameters, None)[:3]
        elif intent.primary_goal == "click":
            return self._generate_click_plan(intent, elements, None)
        else:
            # 최대 2단계
            return self._generate_generic_plan(intent, elements, parameters)[:2]

    def _generate_detailed_plan(self, intent: UserIntent, elements: List[PageElement], parameters: Dict[str, Any]) -> List[ExecutionStep]:
        """상세한 계획 생성"""
        basic_steps = self._generate_execution_plan(
            {"parsed_intent": intent, "identified_elements": elements, "action_parameters": parameters})
        return self._add_verification_steps(basic_steps)

    def _generate_safe_plan(self, intent: UserIntent, elements: List[PageElement], parameters: Dict[str, Any]) -> List[ExecutionStep]:
        """안전한 계획 생성"""
        basic_steps = self._generate_execution_plan(
            {"parsed_intent": intent, "identified_elements": elements, "action_parameters": parameters})
        return self._reduce_plan_risks(basic_steps)

    def _generate_fast_plan(self, intent: UserIntent, elements: List[PageElement], parameters: Dict[str, Any]) -> List[ExecutionStep]:
        """빠른 계획 생성"""
        basic_steps = self._generate_execution_plan(
            {"parsed_intent": intent, "identified_elements": elements, "action_parameters": parameters})
        return self._optimize_for_speed(basic_steps)

    # === 포괄적인 오류 처리 메서드 ===

    def _handle_workflow_error(self, error: Exception, state: InstructionAnalyzerState, node_name: str) -> InstructionAnalyzerState:
        """
        워크플로우 오류 처리

        Args:
            error: 발생한 예외
            state: 현재 상태
            node_name: 오류가 발생한 노드명

        Returns:
            InstructionAnalyzerState: 오류 처리된 상태
        """
        print(f"🚨 워크플로우 오류 처리 중 - 노드: {node_name}")
        print(f"   오류 타입: {type(error).__name__}")
        print(f"   오류 메시지: {str(error)}")

        # 오류 분류 및 처리
        error_type = self._classify_error(error, node_name)
        recovery_strategy = self._determine_recovery_strategy(
            error_type, state)

        # 오류 정보를 상태에 기록
        error_info = ValidationError(
            error_type=error_type,
            message=f"{node_name}에서 {type(error).__name__}: {str(error)}",
            suggested_fix=recovery_strategy.get(
                "suggestion", "시스템 관리자에게 문의하세요"),
            requires_user_input=recovery_strategy.get(
                "requires_user_input", False)
        )

        state["validation_errors"].append(error_info)

        # 복구 전략 실행
        recovered_state = self._execute_recovery_strategy(
            recovery_strategy, state, error)

        return recovered_state

    def _classify_error(self, error: Exception, node_name: str) -> str:
        """오류 분류"""
        error_type_name = type(error).__name__
        error_message = str(error).lower()

        # LLM 관련 오류
        if "api" in error_message or "rate limit" in error_message or "quota" in error_message:
            return "llm_api_error"
        elif "timeout" in error_message or "connection" in error_message:
            return "network_timeout"
        elif "authentication" in error_message or "unauthorized" in error_message:
            return "authentication_error"

        # 페이지 분석 오류
        elif node_name == "analyze_page":
            if "html" in error_message or "parsing" in error_message:
                return "html_parsing_error"
            elif "selector" in error_message:
                return "selector_generation_error"
            else:
                return "page_analysis_error"

        # 지시사항 분석 오류
        elif node_name == "analyze_instruction":
            if "json" in error_message:
                return "instruction_parsing_error"
            elif "confidence" in error_message:
                return "low_confidence_error"
            else:
                return "instruction_analysis_error"

        # 계획 생성 오류
        elif node_name == "generate_plan":
            if "validation" in error_message:
                return "plan_validation_error"
            elif "optimization" in error_message:
                return "plan_optimization_error"
            else:
                return "plan_generation_error"

        # 사용자 상호작용 오류
        elif node_name == "human_interaction":
            if "timeout" in error_message:
                return "user_timeout_error"
            elif "input" in error_message:
                return "user_input_error"
            else:
                return "human_interaction_error"

        # 일반적인 Python 오류들
        elif error_type_name == "KeyError":
            return "missing_data_error"
        elif error_type_name == "TypeError":
            return "type_mismatch_error"
        elif error_type_name == "ValueError":
            return "invalid_value_error"
        elif error_type_name == "AttributeError":
            return "attribute_missing_error"
        elif error_type_name == "IndexError":
            return "index_out_of_range_error"
        elif error_type_name == "MemoryError":
            return "memory_exhaustion_error"

        # 기타 오류
        else:
            return "unknown_error"

    def _determine_recovery_strategy(self, error_type: str, state: InstructionAnalyzerState) -> Dict[str, Any]:
        """복구 전략 결정"""
        strategies = {
            # LLM 관련 오류
            "llm_api_error": {
                "action": "retry_with_fallback",
                "max_retries": 3,
                "fallback_model": "gemini-1.5-flash",
                "suggestion": "API 오류로 인해 대체 모델을 사용합니다",
                "requires_user_input": False
            },
            "network_timeout": {
                "action": "retry_with_delay",
                "max_retries": 2,
                "delay": 5,
                "suggestion": "네트워크 연결을 확인하고 재시도합니다",
                "requires_user_input": False
            },
            "authentication_error": {
                "action": "request_credentials",
                "suggestion": "API 인증 정보를 확인해주세요",
                "requires_user_input": True
            },

            # 페이지 분석 오류
            "html_parsing_error": {
                "action": "use_alternative_parser",
                "suggestion": "대체 HTML 파서를 사용합니다",
                "requires_user_input": False
            },
            "selector_generation_error": {
                "action": "use_basic_selectors",
                "suggestion": "기본 셀렉터를 사용합니다",
                "requires_user_input": False
            },
            "page_analysis_error": {
                "action": "skip_advanced_analysis",
                "suggestion": "고급 분석을 건너뛰고 기본 분석만 수행합니다",
                "requires_user_input": False
            },

            # 지시사항 분석 오류
            "instruction_parsing_error": {
                "action": "use_fallback_parsing",
                "suggestion": "키워드 기반 분석을 사용합니다",
                "requires_user_input": False
            },
            "low_confidence_error": {
                "action": "request_clarification",
                "suggestion": "지시사항을 더 구체적으로 설명해주세요",
                "requires_user_input": True
            },
            "instruction_analysis_error": {
                "action": "use_simple_analysis",
                "suggestion": "단순화된 분석을 사용합니다",
                "requires_user_input": False
            },

            # 계획 생성 오류
            "plan_generation_error": {
                "action": "generate_basic_plan",
                "suggestion": "기본 계획을 생성합니다",
                "requires_user_input": False
            },
            "plan_validation_error": {
                "action": "skip_validation",
                "suggestion": "검증을 건너뛰고 계획을 생성합니다",
                "requires_user_input": False
            },
            "plan_optimization_error": {
                "action": "skip_optimization",
                "suggestion": "최적화를 건너뛰고 기본 계획을 사용합니다",
                "requires_user_input": False
            },

            # 사용자 상호작용 오류
            "user_timeout_error": {
                "action": "use_default_response",
                "suggestion": "기본 응답을 사용하여 진행합니다",
                "requires_user_input": False
            },
            "user_input_error": {
                "action": "request_valid_input",
                "suggestion": "올바른 형식으로 다시 입력해주세요",
                "requires_user_input": True
            },
            "human_interaction_error": {
                "action": "skip_interaction",
                "suggestion": "사용자 상호작용을 건너뛰고 자동으로 진행합니다",
                "requires_user_input": False
            },

            # 일반적인 오류
            "missing_data_error": {
                "action": "use_default_data",
                "suggestion": "기본값을 사용하여 진행합니다",
                "requires_user_input": False
            },
            "type_mismatch_error": {
                "action": "convert_type",
                "suggestion": "데이터 타입을 변환하여 진행합니다",
                "requires_user_input": False
            },
            "invalid_value_error": {
                "action": "use_safe_value",
                "suggestion": "안전한 기본값을 사용합니다",
                "requires_user_input": False
            },
            "memory_exhaustion_error": {
                "action": "reduce_complexity",
                "suggestion": "처리 복잡도를 줄여 진행합니다",
                "requires_user_input": False
            },

            # 기본 전략
            "unknown_error": {
                "action": "graceful_degradation",
                "suggestion": "기본 기능으로 제한하여 진행합니다",
                "requires_user_input": False
            }
        }

        return strategies.get(error_type, strategies["unknown_error"])

    def _execute_recovery_strategy(self, strategy: Dict[str, Any], state: InstructionAnalyzerState, error: Exception) -> InstructionAnalyzerState:
        """복구 전략 실행"""
        action = strategy.get("action", "graceful_degradation")

        print(f"🔧 복구 전략 실행: {action}")

        try:
            if action == "retry_with_fallback":
                state = self._retry_with_fallback(state, strategy)
            elif action == "retry_with_delay":
                state = self._retry_with_delay(state, strategy)
            elif action == "use_alternative_parser":
                state = self._use_alternative_parser(state)
            elif action == "use_basic_selectors":
                state = self._use_basic_selectors(state)
            elif action == "use_fallback_parsing":
                state = self._use_fallback_parsing(state)
            elif action == "generate_basic_plan":
                state = self._generate_basic_plan(state)
            elif action == "skip_advanced_analysis":
                state = self._skip_advanced_analysis(state)
            elif action == "skip_validation":
                state = self._skip_validation(state)
            elif action == "skip_optimization":
                state = self._skip_optimization(state)
            elif action == "use_default_response":
                state = self._use_default_response(state)
            elif action == "use_default_data":
                state = self._use_default_data(state)
            elif action == "reduce_complexity":
                state = self._reduce_complexity(state)
            elif action == "graceful_degradation":
                state = self._graceful_degradation(state)
            else:
                print(f"⚠️ 알 수 없는 복구 액션: {action}")
                state = self._graceful_degradation(state)

            print("✅ 복구 전략 실행 완료")

        except Exception as recovery_error:
            print(f"❌ 복구 전략 실행 실패: {recovery_error}")
            state = self._graceful_degradation(state)

        return state

    def _retry_with_fallback(self, state: InstructionAnalyzerState, strategy: Dict[str, Any]) -> InstructionAnalyzerState:
        """대체 모델로 재시도"""
        print("🔄 대체 모델로 재시도")

        # 현재 모델을 대체 모델로 변경
        fallback_model = strategy.get("fallback_model", "gemini-1.5-flash")
        try:
            self.llm = ChatGoogleGenerativeAI(
                model=fallback_model, temperature=0.1)
            print(f"  모델 변경: {fallback_model}")
        except Exception as e:
            print(f"  모델 변경 실패: {e}")

        return state

    def _retry_with_delay(self, state: InstructionAnalyzerState, strategy: Dict[str, Any]) -> InstructionAnalyzerState:
        """지연 후 재시도"""
        import time
        delay = strategy.get("delay", 3)
        print(f"⏳ {delay}초 대기 후 재시도")
        time.sleep(delay)
        return state

    def _use_alternative_parser(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """대체 HTML 파서 사용"""
        print("🔄 대체 HTML 파서 사용")

        # 기본 페이지 컨텍스트 생성
        state["page_analysis"] = PageContext(
            url=state.get("current_url", ""),
            title="파싱 오류로 인한 기본 제목",
            page_type="unknown"
        )

        return state

    def _use_basic_selectors(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """기본 셀렉터 사용"""
        print("🔄 기본 셀렉터 사용")

        # 기본적인 요소들 생성
        basic_elements = [
            PageElement(
                element_type="input",
                selector="input",
                description="기본 입력 요소",
                is_interactive=True
            ),
            PageElement(
                element_type="button",
                selector="button",
                description="기본 버튼 요소",
                is_interactive=True
            )
        ]

        state["identified_elements"] = basic_elements
        return state

    def _use_fallback_parsing(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """폴백 파싱 사용"""
        print("🔄 키워드 기반 폴백 파싱 사용")

        user_instruction = state.get("user_instruction", "")
        fallback_intent = self._create_fallback_intent(user_instruction)
        state["parsed_intent"] = fallback_intent

        return state

    def _generate_basic_plan(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """기본 계획 생성"""
        print("🔄 기본 계획 생성")

        parsed_intent = state.get("parsed_intent")
        if not parsed_intent:
            # 매우 기본적인 의도 생성
            parsed_intent = UserIntent(
                primary_goal="click",
                target_objects=["버튼"],
                confidence_score=0.3
            )

        # 단순한 기본 계획
        basic_steps = [
            ExecutionStep(
                step_id=1,
                action_type=ActionType.CLICK,
                target_description="첫 번째 클릭 가능한 요소",
                expected_outcome="요소가 클릭됨"
            )
        ]

        state["execution_steps"] = basic_steps
        return state

    def _skip_advanced_analysis(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """고급 분석 건너뛰기"""
        print("⏭️ 고급 분석 건너뛰기")

        # 기본 페이지 분석만 수행
        state["page_analysis"] = PageContext(
            url=state.get("current_url", ""),
            title="기본 분석",
            page_type="unknown"
        )

        return state

    def _skip_validation(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """검증 건너뛰기"""
        print("⏭️ 검증 건너뛰기")

        # 검증 오류 무시
        state["validation_errors"] = []
        return state

    def _skip_optimization(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """최적화 건너뛰기"""
        print("⏭️ 최적화 건너뛰기")

        # 기본 계획 그대로 사용
        return state

    def _use_default_response(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """기본 응답 사용"""
        print("🔄 기본 응답 사용")

        # 자동 승인 처리
        state["is_approved"] = True
        state["final_plan"] = state.get("execution_steps", [])
        state["plan_status"] = PlanStatus.APPROVED

        return state

    def _use_default_data(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """기본 데이터 사용"""
        print("🔄 기본 데이터 사용")

        # 누락된 필수 데이터 채우기
        if not state.get("parsed_intent"):
            state["parsed_intent"] = UserIntent(
                primary_goal="unknown",
                confidence_score=0.1
            )

        if not state.get("page_analysis"):
            state["page_analysis"] = PageContext(
                url=state.get("current_url", ""),
                title="기본 페이지"
            )

        return state

    def _reduce_complexity(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """복잡도 감소"""
        print("📉 처리 복잡도 감소")

        # 실행 단계 수 제한
        execution_steps = state.get("execution_steps", [])
        if len(execution_steps) > 3:
            state["execution_steps"] = execution_steps[:3]
            print(f"  실행 단계 {len(execution_steps)}개 → 3개로 제한")

        # 식별된 요소 수 제한
        identified_elements = state.get("identified_elements", [])
        if len(identified_elements) > 10:
            state["identified_elements"] = identified_elements[:10]
            print(f"  식별 요소 {len(identified_elements)}개 → 10개로 제한")

        return state

    def _graceful_degradation(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """우아한 성능 저하"""
        print("🔻 우아한 성능 저하 모드")

        # 최소한의 기능으로 제한
        state["processing_stage"] = "failed"

        # 기본 오류 메시지 추가
        if not state.get("validation_errors"):
            state["validation_errors"] = []

        state["validation_errors"].append(
            ValidationError(
                error_type="system_error",
                message="시스템 오류로 인해 기본 기능으로 제한됩니다",
                suggested_fix="나중에 다시 시도하거나 관리자에게 문의하세요"
            )
        )

        return state

    def _create_error_report(self, state: InstructionAnalyzerState) -> Dict[str, Any]:
        """오류 보고서 생성"""
        validation_errors = state.get("validation_errors", [])

        error_report = {
            "timestamp": datetime.now().isoformat(),
            "session_id": state.get("session_id"),
            "processing_stage": state.get("processing_stage"),
            "error_count": len(validation_errors),
            "errors": [],
            "recovery_actions": [],
            "system_state": {
                "has_parsed_intent": bool(state.get("parsed_intent")),
                "has_page_analysis": bool(state.get("page_analysis")),
                "execution_steps_count": len(state.get("execution_steps", [])),
                "identified_elements_count": len(state.get("identified_elements", []))
            }
        }

        for error in validation_errors:
            error_report["errors"].append({
                "type": error.error_type,
                "message": error.message,
                "suggested_fix": error.suggested_fix,
                "requires_user_input": error.requires_user_input
            })

        return error_report

    # === 오류 복구 및 대안 제시 메서드 ===

    def _suggest_error_alternatives(self, state: InstructionAnalyzerState) -> List[Dict[str, Any]]:
        """
        오류 상황에 대한 대안 제시

        Args:
            state: 현재 상태

        Returns:
            List[Dict]: 대안 제안 목록
        """
        print("💡 오류 대안 제시 생성 중...")

        validation_errors = state.get("validation_errors", [])
        processing_stage = state.get("processing_stage", "unknown")

        alternatives = []

        # 처리 단계별 대안 제시
        if processing_stage == "failed":
            alternatives.extend(
                self._suggest_general_recovery_alternatives(validation_errors))

        # 오류 타입별 대안 제시
        error_types = {error.error_type for error in validation_errors}

        for error_type in error_types:
            if error_type.startswith("llm_"):
                alternatives.extend(self._suggest_llm_alternatives())
            elif error_type.startswith("page_"):
                alternatives.extend(
                    self._suggest_page_analysis_alternatives(state))
            elif error_type.startswith("instruction_"):
                alternatives.extend(
                    self._suggest_instruction_alternatives(state))
            elif error_type.startswith("plan_"):
                alternatives.extend(self._suggest_plan_alternatives(state))
            elif error_type.startswith("user_") or error_type.startswith("human_"):
                alternatives.extend(self._suggest_interaction_alternatives())

        # 중복 제거
        unique_alternatives = []
        seen_titles = set()
        for alt in alternatives:
            if alt["title"] not in seen_titles:
                unique_alternatives.append(alt)
                seen_titles.add(alt["title"])

        print(f"✅ {len(unique_alternatives)}개 대안 제안 생성")
        return unique_alternatives

    def _suggest_general_recovery_alternatives(self, errors: List[ValidationError]) -> List[Dict[str, Any]]:
        """일반적인 복구 대안"""
        alternatives = []

        # 기본 재시도 옵션
        alternatives.append({
            "type": "retry",
            "title": "다시 시도",
            "description": "동일한 설정으로 처음부터 다시 시도합니다",
            "action": "restart_workflow",
            "success_probability": 0.6,
            "estimated_time": "30초",
            "requirements": []
        })

        # 단순화된 접근
        alternatives.append({
            "type": "simplify",
            "title": "단순화된 처리",
            "description": "복잡한 기능을 제외하고 기본 기능만 사용합니다",
            "action": "use_basic_mode",
            "success_probability": 0.8,
            "estimated_time": "15초",
            "requirements": []
        })

        # 수동 개입
        if any(error.requires_user_input for error in errors):
            alternatives.append({
                "type": "manual",
                "title": "수동 지원 모드",
                "description": "각 단계에서 사용자 확인을 받으며 진행합니다",
                "action": "enable_manual_mode",
                "success_probability": 0.9,
                "estimated_time": "2-5분",
                "requirements": ["사용자 상호작용 필요"]
            })

        return alternatives

    def _suggest_llm_alternatives(self) -> List[Dict[str, Any]]:
        """LLM 관련 오류 대안"""
        return [
            {
                "type": "model_fallback",
                "title": "대체 모델 사용",
                "description": "더 안정적인 대체 LLM 모델을 사용합니다",
                "action": "switch_to_fallback_model",
                "success_probability": 0.7,
                "estimated_time": "30초",
                "requirements": ["대체 모델 API 키"]
            },
            {
                "type": "offline_mode",
                "title": "오프라인 모드",
                "description": "사전 정의된 패턴을 사용하여 LLM 없이 처리합니다",
                "action": "enable_offline_mode",
                "success_probability": 0.5,
                "estimated_time": "10초",
                "requirements": []
            },
            {
                "type": "reduced_complexity",
                "title": "복잡도 감소",
                "description": "더 간단한 프롬프트와 처리 방식을 사용합니다",
                "action": "reduce_llm_complexity",
                "success_probability": 0.8,
                "estimated_time": "20초",
                "requirements": []
            }
        ]

    def _suggest_page_analysis_alternatives(self, state: InstructionAnalyzerState) -> List[Dict[str, Any]]:
        """페이지 분석 오류 대안"""
        alternatives = []

        # 기본 분석 모드
        alternatives.append({
            "type": "basic_analysis",
            "title": "기본 분석 모드",
            "description": "고급 분석을 건너뛰고 기본적인 요소만 식별합니다",
            "action": "use_basic_page_analysis",
            "success_probability": 0.8,
            "estimated_time": "10초",
            "requirements": []
        })

        # 수동 요소 지정
        alternatives.append({
            "type": "manual_elements",
            "title": "수동 요소 지정",
            "description": "사용자가 직접 작업할 요소를 지정합니다",
            "action": "request_manual_element_selection",
            "success_probability": 0.9,
            "estimated_time": "1-2분",
            "requirements": ["사용자가 페이지 요소 정보 제공"]
        })

        # 일반적인 셀렉터 사용
        alternatives.append({
            "type": "generic_selectors",
            "title": "일반 셀렉터 사용",
            "description": "일반적인 HTML 요소 셀렉터를 사용합니다",
            "action": "use_generic_selectors",
            "success_probability": 0.6,
            "estimated_time": "5초",
            "requirements": []
        })

        return alternatives

    def _suggest_instruction_alternatives(self, state: InstructionAnalyzerState) -> List[Dict[str, Any]]:
        """지시사항 분석 오류 대안"""
        alternatives = []

        # 키워드 기반 분석
        alternatives.append({
            "type": "keyword_analysis",
            "title": "키워드 기반 분석",
            "description": "간단한 키워드 매칭으로 의도를 파악합니다",
            "action": "use_keyword_analysis",
            "success_probability": 0.7,
            "estimated_time": "5초",
            "requirements": []
        })

        # 지시사항 명확화
        alternatives.append({
            "type": "clarification",
            "title": "지시사항 명확화",
            "description": "사용자에게 더 구체적인 지시사항을 요청합니다",
            "action": "request_instruction_clarification",
            "success_probability": 0.9,
            "estimated_time": "1-3분",
            "requirements": ["사용자 응답 필요"]
        })

        # 예시 기반 선택
        alternatives.append({
            "type": "example_selection",
            "title": "예시에서 선택",
            "description": "일반적인 작업 예시 중에서 선택하도록 합니다",
            "action": "show_common_task_examples",
            "success_probability": 0.8,
            "estimated_time": "30초",
            "requirements": ["사용자 선택 필요"]
        })

        return alternatives

    def _suggest_plan_alternatives(self, state: InstructionAnalyzerState) -> List[Dict[str, Any]]:
        """계획 생성 오류 대안"""
        alternatives = []

        # 템플릿 기반 계획
        alternatives.append({
            "type": "template_plan",
            "title": "템플릿 기반 계획",
            "description": "사전 정의된 작업 템플릿을 사용합니다",
            "action": "use_plan_template",
            "success_probability": 0.8,
            "estimated_time": "10초",
            "requirements": []
        })

        # 단계별 계획 생성
        alternatives.append({
            "type": "step_by_step_planning",
            "title": "단계별 계획 생성",
            "description": "한 번에 하나씩 단계를 생성하고 확인합니다",
            "action": "enable_step_by_step_planning",
            "success_probability": 0.9,
            "estimated_time": "2-5분",
            "requirements": ["각 단계별 사용자 확인"]
        })

        # 최소 계획
        alternatives.append({
            "type": "minimal_plan",
            "title": "최소 계획",
            "description": "가장 기본적인 1-2단계 계획만 생성합니다",
            "action": "generate_minimal_plan",
            "success_probability": 0.7,
            "estimated_time": "5초",
            "requirements": []
        })

        return alternatives

    def _suggest_interaction_alternatives(self) -> List[Dict[str, Any]]:
        """사용자 상호작용 오류 대안"""
        return [
            {
                "type": "auto_proceed",
                "title": "자동 진행",
                "description": "기본값을 사용하여 사용자 개입 없이 진행합니다",
                "action": "enable_auto_proceed",
                "success_probability": 0.6,
                "estimated_time": "즉시",
                "requirements": []
            },
            {
                "type": "simplified_questions",
                "title": "간단한 질문",
                "description": "예/아니오로 답할 수 있는 간단한 질문만 사용합니다",
                "action": "use_simple_questions",
                "success_probability": 0.8,
                "estimated_time": "30초",
                "requirements": ["간단한 사용자 응답"]
            },
            {
                "type": "preset_options",
                "title": "사전 설정 옵션",
                "description": "미리 정의된 옵션 중에서만 선택하도록 합니다",
                "action": "use_preset_options",
                "success_probability": 0.9,
                "estimated_time": "15초",
                "requirements": ["옵션 선택"]
            }
        ]

    def _execute_alternative_action(self, action: str, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """
        대안 액션 실행

        Args:
            action: 실행할 액션명
            state: 현재 상태

        Returns:
            InstructionAnalyzerState: 액션 실행 후 상태
        """
        print(f"🔧 대안 액션 실행: {action}")

        try:
            if action == "restart_workflow":
                state = self._restart_workflow(state)
            elif action == "use_basic_mode":
                state = self._enable_basic_mode(state)
            elif action == "enable_manual_mode":
                state = self._enable_manual_mode(state)
            elif action == "switch_to_fallback_model":
                state = self._switch_to_fallback_model(state)
            elif action == "enable_offline_mode":
                state = self._enable_offline_mode(state)
            elif action == "use_basic_page_analysis":
                state = self._use_basic_page_analysis(state)
            elif action == "use_keyword_analysis":
                state = self._use_keyword_analysis(state)
            elif action == "use_plan_template":
                state = self._use_plan_template(state)
            elif action == "generate_minimal_plan":
                state = self._generate_minimal_plan(state)
            elif action == "enable_auto_proceed":
                state = self._enable_auto_proceed(state)
            else:
                print(f"⚠️ 알 수 없는 대안 액션: {action}")

            print("✅ 대안 액션 실행 완료")

        except Exception as e:
            print(f"❌ 대안 액션 실행 실패: {e}")
            # 대안 실행도 실패하면 최소한의 복구
            state = self._minimal_recovery(state)

        return state

    def _restart_workflow(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """워크플로우 재시작"""
        print("🔄 워크플로우 재시작")

        # 오류 상태 초기화
        state["processing_stage"] = "analyzing_instruction"
        state["validation_errors"] = []
        state["missing_info"] = []

        return state

    def _enable_basic_mode(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """기본 모드 활성화"""
        print("🔧 기본 모드 활성화")

        # 복잡한 기능 비활성화
        state["basic_mode"] = True
        state["processing_stage"] = "analyzing_instruction"

        return state

    def _enable_manual_mode(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """수동 모드 활성화"""
        print("👤 수동 모드 활성화")

        state["manual_mode"] = True
        state["step_by_step_execution"] = True

        return state

    def _switch_to_fallback_model(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """대체 모델로 전환"""
        print("🔄 대체 모델로 전환")

        try:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash", temperature=0.1)
            state["fallback_model_active"] = True
        except Exception as e:
            print(f"대체 모델 전환 실패: {e}")

        return state

    def _enable_offline_mode(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """오프라인 모드 활성화"""
        print("📴 오프라인 모드 활성화")

        state["offline_mode"] = True

        # 기본 의도 생성
        if not state.get("parsed_intent"):
            state["parsed_intent"] = UserIntent(
                primary_goal="click",
                target_objects=["버튼"],
                confidence_score=0.3
            )

        return state

    def _use_basic_page_analysis(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """기본 페이지 분석 사용"""
        print("📄 기본 페이지 분석 사용")

        # 기본 페이지 컨텍스트 생성
        state["page_analysis"] = PageContext(
            url=state.get("current_url", ""),
            title="기본 분석 페이지",
            page_type="unknown"
        )

        # 기본 요소들 생성
        basic_elements = [
            PageElement(
                element_type="input",
                selector="input",
                description="입력 요소",
                is_interactive=True
            ),
            PageElement(
                element_type="button",
                selector="button",
                description="버튼 요소",
                is_interactive=True
            )
        ]

        state["identified_elements"] = basic_elements

        return state

    def _use_keyword_analysis(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """키워드 기반 분석 사용"""
        print("🔤 키워드 기반 분석 사용")

        user_instruction = state.get("user_instruction", "")
        fallback_intent = self._create_fallback_intent(user_instruction)
        state["parsed_intent"] = fallback_intent

        return state

    def _use_plan_template(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """계획 템플릿 사용"""
        print("📋 계획 템플릿 사용")

        parsed_intent = state.get("parsed_intent")
        if not parsed_intent:
            parsed_intent = UserIntent(
                primary_goal="click", confidence_score=0.3)

        # 목표별 템플릿 계획
        template_plans = {
            "search": [
                ExecutionStep(1, ActionType.CLICK, "검색 입력창",
                              expected_outcome="입력창 활성화"),
                ExecutionStep(2, ActionType.TYPE, "검색 입력창", parameters={
                              "text": "검색어"}, expected_outcome="검색어 입력"),
                ExecutionStep(3, ActionType.CLICK, "검색 버튼",
                              expected_outcome="검색 실행")
            ],
            "click": [
                ExecutionStep(1, ActionType.CLICK, "대상 요소",
                              expected_outcome="요소 클릭됨")
            ],
            "type": [
                ExecutionStep(1, ActionType.CLICK, "입력 필드",
                              expected_outcome="필드 활성화"),
                ExecutionStep(2, ActionType.TYPE, "입력 필드", parameters={
                              "text": "텍스트"}, expected_outcome="텍스트 입력")
            ]
        }

        template = template_plans.get(
            parsed_intent.primary_goal, template_plans["click"])
        state["execution_steps"] = template

        return state

    def _generate_minimal_plan(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """최소 계획 생성"""
        print("⚡ 최소 계획 생성")

        # 가장 기본적인 1단계 계획
        minimal_plan = [
            ExecutionStep(
                step_id=1,
                action_type=ActionType.CLICK,
                target_description="첫 번째 상호작용 요소",
                expected_outcome="요소와 상호작용 완료"
            )
        ]

        state["execution_steps"] = minimal_plan

        return state

    def _enable_auto_proceed(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """자동 진행 활성화"""
        print("⚡ 자동 진행 모드 활성화")

        state["auto_proceed"] = True
        state["awaiting_user_input"] = False

        # 기본 승인 처리
        if state.get("execution_steps"):
            state["is_approved"] = True
            state["final_plan"] = state["execution_steps"]
            state["plan_status"] = PlanStatus.APPROVED
            state["processing_stage"] = "completed"

        return state

    def _minimal_recovery(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """최소한의 복구"""
        print("🆘 최소한의 복구 실행")

        # 가장 기본적인 상태로 설정
        state["processing_stage"] = "completed"
        state["is_approved"] = False

        # 기본 오류 메시지
        state["validation_errors"] = [
            ValidationError(
                error_type="minimal_recovery",
                message="시스템 복구를 위해 최소 기능으로 제한됩니다",
                suggested_fix="나중에 다시 시도해주세요"
            )
        ]

        return state

    def _generate_plan_node(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """
        실행 계획 생성 노드 - 구체적인 실행 단계들을 생성
        """
        print("📋 실행 계획 생성 중...")

        try:
            state["processing_stage"] = "generating_plan"
            state["last_updated"] = datetime.now().isoformat()

            # 실제 실행 계획 생성
            execution_steps = self._generate_execution_plan(state)

            # 계획 최적화
            if execution_steps:
                optimized_steps = self._optimize_execution_plan(
                    execution_steps, state.get("parsed_intent"))

                # 계획 검증
                is_valid, validation_errors = self._validate_execution_plan(
                    optimized_steps, state)

                if is_valid:
                    state["execution_steps"] = optimized_steps
                    state["plan_status"] = PlanStatus.UNDER_REVIEW
                    print(f"✅ 실행 계획 생성 완료 - {len(optimized_steps)}단계 (최적화됨)")
                else:
                    # 오류가 있어도 계획은 저장
                    state["execution_steps"] = optimized_steps
                    state["plan_status"] = PlanStatus.DRAFT
                    state["validation_errors"].extend(validation_errors)
                    print(
                        f"⚠️ 실행 계획 생성 완료 - {len(optimized_steps)}단계 (검증 오류 {len(validation_errors)}개)")
            else:
                state["execution_steps"] = []
                state["plan_status"] = PlanStatus.DRAFT
                print("❌ 실행 계획 생성 실패 - 단계가 생성되지 않음")

        except Exception as e:
            print(f"❌ 실행 계획 생성 실패: {e}")
            state = self._handle_workflow_error(e, state, "generate_plan")

        return state

    def _review_plan_node(self, state: InstructionAnalyzerState) -> InstructionAnalyzerState:
        """
        계획 검토 노드 - 생성된 계획을 사용자가 검토하고 승인
        """
        print("👀 계획 검토 중...")

        try:
            state["processing_stage"] = "awaiting_review"
            state["last_updated"] = datetime.now().isoformat()

            # 검토용 계획 정보 생성
            review_info = self._present_plan_for_review(state)

            # 검토 정보를 상태에 저장 (나중에 UI에서 사용)
            state["review_info"] = review_info

            # 검토 기반 질문 생성
            review_questions = self._generate_review_questions(review_info)

            # 기존 질문과 병합
            existing_question_ids = {
                q.question_id for q in state.get("user_questions", [])}
            new_questions = [
                q for q in review_questions if q.question_id not in existing_question_ids]
            state["user_questions"].extend(new_questions)

            # 검토 정보 출력
            self._display_review_summary(review_info)

            # 테스트를 위한 자동 응답 시뮬레이션
            if new_questions:
                print(f"📋 사용자에게 {len(new_questions)}개 검토 질문 제시")
                simulated_responses = self._simulate_review_responses(
                    new_questions, review_info)

                if simulated_responses:
                    state = self._process_review_responses(
                        state, simulated_responses)
                else:
                    # 기본 승인 처리
                    state["is_approved"] = True
                    state["final_plan"] = state["execution_steps"]
                    state["plan_status"] = PlanStatus.APPROVED
                    state["processing_stage"] = "completed"
            else:
                # 질문이 없으면 자동 승인
                state["is_approved"] = True
                state["final_plan"] = state["execution_steps"]
                state["plan_status"] = PlanStatus.APPROVED
                state["processing_stage"] = "completed"

            print("✅ 계획 검토 완료")

        except Exception as e:
            print(f"❌ 계획 검토 실패: {e}")
            state = self._handle_workflow_error(e, state, "review_plan")
            state["validation_errors"].append(
                ValidationError(
                    error_type="plan_review_failed",
                    message=f"계획 검토 중 오류: {str(e)}"
                )
            )

        return state

    # === 라우팅 함수들 ===

    def _route_after_instruction_analysis(self, state: InstructionAnalyzerState) -> str:
        """지시사항 분석 후 라우팅"""
        if state["processing_stage"] == "failed":
            return "failed"
        return "analyze_page"

    def _route_after_page_analysis(self, state: InstructionAnalyzerState) -> str:
        """페이지 분석 후 라우팅"""
        if state["processing_stage"] == "failed":
            return "failed"
        return "validate_requirements"

    def _route_after_validation(self, state: InstructionAnalyzerState) -> str:
        """검증 후 라우팅"""
        if state["processing_stage"] == "failed":
            return "failed"
        if state.get("missing_info"):
            return "human_interaction"
        return "generate_plan"

    def _route_after_human_interaction(self, state: InstructionAnalyzerState) -> str:
        """사용자 상호작용 후 라우팅"""
        if state["processing_stage"] == "failed":
            return "failed"
        if state.get("missing_info"):
            return "validate_requirements"
        return "generate_plan"

    def _route_after_plan_generation(self, state: InstructionAnalyzerState) -> str:
        """계획 생성 후 라우팅"""
        if state["processing_stage"] == "failed":
            return "failed"
        return "review_plan"

    def _route_after_plan_review(self, state: InstructionAnalyzerState) -> str:
        """계획 검토 후 라우팅"""
        if state["processing_stage"] == "failed":
            return "failed"
        if state.get("is_approved"):
            return "completed"
        return "human_interaction"

    def __str__(self) -> str:
        """문자열 표현"""
        return f"InstructionAnalyzer(session_id={self.current_session_id})"

    def __repr__(self) -> str:
        """개발자용 문자열 표현"""
        return (
            f"InstructionAnalyzer("
            f"model={getattr(self.llm, 'model_name', 'unknown')}, "
            f"session_id={self.current_session_id})"
        )


# 편의 함수들
def create_instruction_analyzer(**kwargs) -> InstructionAnalyzer:
    """
    InstructionAnalyzer 인스턴스 생성 편의 함수

    Args:
        **kwargs: InstructionAnalyzer 생성자 인자들

    Returns:
        InstructionAnalyzer: 생성된 인스턴스
    """
    return InstructionAnalyzer(**kwargs)


def validate_execution_step(step: ExecutionStep) -> List[str]:
    """
    ExecutionStep 검증 함수

    Args:
        step: 검증할 실행 단계

    Returns:
        List[str]: 검증 오류 메시지 목록
    """
    errors = []

    if not step.target_description:
        errors.append("target_description이 비어있습니다")

    if step.action_type not in ActionType:
        errors.append(f"지원되지 않는 액션 타입: {step.action_type}")

    if step.step_id < 0:
        errors.append("step_id는 0 이상이어야 합니다")

    # 액션 타입별 특별 검증
    if step.action_type == ActionType.TYPE and not step.parameters.get("text"):
        errors.append("TYPE 액션에는 'text' 매개변수가 필요합니다")

    if step.action_type == ActionType.NAVIGATE and not step.parameters.get("url"):
        errors.append("NAVIGATE 액션에는 'url' 매개변수가 필요합니다")

    return errors


# 테스트용 메인 함수
if __name__ == "__main__":
    # 기본 테스트
    analyzer = create_instruction_analyzer()

    print("=== InstructionAnalyzer 기본 테스트 ===")
    print(f"세션 정보: {analyzer.get_session_info()}")
    print(f"지원 액션: {analyzer.get_supported_actions()}")

    # 입력 검증 테스트
    test_instruction = "네이버에서 날씨를 검색해주세요"
    test_html = "<html><body><h1>Test</h1></body></html>"
    test_url = "https://www.naver.com"

    validation_errors = analyzer.validate_input(
        test_instruction, test_html, test_url)
    print(f"입력 검증 결과: {validation_errors}")

    if not validation_errors:
        # 분석 실행 (현재는 초기 상태만 반환)
        result = analyzer.analyze_instruction(
            test_instruction, test_html, test_url)
        print(f"분석 결과 상태: {result['processing_stage']}")
        print(f"세션 ID: {result['session_id']}")

    print("=== 테스트 완료 ===")
