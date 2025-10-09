# pgvector 데이터 삭제 쿼리

```
DELETE FROM langchain_pg_embedding WHERE collection_id = '646db416-108b-42b0-965f-d3777eca9f22';

DELETE FROM langchain_pg_collection
WHERE uuid = '646db416-108b-42b0-965f-d3777eca9f22';
```

## 쿼리 목적

제공된 SQL 쿼리는 `langchain_pg_embedding` 테이블과 `langchain_pg_collection` 테이블에서 특정 `collection_id` 또는 `uuid`를 가진 데이터를 삭제하는 데 사용된다. 이는 일반적으로 LangChain과 pgvector를 사용하여 관리되는 벡터 저장소에서 특정 컬렉션(예: 특정 문서 또는 주제와 관련된 임베딩)을 제거할 때 활용된다.

## 쿼리 구성 요소

다음은 쿼리의 각 부분에 대한 설명이다.

### 1. `DELETE FROM langchain_pg_embedding WHERE collection_id = '646db416-108b-42b0-965f-d3777eca9f22';`

-   **`langchain_pg_embedding`**: 이 테이블은 실제 벡터 임베딩 데이터와 해당 메타데이터를 저장한다. 각 행은 하나의 임베딩과 관련된 정보를 나타낸다.
-   **`collection_id`**: 이 컬럼은 임베딩이 속한 컬렉션을 식별하는 고유 ID이다. 여러 임베딩이 동일한 `collection_id`를 가질 수 있으며, 이는 해당 임베딩이 같은 논리적 그룹에 속함을 의미한다.
-   **`'646db416-108b-42b0-965f-d3777eca9f22'`**: 삭제할 임베딩 컬렉션의 실제 ID 값이다. 이 값은 사용자의 환경에 따라 달라진다.

이 쿼리는 지정된 `collection_id`에 해당하는 모든 임베딩 데이터를 `langchain_pg_embedding` 테이블에서 삭제한다.

### 2. `DELETE FROM langchain_pg_collection WHERE uuid = '646db416-108b-42b0-965f-d3777eca9f22';`

-   **`langchain_pg_collection`**: 이 테이블은 pgvector에 저장된 컬렉션 자체의 정의 및 메타데이터를 관리한다. 각 행은 하나의 고유한 컬렉션을 나타낸다.
-   **`uuid`**: 이 컬럼은 컬렉션의 고유 식별자로, `langchain_pg_embedding` 테이블의 `collection_id`와 연결된다.
-   **`'646db416-108b-42b0-965f-d3777eca9f22'`**: 삭제할 컬렉션 정의의 실제 UUID 값이다. 이 값은 `langchain_pg_embedding` 테이블에서 사용된 `collection_id`와 동일해야 한다.

이 쿼리는 지정된 `uuid`에 해당하는 컬렉션 정의를 `langchain_pg_collection` 테이블에서 삭제한다.

## 작동 방식 및 중요성

이 두 쿼리는 특정 컬렉션을 pgvector 데이터베이스에서 완전히 제거하기 위해 순서대로 실행되어야 한다.

1.  **임베딩 데이터 삭제 (`langchain_pg_embedding`)**: 먼저 컬렉션에 속한 모든 개별 임베딩 데이터(실제 벡터와 관련 메타데이터)를 삭제한다. 이는 대량의 데이터가 될 수 있으므로, 먼저 이를 처리하여 참조 무결성 문제를 방지하고 불필요한 데이터를 제거한다.
2.  **컬렉션 정의 삭제 (`langchain_pg_collection`)**: 다음으로, 해당 컬렉션 자체의 정의를 삭제한다. 임베딩 데이터가 먼저 삭제되었으므로, 이 단계에서 컬렉션 정의를 삭제하여 데이터베이스의 일관성을 유지한다.

**주의사항**: 이 쿼리를 실행하기 전에 삭제하려는 `collection_id` 또는 `uuid`가 올바른지 반드시 확인해야 한다. 잘못된 ID를 사용하면 의도하지 않은 데이터 손실이 발생할 수 있다.
