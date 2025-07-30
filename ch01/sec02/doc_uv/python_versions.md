# 파이썬 버전

파이썬 버전은 파이썬 인터프리터(예: `python` 실행 파일), 표준 라이브러리 및 기타 지원 파일로 구성됩니다.

## 관리형 및 시스템 파이썬 설치

시스템에 기존 파이썬 설치가 있는 것이 일반적이므로 uv는 파이썬 버전 [탐색](#discovery-of-python-versions)을 지원합니다. 그러나 uv는 [파이썬 버전 자체를 설치](#installing-a-python-version)하는 것도 지원합니다. 이 두 가지 유형의 파이썬 설치를 구별하기 위해 uv는 자신이 설치하는 파이썬 버전을 _관리형_ 파이썬 설치라고 부르고 다른 모든 파이썬 설치를 _시스템_ 파이썬 설치라고 부릅니다.

> **참고**
> uv는 운영 체제에서 설치한 파이썬 버전과 다른 도구로 설치 및 관리되는 파이썬 버전을 구별하지 않습니다. 예를 들어, 파이썬 설치가 `pyenv`로 관리되는 경우에도 uv에서는 _시스템_ 파이썬 버전으로 간주됩니다.

## 버전 요청

대부분의 uv 명령에서 `--python` 플래그를 사용하여 특정 파이썬 버전을 요청할 수 있습니다. 예를 들어, 가상 환경을 생성할 때:

```bash
uv venv --python 3.11.6
```

uv는 필요한 경우 파이썬 3.11.6이 사용 가능한지 확인한 다음 다운로드 및 설치하고, 이를 사용하여 가상 환경을 생성합니다.

다음 파이썬 버전 요청 형식이 지원됩니다:

- `<version>` (예: `3`, `3.12`, `3.12.3`)
- `<version-specifier>` (예: `>=3.12,<3.13`)
- `<implementation>` (예: `cpython` 또는 `cp`)
- `<implementation>@<version>` (예: `cpython@3.12`)
- `<implementation><version>` (예: `cpython3.12` 또는 `cp312`)
- `<implementation><version-specifier>` (예: `cpython>=3.12,<3.13`)
- `<implementation>-<version>-<os>-<arch>-<libc>` (예: `cpython-3.12.3-macos-aarch64-none`)

또한, 다음을 사용하여 특정 시스템 파이썬 인터프리터를 요청할 수 있습니다:

- `<executable-path>` (예: `/opt/homebrew/bin/python3`)
- `<executable-name>` (예: `mypython3`)
- `<install-dir>` (예: `/some/environment/`)

기본적으로 uv는 시스템에서 파이썬 버전을 찾을 수 없는 경우 자동으로 다운로드합니다. 이 동작은 [python-downloads 옵션으로 비활성화](#disabling-automatic-python-downloads)할 수 있습니다.

### 파이썬 버전 파일

`.python-version` 파일은 기본 파이썬 버전 요청을 생성하는 데 사용될 수 있습니다. uv는 작업 디렉터리와 모든 상위 디렉터리에서 `.python-version` 파일을 검색합니다. 찾을 수 없는 경우, uv는 사용자 수준 구성 디렉터리를 확인합니다. 위에 설명된 모든 요청 형식을 사용할 수 있지만, 다른 도구와의 상호 운용성을 위해 버전 번호를 사용하는 것이 좋습니다.

`.python-version` 파일은 [`uv python pin`](../../reference/cli/#uv-python-pin) 명령을 사용하여 현재 디렉터리에 생성할 수 있습니다.

전역 `.python-version` 파일은 [`uv python pin --global`](../../reference/cli/#uv-python-pin) 명령을 사용하여 사용자 구성 디렉터리에 생성할 수 있습니다.

`--no-config`를 사용하여 `.python-version` 파일 탐색을 비활성화할 수 있습니다.

uv는 프로젝트 또는 워크스페이스 경계(사용자 구성 디렉터리 제외)를 넘어 `.python-version` 파일을 검색하지 않습니다.

## 파이썬 버전 설치

uv는 macOS, Linux 및 Windows용 다운로드 가능한 CPython 및 PyPy 배포판 목록을 번들로 제공합니다.

> **팁**
> 기본적으로 파이썬 버전은 `uv python install`을 사용하지 않고 필요에 따라 자동으로 다운로드됩니다.

특정 버전의 파이썬을 설치하려면:

```bash
uv python install 3.12.3
```

최신 패치 버전을 설치하려면:

```bash
uv python install 3.12
```

제약 조건을 만족하는 버전을 설치하려면:

```bash
uv python install '>=3.8,<3.10'
```

여러 버전을 설치하려면:

```bash
uv python install 3.9 3.10 3.11
```

특정 구현을 설치하려면:

```bash
uv python install pypy
```

파일 경로와 같이 로컬 인터프리터를 요청하는 데 사용되는 형식을 제외하고 모든 [파이썬 버전 요청](#requesting-a-version) 형식이 지원됩니다.

기본적으로 `uv python install`은 관리형 파이썬 버전이 설치되었는지 확인하거나 최신 버전을 설치합니다. `.python-version` 파일이 있으면 uv는 파일에 나열된 파이썬 버전을 설치합니다. 여러 파이썬 버전이 필요한 프로젝트는 `.python-versions` 파일을 정의할 수 있습니다. 이 파일이 있으면 uv는 파일에 나열된 모든 파이썬 버전을 설치합니다.

> **중요**
> 사용 가능한 파이썬 버전은 각 uv 릴리스에 대해 고정됩니다. 새 파이썬 버전을 설치하려면 uv를 업그레이드해야 할 수 있습니다.

### 파이썬 실행 파일 설치

uv는 기본적으로 파이썬 실행 파일을 `PATH`에 설치합니다. 예를 들어, `uv python install 3.12`는 `~/.local/bin`에 `python3.12`와 같은 파이썬 실행 파일을 설치합니다.

> **팁** > `~/.local/bin`이 `PATH`에 없으면 `uv tool update-shell`을 사용하여 추가할 수 있습니다.

`python` 및 `python3` 실행 파일을 설치하려면 실험적인 `--default` 옵션을 포함하십시오:

```bash
uv python install 3.12 --default
```

파이썬 실행 파일을 설치할 때 uv는 기존 실행 파일이 uv에 의해 관리되는 경우에만 덮어씁니다. 예를 들어, `~/.local/bin/python3.12`가 이미 존재하는 경우 uv는 `--force` 플래그 없이는 덮어쓰지 않습니다.

uv는 자신이 관리하는 실행 파일을 업데이트합니다. 그러나 기본적으로 각 파이썬 부 버전의 최신 패치 버전을 선호합니다. 예를 들어:

```bash
uv python install 3.12.7  # Adds `python3.12` to `~/.local/bin`
uv python install 3.12.6  # Does not update `python3.12`
uv python install 3.12.8  # Updates `python3.12` to point to 3.12.8
```

## 파이썬 버전 업그레이드

> **중요**
> 파이썬 버전 업그레이드 지원은 _미리 보기_ 상태입니다. 이는 동작이 실험적이며 변경될 수 있음을 의미합니다.
> 업그레이드는 uv 관리형 파이썬 버전에 대해서만 지원됩니다.
> PyPy 및 GraalPy에 대한 업그레이드는 현재 지원되지 않습니다.

uv는 파이썬 버전을 최신 패치 릴리스(예: 3.13.4를 3.13.5로)로 투명하게 업그레이드할 수 있도록 합니다. uv는 부 버전 변경이 종속성 해결에 영향을 미칠 수 있으므로 부 파이썬 버전(예: 3.12를 3.13으로) 간의 투명한 업그레이드를 허용하지 않습니다.

uv 관리형 파이썬 버전은 `python upgrade` 명령을 사용하여 지원되는 최신 패치 릴리스로 업그레이드할 수 있습니다:

파이썬 버전을 지원되는 최신 패치 릴리스로 업그레이드하려면:

```bash
uv python upgrade 3.12
```

설치된 모든 파이썬 버전을 업그레이드하려면:

```bash
uv python upgrade
```

업그레이드 후 uv는 새 버전을 선호하지만, 가상 환경에서 여전히 사용될 수 있으므로 기존 버전은 유지합니다.

파이썬 버전이 미리 보기 모드가 활성화된 상태로 설치된 경우(예: `uv python install 3.12 --preview`), 해당 파이썬 버전을 사용하는 가상 환경은 새 패치 버전으로 자동으로 업그레이드됩니다.

> **참고**
> 가상 환경이 미리 보기 모드를 선택하기 _전에_ 생성된 경우, 자동 업그레이드에 포함되지 않습니다.

가상 환경이 명시적으로 요청된 패치 버전(예: `uv venv -p 3.10.8`)으로 생성된 경우, 새 버전으로 투명하게 업그레이드되지 않습니다.

### 부 버전 디렉터리

가상 환경에 대한 자동 업그레이드는 파이썬 부 버전과 함께 디렉터리를 사용하여 구현됩니다. 예를 들어:

```bash
~/.local/share/uv/python/cpython-3.12-macos-aarch64-none
```

이는 특정 패치 버전을 가리키는 심볼릭 링크(Unix) 또는 접합점(Windows)입니다:

```bash
readlink ~/.local/share/uv/python/cpython-3.12-macos-aarch64-none
~/.local/share/uv/python/cpython-3.12.11-macos-aarch64-none
```

이 링크가 다른 도구(예: 파이썬 인터프리터 경로를 정규화하여)에 의해 해결되고 가상 환경을 생성하는 데 사용되는 경우, 자동으로 업그레이드되지 않습니다.

## 프로젝트 파이썬 버전

uv는 프로젝트 명령 호출 시 `pyproject.toml` 파일에 정의된 `requires-python` 요구 사항을 준수합니다. 요구 사항과 호환되는 첫 번째 파이썬 버전이 사용되며, `.python-version` 파일 또는 `--python` 플래그를 통해 버전이 요청되지 않는 한 그러합니다.

## 사용 가능한 파이썬 버전 보기

설치된 파이썬 버전과 사용 가능한 파이썬 버전을 나열하려면:

```bash
uv python list
```

파이썬 버전을 필터링하려면 요청을 제공하십시오. 예를 들어, 모든 파이썬 3.13 인터프리터를 표시하려면:

```bash
uv python list 3.13
```

또는 모든 PyPy 인터프리터를 표시하려면:

```bash
uv python list pypy
```

기본적으로 다른 플랫폼 및 이전 패치 버전에 대한 다운로드는 숨겨져 있습니다.

모든 버전을 보려면:

```bash
uv python list --all-versions
```

다른 플랫폼의 파이썬 버전을 보려면:

```bash
uv python list --all-platforms
```

다운로드를 제외하고 설치된 파이썬 버전만 표시하려면:

```bash
uv python list --only-installed
```

자세한 내용은 [`uv python list` 참조](../../reference/cli/#uv-python-list)를 참조하십시오.

## 파이썬 실행 파일 찾기

파이썬 실행 파일을 찾으려면 `uv python find` 명령을 사용하십시오:

```bash
uv python find
```

기본적으로 이 명령은 사용 가능한 첫 번째 파이썬 실행 파일의 경로를 표시합니다. 실행 파일이 어떻게 탐색되는지에 대한 자세한 내용은 [탐색 규칙](#discovery-of-python-versions)을 참조하십시오.

이 인터페이스는 또한 많은 [요청 형식](#requesting-a-version)을 지원합니다. 예를 들어, 3.11 이상의 버전인 파이썬 실행 파일을 찾으려면:

```bash
uv python find '>=3.11'
```

기본적으로 `uv python find`는 가상 환경의 파이썬 버전을 포함합니다. 작업 디렉터리 또는 상위 디렉터리에서 `.venv` 디렉터리가 발견되거나 `VIRTUAL_ENV` 환경 변수가 설정된 경우, 이는 `PATH`의 모든 파이썬 실행 파일보다 우선합니다.

가상 환경을 무시하려면 `--system` 플래그를 사용하십시오:

```bash
uv python find --system
```

## 파이썬 버전 탐색

파이썬 버전을 검색할 때 다음 위치가 확인됩니다:

- `UV_PYTHON_INSTALL_DIR`의 관리형 파이썬 설치.
- macOS 및 Linux에서는 `python`, `python3` 또는 `python3.x`로, Windows에서는 `python.exe`로 `PATH`에 있는 파이썬 인터프리터.
- Windows에서는 요청된 버전과 일치하는 Windows 레지스트리 및 Microsoft Store 파이썬 인터프리터( `py --list-paths` 참조).

일부 경우에 uv는 가상 환경에서 파이썬 버전을 사용할 수 있도록 합니다. 이 경우, 위에서 설명한 설치를 검색하기 전에 가상 환경의 인터프리터가 요청과 호환되는지 확인됩니다. 자세한 내용은 [pip-호환 가상 환경 탐색](../../pip/environments/#discovery-of-python-environments) 문서를 참조하십시오.

탐색을 수행할 때 실행 불가능한 파일은 무시됩니다. 발견된 각 실행 파일은 [요청된 파이썬 버전](#requesting-a-version)을 충족하는지 확인하기 위해 메타데이터를 쿼리합니다. 쿼리가 실패하면 실행 파일은 건너뛰어집니다. 실행 파일이 요청을 만족하면 추가 실행 파일을 검사하지 않고 사용됩니다.

관리형 파이썬 버전을 검색할 때 uv는 더 새로운 버전을 먼저 선호합니다. 시스템 파이썬 버전을 검색할 때 uv는 가장 최신 버전이 아닌 첫 번째 호환 버전을 사용합니다.

시스템에서 파이썬 버전을 찾을 수 없는 경우, uv는 호환되는 관리형 파이썬 버전 다운로드를 확인합니다.

### 파이썬 미리 보기 릴리스

파이썬 미리 보기 릴리스는 기본적으로 선택되지 않습니다. 파이썬 미리 보기 릴리스는 요청과 일치하는 다른 사용 가능한 설치가 없는 경우에만 사용됩니다. 예를 들어, 미리 보기 버전만 사용 가능한 경우 해당 버전이 사용되지만, 그렇지 않은 경우 안정적인 릴리스 버전이 사용됩니다. 마찬가지로, 미리 보기 파이썬 실행 파일의 경로가 제공되면 다른 파이썬 버전이 요청과 일치하지 않고 미리 보기 버전이 사용됩니다.

미리 보기 파이썬 버전이 사용 가능하고 요청과 일치하는 경우, uv는 대신 안정적인 파이썬 버전을 다운로드하지 않습니다.

## 자동 파이썬 다운로드 비활성화

기본적으로 uv는 필요할 때 파이썬 버전을 자동으로 다운로드합니다.

[`python-downloads`](../../reference/settings/#python-downloads) 옵션을 사용하여 이 동작을 비활성화할 수 있습니다. 기본적으로 `automatic`으로 설정되어 있으며, `manual`로 설정하면 `uv python install` 중에만 파이썬 다운로드를 허용합니다.

> **팁** > `python-downloads` 설정은 기본 동작을 변경하기 위해 [영구 구성 파일](../configuration-files/)에 설정하거나, `--no-python-downloads` 플래그를 모든 uv 명령에 전달할 수 있습니다.

## 관리형 파이썬 버전 요구 또는 비활성화

기본적으로 uv는 시스템에서 찾은 파이썬 버전을 사용하려고 시도하며, 필요한 경우에만 관리형 파이썬 버전을 다운로드합니다. 시스템 파이썬 버전을 무시하고 관리형 파이썬 버전만 사용하려면 `--managed-python` 플래그를 사용하십시오:

```bash
uv python list --managed-python
```

마찬가지로, 관리형 파이썬 버전을 무시하고 시스템 파이썬 버전만 사용하려면 `--no-managed-python` 플래그를 사용하십시오:

```bash
uv python list --no-managed-python
```

구성 파일에서 uv의 기본 동작을 변경하려면 [python-preference 설정](#adjusting-python-version-preferences)을 사용하십시오.

## 파이썬 버전 선호도 조정

[`python-preference`](../../reference/settings/#python-preference) 설정은 시스템에 이미 존재하는 파이썬 설치를 선호할지, 아니면 uv가 다운로드하여 설치하는 파이썬 설치를 선호할지를 결정합니다.

기본적으로 `python-preference`는 `managed`로 설정되어 시스템 파이썬 설치보다 관리형 파이썬 설치를 선호합니다. 그러나 시스템 파이썬 설치는 관리형 파이썬 버전 다운로드보다 여전히 우선합니다.

다음 대체 옵션이 사용 가능합니다:

- `only-managed`: 관리형 파이썬 설치만 사용; 시스템 파이썬 설치는 사용하지 않음. `--managed-python`과 동일.
- `system`: 관리형 파이썬 설치보다 시스템 파이썬 설치를 선호.
- `only-system`: 시스템 파이썬 설치만 사용; 관리형 파이썬 설치는 사용하지 않음. `--no-managed-python`과 동일.

> **참고**
> 자동 파이썬 버전 다운로드는 선호도를 변경하지 않고 [비활성화](#disabling-automatic-python-downloads)할 수 있습니다.

## 파이썬 구현 지원

uv는 CPython, PyPy 및 GraalPy 파이썬 구현을 지원합니다. 파이썬 구현이 지원되지 않으면 uv는 해당 인터프리터를 탐색하지 못합니다.

구현은 긴 이름 또는 짧은 이름으로 요청할 수 있습니다:

- CPython: `cpython`, `cp`
- PyPy: `pypy`, `pp`
- GraalPy: `graalpy`, `gp`

구현 이름 요청은 대소문자를 구분하지 않습니다.

지원되는 형식에 대한 자세한 내용은 [파이썬 버전 요청](#requesting-a-version) 문서를 참조하십시오.

## 관리형 파이썬 배포판

uv는 CPython 및 PyPy 배포판의 다운로드 및 설치를 지원합니다.

### CPython 배포판

파이썬은 공식적인 배포 가능한 CPython 바이너리를 게시하지 않으므로, uv는 대신 Astral의 [python-build-standalone](https://github.com/astral-sh/python-build-standalone) 프로젝트에서 사전 빌드된 배포판을 사용합니다. `python-build-standalone`는 [Rye](https://github.com/astral-sh/rye), [Mise](https://mise.jdx.dev/lang/python.html), [bazelbuild/rules_python](https://github.com/bazelbuild/rules_python)와 같은 다른 많은 파이썬 프로젝트에서도 사용됩니다.

uv 파이썬 배포판은 자체 포함되어 있고, 이식성이 높으며, 성능이 뛰어납니다. `pyenv`와 같은 도구에서처럼 소스에서 파이썬을 빌드할 수 있지만, 그렇게 하려면 사전 설치된 시스템 종속성이 필요하며, 최적화되고 성능이 뛰어난 빌드(예: PGO 및 LTO 활성화)를 생성하는 것은 매우 느립니다.

이러한 배포판에는 일반적으로 이식성으로 인한 일부 동작 특이점이 있습니다. 자세한 내용은 [python-build-standalone quirks](https://gregoryszorc.com/docs/python-build-standalone/main/quirks.html) 문서를 참조하십시오. 또한 일부 플랫폼은 지원되지 않을 수 있습니다(예: ARM의 musl Linux용 배포판은 아직 사용할 수 없음).

### PyPy 배포판

PyPy 배포판은 PyPy 프로젝트에서 제공됩니다.

## Windows 레지스트리 등록

Windows에서는 관리형 파이썬 버전 설치 시 [PEP 514](https://peps.python.org/pep-0514/)에 정의된 대로 Windows 레지스트리에 등록됩니다.

설치 후 파이썬 버전은 `py` 런처를 사용하여 선택할 수 있습니다. 예를 들면:

```bash
uv python install 3.13.1
py -V:Astral/CPython3.13.1
```

제거 시 uv는 대상 버전에 대한 레지스트리 항목과 손상된 레지스트리 항목을 제거합니다.

