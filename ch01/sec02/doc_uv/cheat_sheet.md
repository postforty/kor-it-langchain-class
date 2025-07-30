# UV 치트 시트

> 원문: <https://whdrns2013.github.io/python/20250515_002_uv/>

## 특징

- Rust로 제작된 파이썬 패키지 매니저이자 프로젝트 매니저입니다.
- pip, pip-tools, poetry, pyenv, twine, virtualenv를 대체할 수 있는 단일 도구입니다.
- pip보다 10 ~ 100배 빠른 속도를 제공합니다.
- universal lockfile로 포괄적인 프로젝트 관리가 가능합니다.
- inline dependency metadata를 지원하여 스크립트를 실행할 수 있습니다.
- Python 버전을 설치하고 관리할 수 있습니다.
- Python 패키지로 등록되어있는 도구들을 설치하고 실행할 수 있습니다.
- pip 호환 인터페이스를 제공하여 친숙한 CLI 환경을 제공합니다.
- Cargo-style workspace를 제공하여 확장 가능한 프로젝트의 환경을 제공합니다.
- 종속성 중복 제거를 위한 global cache를 사용해 디스크 공간 효율성을 확보합니다.
- curl 또는 pip로 설치 가능합니다.
- macOS, Linux, Windows를 지원합니다.

## UV 설치와 사용

### 설치

```bash
# mac, Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
# windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

```bash
# pip
pip install uv

# pipx
pipx install uv
```

### uv 명령어 환경변수 추가

- 설치 후에 uv 명령어가 인식되지 않을 경우, 환경변수에 추가해줍니다.

```bash
export PATH="/root/.local/bin:$PATH"
```

### 프로젝트 init

- 가장 먼저 `init`을 통해 프로젝트(작업공간=workspace)를 초기화해줍니다.

```bash
# 현재 디렉터리에 초기화를 진행할 경우
uv init .

# 현재 디렉터리 하위에 디렉터리를 만들면서 그곳에 초기화를 진행할 경우
uv init example
```

- 초기화한 내용을 삭제하려면 프로젝트 루트에서 파일들을 삭제하고, `uv clean cache`를 해줍니다.

```bash
# 파일 삭제
- .python-verion
- main.py
- pyproject.toml
- README.md

# cache clean
uv cache clean
```

### 초기화한 프로젝트 디렉터리 살펴보기

| 파일명            | 설명                                                                                                                                                                                                                                                                             |
| :---------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `.python-version` | - **용도:** 프로젝트에서 사용할 Python 버전을 명시합니다. <br>- **예시:** `3.11.9`처럼 작성되어 있습니다. <br>- **사용 도구:** `pyenv`, `uv`, `direnv` 등이 이 파일을 참고합니다.                                                                                                |
| `main.py`         | - **용도:** 기본 실행 스크립트로, Python 프로젝트의 진입점 역할을 합니다. <br>- **내용:** 일반적으로 “Hello, world!” 같은 간단한 예제 코드가 들어 있습니다. <br>- **실행:** `python main.py` 또는 `uv run main.py`로 실행 가능합니다.                                            |
| `pyproject.toml`  | - **용도:** Python 프로젝트의 설정 파일입니다. <br>- **포함 내용:** 프로젝트 이름, 버전, 의존성, 빌드 시스템 설정 등. <br>- **표준:** [PEP 518](https://www.python.org/dev/peps/pep-0518/)에 따라 Python 생태계에서 공식 표준으로 채택된 형식입니다.                             |
| `README.md`       | - **용도:** 프로젝트에 대한 설명을 적는 문서입니다. <br>- **형식:** Markdown(.md) 포맷. <br>- **보통 포함 내용:** 프로젝트 개요, 설치 방법, 사용 방법, 예제 코드 등.                                                                                                             |
| `uv.lock`         | - **용도**: 프로젝트의 **의존성 잠금(lock) 파일**입니다.<br>- 패키지 버전과 해시를 고정해 **재현 가능한 환경**을 보장합니다.<br>- 의존성 라이브러리나 파이썬 버전 등을 버전과 함께 기록합니다.<br>- **재현성**: 같은 uv.lock 파일을 사용하면 항상 동일한 환경 확보가 가능합니다. |

### Python 설치하기

- 해당 프로젝트 디렉터리(workspace)에 파이썬을 설치합니다.
- 파이썬이 이미 시스템에 있다면, 별도의 설정 없이도 uv가 이를 감지하여 사용합니다.
- 그러나 uv는 파이썬 버전을 설치하고 관리할 수도 있습니다.

```bash
# 파이썬 설치
uv python install

# 버전 명시
uv python install 3.12
```

설치된 파이썬의 버전 및 경로는 `uv python list` 명령어를 통해 조회할 수 있습니다. 이 명령어는 시스템에 기존에 설치된 파이썬도 탐지하여 출력합니다.

```bash
uv python list
```

### uv로 python script 실행하기

예시를 위한 `example.py`는 아래와 같습니다.

```python
import datetime
print(f"it's uv! now is {datetime.datetime.now().strftime('%Y-%m-%d')}")
```

```bash
uv run example.py

>> it's uv! now is 2025-05-13
```

### uv 용 python 실행하기

```bash
uv run python
```

## 의존성

### UV에서 의존성 관리

- UV에서는 `uv.lock` 파일에 의존성을 명세합니다.
- 이 파일에는 파이썬의 버전이나 의존성 라이브러리의 종류와 버전을 명세합니다.
- 이를 통해 동일한 `uv.lock` 파일로 실행할 경우 재현성을 보장할 수 있게 됩니다.

### 의존성 추가

- `uv add` 명령어로 프로젝트의 의존성을 추가할 수 있습니다.

```bash
# pandas 설치 예시
uv add pandas

Resolved 7 packages in 655ms
Prepared 6 packages in 3.49s
Installed 6 packages in 1.25s
 + numpy==2.2.5
 + pandas==2.2.3
 + python-dateutil==2.9.0.post0
 + pytz==2025.2
 + six==1.17.0
 + tzdata==2025.2
```

이렇게 추가한 의존성은 프로젝트 디렉터리의 `.venv` 디렉터리에 저장됩니다.
또한 의존성이 `uv.lock`과 `pyproject.toml`에 명세됩니다.

### 개발용 의존성 추가

개발용 의존성 추가 시에는 `uv add` 명령어에 `--dev` 옵션을 추가하면 됩니다.

```bash
uv add [패키지명] --dev
```

### 의존성 제거

의존성 제거 시에는 `uv remove` 명령어를 사용할 수 있습니다.

```bash
uv remove [패키지명]
```

### 의존성 라이브러리 업그레이드

의존성 라이브러리를 업그레이드할 때에는 `uv lock --upgrade-package` 명령어를 사용할 수 있습니다.

```bash
uv lock --upgrade-package [패키지명]
```

### uv.lock 파일로 의존성 설치

`uv.lock` 파일만 있다면 충돌 없이 의존성 설치가 가능합니다. `uv sync` 명령어를 사용하면 됩니다.

```bash
# uv sync를 사용하면 환경을 수동으로 업데이트할 수 있습니다.
uv sync
```

### 의존성 추출

uv에서는 `uv export` 명령어를 통해 의존성 라이브러리 리스트를 추출할 수 있습니다. pip의 `pip freeze`와 같은 기능입니다.

```bash
# 의존성 라이브러리 추출
uv export -o requirements.txt

# 의존성 라이브러리 추출, 개발용 의존성 제외
uv export -o requirements.txt --no-dev

# 의존성 라이브러리 추출, 해시값 제외
uv export -o requirements.txt --no-hashes

# pip을 이용할 수도 있습니다.
uv pip freeze > requirements.txt
```

## 기타

### UV로 Jupyter 실행하기

```bash
# jupyter 의존성 설치
uv add jupyter jupyterlab ipykernel

# jupyterlab 실행
uv run --with jupyter jupyter lab --allow-root --ip=0.0.0.0 --port=8888 --NotebookApp.token=''
```
