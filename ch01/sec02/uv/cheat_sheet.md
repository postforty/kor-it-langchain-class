# UV 치트 시트

## 1\. UV의 특징

- **Rust 기반의 빠른 성능**: Rust로 개발되어 기존 파이썬 패키지 관리자 대비 10\~100배 빠른 속도를 자랑한다.
- **단일 도구로 통합**: `pip`, `pip-tools`, `poetry`, `pyenv`, `twine`, `virtualenv` 등 다양한 파이썬 도구의 기능을 UV 하나로 대체할 수 있다.
- **Universal Lockfile**: `uv.lock` 파일 하나로 프로젝트의 파이썬 버전 명시 및 모든 의존성 패키지의 정확한 버전과 해시값을 고정하여 일관되고 재현 가능한 개발 환경을 보장한다.
- **Inline Dependency Metadata 지원**: 스크립트 파일 자체에 의존성을 직접 명시함으로써 별도의 `requirements.txt` 파일 없이도 스크립트를 바로 실행하고 필요한 의존성을 자동으로 설치할 수 있다.
- **Python 버전 관리**: 파이썬 버전을 직접 설치하고 관리하는 기능을 제공한다.
- **Python 패키지 실행**: 파이썬 패키지로 등록된 도구들을 설치하고 실행할 수 있다.
- **Pip 호환 인터페이스**: `pip`과 유사한 CLI(Command Line Interface) 환경을 제공하여 기존 사용자에게 친숙함을 준다.
- **Cargo-style Workspace**: Rust의 Cargo와 유사한 워크스페이스 개념을 도입하여 확장 가능한 프로젝트 환경을 제공한다.
- **Global Cache**: 종속성 중복 제거를 위한 글로벌 캐시를 사용하여 디스크 공간 효율성을 확보한다.
- **다양한 설치 방법**을 지원한다(`curl` 또는 `pip`을 이용해 쉽게 설치 가능).
- **크로스 플랫폼 지원**: macOS, Linux, Windows 등 다양한 운영체제를 지원한다.

---

## 2\. UV 설치 및 프로젝트 초기화

### 2-1. UV 설치

- **macOS 및 Linux 설치**

  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- **Windows 설치**

  ```bash
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

- **pip을 이용한 설치**

  ```bash
  pip install uv
  ```

- **pipx를 이용한 설치**

  ```bash
  pipx install uv
  ```

### 2-2. UV 명령어 환경변수 추가

- 설치 후 `uv` 명령어가 인식되지 않을 경우, 환경변수에 추가한다.

  ```bash
  export PATH="/root/.local/bin:$PATH"
  ```

### 2-3. 프로젝트 초기화 (`uv init`)

- `init` 명령어를 통해 프로젝트(**작업공간=workspace**)를 초기화한다.

  ```bash
  # 현재 디렉터리에 초기화 진행
  uv init .

  # 현재 디렉터리 하위에 디렉터리를 만들면서 그곳에 초기화 진행
  uv init example
  ```

- 가상 환경 생성

```bash
# .venv 폴더가 생성됨(VSCode에서 해상 커널 선택)
uv venv
```

```bash
# 가상 환경 해제 명령어
deactivate
```

- 초기화된 프로젝트 환경을 완전히 제거하려면, `uv init` 명령어로 생성된 파일을 삭제하고 필요한 경우 `uv cache clean` 명령어로 캐시를 정리한다.

  ```bash
  # uv init으로 생성되는 주요 파일 (예시)
  - .python-version
  - pyproject.toml
  - README.md
  - uv.lock (의존성 설치 시 생성)

  # 캐시 정리 명령어
  uv cache clean
  ```

### 2-4. 초기화된 프로젝트 디렉터리 구조 이해

| 파일명                | 설명                                                                                                                                                                                                                                                                                                                                     |
| :-------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`.python-version`** | - **용도:** 프로젝트에서 사용할 Python 버전을 명시한다. <br/>- **예시:** `3.13`처럼 작성되어 있다. <br/>- **참고 도구:** `pyenv`, `uv`, `direnv` 등이 이 파일을 참고한다.                                                                                                                                                                |
| **`main.py`**         | - **용도:** 기본 실행 스크립트로, Python 프로젝트의 진입점 역할을 한다. 이 파일은 `uv init` 시 기본으로 생성되지 않으며, 프로젝트 구성 시 사용자가 직접 생성하는 예시 파일이다. <br/>- **내용:** 일반적으로 “Hello, world\!” 같은 간단한 예제 코드가 포함된다. <br/>- **실행:** `python main.py` 또는 `uv run main.py`로 실행할 수 있다. |
| **`pyproject.toml`**  | - **용도:** Python 프로젝트의 설정 파일이다. <br/>- **포함 내용:** 프로젝트 이름, 버전, 의존성, 빌드 시스템 설정 등. <br/>- **표준:** [PEP 518](https://www.python.org/dev/peps/pep-0518/)에 따라 Python 생태계에서 공식 표준으로 채택된 형식이다.                                                                                       |
| **`README.md`**       | - **용도:** 프로젝트에 대한 설명을 담는 문서이다. 이 파일은 `uv init` 명령어 실행 시 자동으로 생성된다. <br/>- **형식:** Markdown(.md) 포맷. <br/>- **주요 내용:** 프로젝트 개요, 설치 방법, 사용 방법, 예제 코드 등이 포함된다.                                                                                                         |
| **`uv.lock`**         | - **용도**: 프로젝트의 **의존성 잠금(lock) 파일**이다.<br/>- `pyproject.toml`에 명시된 의존성 패키지들의 **정확한 버전과 해시값**을 고정하여 **재현 가능한 환경**을 보장한다.<br/>- **재현성**: 동일한 `uv.lock` 파일을 사용하면 항상 동일한 환경 확보가 가능하다.                                                                       |

---

## 3\. Python 버전 및 스크립트 실행

### 3-1. Python 설치 및 관리

- 프로젝트 디렉터리(workspace)에 특정 파이썬 버전을 설치할 수 있다. 시스템에 이미 파이썬이 있다면, UV가 이를 감지하여 사용한다.

  ```bash
  # 기본 파이썬 버전 설치 (uv가 권장하는 최신 버전)
  uv python install

  # 특정 파이썬 버전 명시하여 설치
  uv python install 3.12
  ```

- 설치된 파이썬의 버전 및 경로는 `uv python list` 명령어를 통해 조회할 수 있다. 이 명령어는 시스템에 기존에 설치된 파이썬도 탐지하여 출력한다.

  ```bash
  uv python list
  ```

- 설치된 파이썬을 삭제한다.

  ```bash
  # 특정 파이썬 버전 삭제
  uv python uninstall 3.12

  # uv가 관리하는 모든 파이썬 버전 삭제 (주의: 시스템의 다른 파이썬 설치는 삭제하지 않음)
  uv python uninstall --all
  ```

### 3-2. UV를 이용한 Python 스크립트 실행

- 예시를 위한 `example.py` 파일 내용은 다음과 같다.

  ```python
  import datetime
  print(f"it's uv! now is {datetime.datetime.now().strftime('%Y-%m-%d')}")
  ```

- `uv run` 명령어를 통해 파이썬 스크립트를 실행한다.

  ```bash
  uv run example.py
  ```

### 3-3. UV 환경에서 Python 셸 실행

- `uv run python` 명령어를 통해 UV 관리 환경에서 파이썬 셸을 실행할 수 있다.

  ```bash
  uv run python
  ```

---

## 4\. 의존성 관리

### 4-1. UV의 의존성 관리 방식

- UV는 `pyproject.toml`에 프로젝트의 직접적인 의존성(`pandas`, `numpy` 등)과 그 버전에 대한 제약 조건(예: `pandas = "^2.3.1"`)을 명세한다.
- `uv.lock` 파일은 `pyproject.toml`에 명세된 의존성을 기반으로, 모든 전이 의존성(transitive dependencies)을 포함하여 각 패키지의 **정확한 버전과 해시값**을 기록한다.
- 이를 통해 동일한 `uv.lock` 파일로 실행할 경우 항상 동일한 개발 환경을 재현할 수 있다.

### 4-2. 의존성 추가 및 제거

- **의존성 추가**: `uv add` 명령어로 프로젝트의 의존성을 추가한다.

  ```bash
  # pandas 설치 예시
  uv add pandas
  ```

  - 이렇게 추가된 의존성은 프로젝트 디렉터리 내의 `.venv` 가상 환경에 저장된다.
  - 의존성 정보는 `pyproject.toml`에 선언되고, 그에 따른 정확한 버전 정보는 `uv.lock`에 잠긴다.

- **개발용 의존성 추가**: 개발용 의존성 추가 시에는 `uv add` 명령어에 `--dev` 옵션을 사용한다.

  ```bash
  uv add [패키지명] --dev
  ```

- **의존성 제거**: `uv remove` 명령어를 사용하여 의존성을 제거한다.

  ```bash
  uv remove [패키지명]
  ```

### 4-3. 의존성 업데이트 및 동기화

- **의존성 라이브러리 업그레이드**: 특정 의존성 라이브러리를 업그레이드할 때에는 `uv lock --upgrade-package` 명령어를 사용한다.

  ```bash
  uv lock --upgrade-package [패키지명]
  ```

- **`uv.lock` 파일로 의존성 설치 (동기화)**: `uv.lock` 파일만 있다면 충돌 없이 의존성 설치가 가능하다. `uv sync` 명령어를 사용한다.

  ```bash
  # uv sync를 사용하면 pyproject.toml 및 uv.lock 파일에 맞춰 환경을 동기화할 수 있다.
  uv sync
  ```

### 4-4. 의존성 목록 추출

- UV에서는 `uv export` 명령어를 통해 의존성 라이브러리 목록을 추출할 수 있다. 이는 `pip freeze`와 같은 기능이다.

  ```bash
  # 의존성 라이브러리 목록을 requirements.txt 파일로 추출
  uv export -o requirements.txt

  # 의존성 라이브러리 목록 추출 시, 개발용 의존성 제외
  uv export -o requirements.txt --no-dev

  # 의존성 라이브러리 목록 추출 시, 해시값 제외
  uv export -o requirements.txt --no-hashes

  # pip 명령어를 통해서도 추출 가능
  uv pip freeze > requirements.txt
  ```

---

## 5\. 기타 활용 예시

### 5-1. UV를 이용한 Jupyter 실행

- Jupyter 관련 의존성을 설치한다.

  ```bash
  uv add jupyter jupyterlab ipykernel
  ```

- `uv run` 명령어를 통해 JupyterLab을 실행한다.

  ```bash
  uv run --with jupyter jupyter lab --allow-root --ip=0.0.0.0 --port=8888 --NotebookApp.token=''
  ```

### 5-2. VS Code에서 UV 가상 환경의 Jupyter Notebook 사용 시 고려사항

- `uv`로 관리되는 가상 환경에서 Jupyter Notebook을 사용할 경우, VS Code에서 Jupyter 커널 선택 시 `.venv`와 같은 해당 가상 환경을 선택해야 정상적으로 동작한다.
- 가상 환경에서 Jupyter Notebook 관련 의존성(예: `ipykernel`)을 설치할 때는 `pip` 대신 `uv add` 명령어를 사용한다. 예를 들어, `uv add ipykernel`과 같이 사용한다.
