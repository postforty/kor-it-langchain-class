# 기능

> 원문: <https://docs.astral.sh/uv/getting-started/features/>

uv는 파이썬 개발을 위한 필수 기능을 제공합니다. 파이썬 설치 및 간단한 스크립트 작업부터 여러 파이썬 버전과 플랫폼을 지원하는 대규모 프로젝트 작업에 이르기까지 다양합니다.

uv의 인터페이스는 독립적으로 또는 함께 사용할 수 있는 섹션으로 나눌 수 있습니다.

## 파이썬 버전

파이썬 자체를 설치하고 관리하는 기능입니다.

- `uv python install`: 파이썬 버전 설치.
- `uv python list`: 사용 가능한 파이썬 버전 보기.
- `uv python find`: 설치된 파이썬 버전 찾기.
- `uv python pin`: 현재 프로젝트에서 특정 파이썬 버전을 사용하도록 고정.
- `uv python uninstall`: 파이썬 버전 제거.

시작하려면 [파이썬 설치 가이드](../../guides/install-python/)를 참조하십시오.

## 스크립트

독립 실행형 파이썬 스크립트(예: `example.py`) 실행.

- `uv run`: 스크립트 실행.
- `uv add --script`: 스크립트에 종속성 추가.
- `uv remove --script`: 스크립트에서 종속성 제거.

시작하려면 [스크립트 실행 가이드](../../guides/scripts/)를 참조하십시오.

## 프로젝트

파이썬 프로젝트 생성 및 작업(예: `pyproject.toml` 사용).

- `uv init`: 새 파이썬 프로젝트 생성.
- `uv add`: 프로젝트에 종속성 추가.
- `uv remove`: 프로젝트에서 종속성 제거.
- `uv sync`: 프로젝트의 종속성을 환경과 동기화.
- `uv lock`: 프로젝트 종속성에 대한 잠금 파일 생성.
- `uv run`: 프로젝트 환경에서 명령 실행.
- `uv tree`: 프로젝트의 종속성 트리 보기.
- `uv build`: 프로젝트를 배포 아카이브로 빌드.
- `uv publish`: 프로젝트를 패키지 인덱스에 게시.

시작하려면 [프로젝트 가이드](../../guides/projects/)를 참조하십시오.

## 도구

파이썬 패키지 인덱스에 게시된 도구(예: `ruff` 또는 `black`) 실행 및 설치.

- `uvx` / `uv tool run`: 임시 환경에서 도구 실행.
- `uv tool install`: 사용자 전체에 도구 설치.
- `uv tool uninstall`: 도구 제거.
- `uv tool list`: 설치된 도구 목록.
- `uv tool update-shell`: 도구 실행 파일을 포함하도록 셸 업데이트.

시작하려면 [도구 가이드](../../guides/tools/)를 참조하십시오.

## pip 인터페이스

환경 및 패키지 수동 관리 — 레거시 워크플로 또는 상위 수준 명령이 충분한 제어를 제공하지 않는 경우에 사용하도록 고안되었습니다.

가상 환경 생성(`venv` 및 `virtualenv` 대체):

- `uv venv`: 새 가상 환경 생성.

자세한 내용은 [환경 사용 문서](../../pip/environments/)를 참조하십시오.

환경에서 패키지 관리([`pip`](https://github.com/pypa/pip) 및 [`pipdeptree`](https://github.com/tox-dev/pipdeptree) 대체):

- `uv pip install`: 현재 환경에 패키지 설치.
- `uv pip show`: 설치된 패키지에 대한 세부 정보 표시.
- `uv pip freeze`: 설치된 패키지 및 해당 버전 나열.
- `uv pip check`: 현재 환경에 호환되는 패키지가 있는지 확인.
- `uv pip list`: 설치된 패키지 나열.
- `uv pip uninstall`: 패키지 제거.
- `uv pip tree`: 환경의 종속성 트리 보기.

자세한 내용은 [패키지 관리 문서](../../pip/packages/)를 참조하십시오.

환경에서 패키지 잠금([`pip-tools`](https://github.com/jazzband/pip-tools) 대체):

- `uv pip compile`: 요구 사항을 잠금 파일로 컴파일.
- `uv pip sync`: 잠금 파일과 환경 동기화.

자세한 내용은 [환경 잠금 문서](../../pip/compile/)를 참조하십시오.

> **중요**
> 이러한 명령은 기반으로 하는 도구의 인터페이스 및 동작을 정확히 구현하지 않습니다. 일반적인 워크플로에서 벗어날수록 차이점을 발견할 가능성이 높습니다. 자세한 내용은 [pip-호환성 가이드](../../pip/compatibility/)를 참조하십시오.

## 유틸리티

캐시, 저장 디렉터리 또는 자체 업데이트 수행과 같은 uv의 상태 관리 및 검사:

- `uv cache clean`: 캐시 항목 제거.
- `uv cache prune`: 오래된 캐시 항목 제거.
- `uv cache dir`: uv 캐시 디렉터리 경로 표시.
- `uv tool dir`: uv 도구 디렉터리 경로 표시.
- `uv python dir`: uv 설치된 파이썬 버전 경로 표시.
- `uv self update`: uv를 최신 버전으로 업데이트.

## 다음 단계

각 기능에 대한 소개는 [가이드](../../guides/)를 참조하고, uv 기능에 대한 심층적인 세부 정보는 [개념](../../concepts/) 페이지를 확인하거나, 문제가 발생하면 [도움 받기](../help/) 방법을 알아보십시오.
