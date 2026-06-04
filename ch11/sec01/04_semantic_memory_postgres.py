import os
from dotenv import load_dotenv
load_dotenv()

import uuid
from datetime import datetime
from dataclasses import dataclass
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.tools import ToolRuntime, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.postgres import PostgresStore
from langgraph.store.base import IndexConfig

@dataclass
class Context:
    user_id: str

# 임베딩 모델 초기화
# pgvector HNSW 인덱스는 최대 2000차원까지만 지원하므로 output_dimensionality로 차원을 축소합니다.
EMBEDDING_DIMS = 768
_embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001") # 참고: gemini-embedding-001 차원은 3072

def embed_documents_reduced(texts):
    """차원 축소가 적용된 임베딩 래퍼 함수"""
    return _embeddings.embed_documents(texts, output_dimensionality=EMBEDDING_DIMS)

# 도구 정의
@tool
def get_user_info(runtime: ToolRuntime[Context]) -> str:
    """사용자의 기본 정보를 조회합니다."""
    assert runtime.store is not None
    user_info = runtime.store.get(("users",), runtime.context.user_id)
    return str(user_info.value) if user_info else "알 수 없는 사용자"

@tool
def save_user_info(
    preferences: list[str] = None,
    interests: list[str] = None,
    experiences: list[str] = None,
    current_activities: list[str] = None,
    goals: list[str] = None,
    routines: list[str] = None,
    concerns: list[str] = None,
    achievements: list[str] = None,
    runtime: ToolRuntime[Context] = None
) -> str:
    """사용자의 다양한 정보를 8개의 세분화된 카테고리(네임스페이스)로 분류하여 체계적으로 저장합니다."""
    assert runtime.store is not None
    store = runtime.store
    user_id = runtime.context.user_id
    current_time = datetime.now().isoformat()

    categories = {
        "preferences": preferences, "interests": interests, "experiences": experiences,
        "current_activities": current_activities, "goals": goals, "routines": routines,
        "concerns": concerns, "achievements": achievements
    }

    update_summary = []
    for category, values in categories.items():
        if values:
            for value in values:
                item_id = str(uuid.uuid4())
                store.put(
                    (user_id, category),
                    item_id,
                    {"text": value, "created_at": current_time, "category": category}
                )
            update_summary.append(f"{len(values)}개의 {category}")

    return f"사용자 장기 기억 성공적 저장: {', '.join(update_summary)}"

@tool
def search_user_memories(
    query: str,
    category: str = None,
    limit: int = 5,
    runtime: ToolRuntime[Context] = None
) -> str:
    """사용자의 메모리를 '자연어 쿼리(query)'를 이용해 시맨틱(의미) 검색합니다."""
    assert runtime.store is not None
    store = runtime.store
    user_id = runtime.context.user_id

    if category:
        namespace = (user_id, category)
        results = store.search(namespace, query=query, limit=limit)
        if not results:
            return f"{category} 카테고리에서 관련된 메모리를 찾을 수 없습니다."
        result_text = f"{category} 관련 메모리:\n"
        for item in results:
            result_text += f"- {item.value['text']} (저장일자: {item.value['created_at']})\n"
        return result_text
    else:
        categories = ["preferences", "interests", "experiences", "current_activities",
                     "goals", "routines", "concerns", "achievements"]
        all_results = []
        for cat in categories:
            try:
                results = store.search((user_id, cat), query=query, limit=limit)
                all_results.extend([(r, cat) for r in results])
            except Exception as e:
                continue

        all_results.sort(key=lambda x: x[0].score if hasattr(x[0], 'score') else 0, reverse=True)
        all_results = all_results[:limit]

        if not all_results:
            return "관련된 메모리를 찾을 수 없습니다."

        result_text = "관련 메모리:\n"
        for item, cat in all_results:
            result_text += f"[{cat}] {item.value['text']} (저장일자: {item.value['created_at']})\n"
        return result_text


def main():
    model = init_chat_model("google_genai:gemini-3.1-flash-lite")
    checkpointer = InMemorySaver()

    # .env에 정의된 접속 정보를 가져와 DB_URI 동적 생성
    pg_id = os.getenv("PGVECTOR_ID", "postgres")
    pg_pw = os.getenv("PGVECTOR_PW", "postgres")
    pg_host = os.getenv("PGVECTOR_HOST", "localhost")
    pg_port = os.getenv("PGVECTOR_PORT", "5432")
    pg_db = os.getenv("PGVECTOR_DB", "postgres")
    
    DB_URI = f"postgresql://{pg_id}:{pg_pw}@{pg_host}:{pg_port}/{pg_db}?sslmode=disable"

    with PostgresStore.from_conn_string(
        DB_URI,
        index=IndexConfig(embed=embed_documents_reduced, dims=EMBEDDING_DIMS),
    ) as store:
        store.setup()
        
        agent = create_agent(
            model=model,
            tools=[get_user_info, save_user_info, search_user_memories],
            store=store,
            checkpointer=checkpointer,
            context_schema=Context,
            system_prompt="당신은 누적된 사용자 메모리를 활용하여 맞춤 조언을 제공하는 라이프 코치입니다."
        )

        print("==============================================")
        print("라이프 코치 AI가 시작되었습니다. (종료하려면 'q' 입력)")
        print("==============================================")
        
        while True:
            try:
                user_input = input("\nUser: ")
                if user_input.lower() in ["q", "exit", "quit"]:
                    break
                if not user_input.strip():
                    continue

                response = agent.invoke(
                    {"messages": [{"role": "user", "content": user_input}]},
                    config={"configurable": {"thread_id": "1"}}, # 단기 기억 대화 세션
                    context=Context(user_id="user_123") # 장기 기억 유저 식별
                )

                for msg in response["messages"]:
                    msg.pretty_print()
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\n오류 발생: {e}")

if __name__ == "__main__":
    main()
