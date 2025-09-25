"""
지시사항 분석 에이전트를 위한 데이터 구조 및 타입 정의
"""

from typing import TypedDict, Optional, List, Dict, Any, Literal
from dataclasses import dataclass
from enum import Enum


class ActionType(Enum):
    """실행 가능한 액션 타입들"""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SEARCH = "search"
    WAIT = "wait"
    SCROLL = "scroll"
    ANALYZE = "analyze"
    VERIFY = "verify"


class ValidationStatus(Enum):
    """검증 상태"""
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    NEEDS_CLARIFICATION = "needs_clarification"


class PlanStatus(Enum):
    """실행 계획 상태"""
    DRAFT = "draft"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


@dataclass
class ExecutionStep:
    """실행 단계를 나타내는 데이터 클래스"""
    step_id: int
    action_type: ActionType
    target_description: str  # 자연어 설명 (예: "검색창", "로그인 버튼")
    target_selector: Optional[str] = None  # CSS 셀렉터 (PageAnalyzer가 생성)
    parameters: Dict[str, Any] = None  # 추가 매개변수 (텍스트 입력값 등)
    expected_outcome: str = ""  # 예상 결과
    fallback_actions: List[str] = None  # 실패시 대안 액션들
    validation_criteria: str = ""  # 성공 검증 기준
    dependencies: List[int] = None  # 의존하는 이전 단계들의 step_id

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.fallback_actions is None:
            self.fallback_actions = []
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class PageElement:
    """페이지 요소 정보"""
    element_type: str  # 'button', 'input', 'link', 'form' 등
    selector: str  # CSS 셀렉터
    description: str  # 자연어 설명
    attributes: Dict[str, str] = None  # HTML 속성들
    text_content: str = ""  # 요소의 텍스트 내용
    is_visible: bool = True  # 가시성 여부
    is_interactive: bool = True  # 상호작용 가능 여부

    def __post_init__(self):
        if self.attributes is None:
            self.attributes = {}


@dataclass
class PageContext:
    """현재 페이지의 컨텍스트 정보"""
    url: str
    title: str
    main_elements: List[PageElement] = None  # 주요 UI 요소들
    forms: List[PageElement] = None  # 폼 요소들
    navigation: List[PageElement] = None  # 네비게이션 요소들
    content_areas: List[PageElement] = None  # 콘텐츠 영역들
    interactive_elements: List[PageElement] = None  # 상호작용 가능한 요소들
    page_type: str = "unknown"  # 'search', 'form', 'article', 'dashboard' 등

    def __post_init__(self):
        if self.main_elements is None:
            self.main_elements = []
        if self.forms is None:
            self.forms = []
        if self.navigation is None:
            self.navigation = []
        if self.content_areas is None:
            self.content_areas = []
        if self.interactive_elements is None:
            self.interactive_elements = []


@dataclass
class UserIntent:
    """파싱된 사용자 의도"""
    primary_goal: str  # 주요 목표 (예: "검색", "로그인", "구매")
    target_objects: List[str] = None  # 대상 객체들 (예: ["날씨", "검색창"])
    actions_sequence: List[str] = None  # 예상 액션 시퀀스
    constraints: List[str] = None  # 제약 조건들
    success_criteria: str = ""  # 성공 기준
    confidence_score: float = 0.0  # 해석 신뢰도 (0.0 ~ 1.0)

    def __post_init__(self):
        if self.target_objects is None:
            self.target_objects = []
        if self.actions_sequence is None:
            self.actions_sequence = []
        if self.constraints is None:
            self.constraints = []


@dataclass
class ValidationError:
    """검증 오류 정보"""
    error_type: str  # 'missing_info', 'ambiguous', 'impossible' 등
    message: str  # 오류 메시지
    suggested_fix: str = ""  # 제안된 해결책
    requires_user_input: bool = False  # 사용자 입력 필요 여부


@dataclass
class UserQuestion:
    """사용자에게 할 질문"""
    question_id: str
    question_text: str
    question_type: Literal["choice", "text", "confirmation"]  # 질문 유형
    options: List[str] = None  # 선택지 (choice 타입인 경우)
    default_answer: Optional[str] = None  # 기본 답변
    timeout_seconds: int = 30  # 타임아웃 시간

    def __post_init__(self):
        if self.options is None:
            self.options = []


class InstructionAnalyzerState(TypedDict):
    """지시사항 분석 에이전트의 상태"""

    # === 입력 데이터 ===
    user_instruction: str  # 사용자의 원본 지시사항
    html_content: str  # 현재 페이지 HTML
    current_url: str  # 현재 페이지 URL

    # === 분석 결과 ===
    parsed_intent: Optional[UserIntent]  # 파싱된 사용자 의도
    page_analysis: Optional[PageContext]  # 페이지 분석 결과
    identified_elements: List[PageElement]  # 식별된 UI 요소들

    # === 실행 계획 ===
    execution_steps: List[ExecutionStep]  # 생성된 실행 단계들
    plan_status: PlanStatus  # 계획 상태

    # === 검증 및 오류 처리 ===
    validation_errors: List[ValidationError]  # 검증 오류들
    missing_info: List[str]  # 부족한 정보 목록

    # === Human-in-the-Loop ===
    user_questions: List[UserQuestion]  # 사용자에게 할 질문들
    user_responses: Dict[str, str]  # 사용자 응답들 (question_id -> response)
    awaiting_user_input: bool  # 사용자 입력 대기 중 여부

    # === 상태 관리 ===
    current_step: int  # 현재 처리 중인 단계
    processing_stage: Literal[
        "analyzing_instruction",
        "analyzing_page",
        "validating_requirements",
        "generating_plan",
        "awaiting_review",
        "completed",
        "failed"
    ]  # 현재 처리 단계
    action_parameters: Dict[str, Any]  # 추출된 액션 매개변수들

    # === 모드 설정 ===
    basic_mode: bool  # 기본 모드 활성화 여부
    manual_mode: bool  # 수동 모드 활성화 여부
    offline_mode: bool  # 오프라인 모드 활성화 여부
    auto_proceed: bool  # 자동 진행 모드 활성화 여부
    fallback_model_active: bool  # 대체 모델 활성화 여부

    # === 결과 및 승인 ===
    is_approved: bool  # 사용자 승인 여부
    final_plan: Optional[List[ExecutionStep]]  # 최종 승인된 실행 계획
    selected_element: Optional[PageElement]  # 사용자가 선택한 요소
    review_info: Optional[Dict[str, Any]]  # 검토용 계획 정보
    step_by_step_execution: bool  # 단계별 실행 여부

    # === 메타데이터 ===
    created_at: str  # 생성 시간
    last_updated: str  # 마지막 업데이트 시간
    session_id: str  # 세션 ID
    error_report: Optional[Dict[str, Any]]  # 오류 보고서


# === 상수 정의 ===

# 기본 타임아웃 설정
DEFAULT_USER_RESPONSE_TIMEOUT = 30  # 초
DEFAULT_PAGE_ANALYSIS_TIMEOUT = 10  # 초
DEFAULT_LLM_TIMEOUT = 15  # 초

# 신뢰도 임계값
MIN_CONFIDENCE_THRESHOLD = 0.7  # 최소 신뢰도
HIGH_CONFIDENCE_THRESHOLD = 0.9  # 높은 신뢰도

# 최대 재시도 횟수
MAX_RETRY_ATTEMPTS = 3
MAX_CLARIFICATION_ROUNDS = 5

# 지원되는 페이지 타입들
SUPPORTED_PAGE_TYPES = [
    "search",
    "form",
    "article",
    "dashboard",
    "e-commerce",
    "social_media",
    "news",
    "unknown"
]

# 일반적인 UI 요소 패턴들
COMMON_UI_PATTERNS = {
    "search_box": ["input[type='search']", "input[name*='search']", ".search-input", "#search"],
    "search_button": ["button[type='submit']", ".search-btn", ".search-button", "input[type='submit']"],
    "login_button": [".login", ".signin", "button[name='login']", "#login-btn"],
    "navigation_menu": ["nav", ".nav", ".menu", ".navigation"],
    "main_content": ["main", ".main", "#main", ".content", "#content"]
}

# 오류 메시지 템플릿
ERROR_MESSAGES = {
    "missing_info": "지시사항을 실행하기 위해 추가 정보가 필요합니다: {details}",
    "ambiguous": "지시사항이 모호합니다. 명확히 해주세요: {details}",
    "impossible": "현재 페이지에서 요청된 작업을 수행할 수 없습니다: {details}",
    "element_not_found": "'{element}'에 해당하는 요소를 찾을 수 없습니다",
    "page_analysis_failed": "페이지 분석에 실패했습니다: {error}",
    "llm_error": "지시사항 해석 중 오류가 발생했습니다: {error}"
}
