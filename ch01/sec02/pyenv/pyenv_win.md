# Windows용 pyenv

> 원문 : <https://github.com/pyenv-win/pyenv-win?tab=readme-ov-file>

[pyenv][1]는 머신에서 여러 버전의 파이썬을 관리하는 데 사용되는 놀라운 도구입니다. 저희는 이를 Windows로 포팅했습니다. 이 라이브러리를 개선하기 위한 여러분의 생각과 피드백은 프로젝트 성장에 도움이 됩니다.

기존 파이썬 사용자들을 위해 [pip을 통한 설치](#installation)를 지원합니다.

기여자 및 관심 있는 분들은 @[Slack](https://join.slack.com/t/pyenv/shared_invite/zt-f9ydwgyt-Fp8tehxqeCQi5mi77RxpGw)에 참여할 수 있습니다. 여러분의 도움은 저희에게 동기를 부여합니다!

[![pytest](https://github.com/pyenv-win/pyenv-win/actions/workflows/pytest.yml/badge.svg)](https://github.com/pyenv-win/pyenv-win/actions/workflows/pytest.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub issues open](https://img.shields.io/github/issues/pyenv-win/pyenv-win.svg?)](https://github.com/pyenv-win/pyenv-win/issues)
[![Downloads](https://pepy.tech/badge/pyenv-win)](https://pepy.tech/project/pyenv-win)

- [소개](#introduction)
- [pyenv](#pyenv)
- [pyenv-win 명령어](#pyenv-win-commands)
- [설치](#설치)
- [설치 유효성 검사](#validate-installation)
- [사용법](#usage)
- [pyenv 업데이트 방법](#how-to-update-pyenv)
- [공지사항](#announcements)
- [자주 묻는 질문](#faq)
- [변경 로그](#changelog)
- [기여 방법](#how-to-contribute)
- [버그 추적 및 지원](#bug-tracker-and-support)
- [라이선스 및 저작권](#license-and-copyright)
- [저자 및 감사](#author-and-thanks)

## 소개

파이썬용 [pyenv][1]는 훌륭한 도구이지만, 루비 개발자를 위한 [rbenv][2]처럼 Windows를 직접 지원하지는 않습니다. 파이썬 개발자들의 연구와 피드백을 통해, 저는 그들이 Windows 시스템에도 유사한 기능을 원한다는 것을 알게 되었습니다.

이 프로젝트는 [rbenv-win][3]에서 포크되었고 [pyenv][1]를 위해 수정되었습니다. 현재는 많은 기여자들의 도움 덕분에 상당히 안정적입니다.

## pyenv

[pyenv][1]는 간단한 파이썬 버전 관리 도구입니다. 이를 통해 여러 버전의 파이썬을 쉽게 전환할 수 있습니다. 간단하고 방해받지 않으며, 한 가지 작업을 잘 수행하는 UNIX의 단일 목적 도구 전통을 따릅니다.

## 빠른 시작

1. PowerShell에 pyenv-win을 설치합니다.

   ```pwsh
   Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
   ```

2. PowerShell을 다시 엽니다.
3. `pyenv --version`을 실행하여 설치가 성공했는지 확인합니다.
4. `pyenv install -l`을 실행하여 pyenv-win이 지원하는 파이썬 버전 목록을 확인합니다.
5. `pyenv install <version>`을 실행하여 지원되는 버전을 설치합니다.
6. `pyenv global <version>`을 실행하여 파이썬 버전을 전역 버전으로 설정합니다.
7. 사용 중인 파이썬 버전과 해당 경로를 확인합니다.

   ```plaintext
   > pyenv version
   <version> (set by \path\to\.pyenv\pyenv-win\.python-version)
   ```

8. 파이썬이 작동하는지 확인합니다.

   ```plaintext
   > python -c "import sys; print(sys.executable)"
   \path\to\.pyenv\pyenv-win\versions\<version>\python.exe
   ```

## pyenv-win 명령어

```yml
commands     List all available pyenv commands
local        Set or show the local application-specific Python version
latest       Print the latest installed or known version with the given prefix
global       Set or show the global Python version
shell        Set or show the shell-specific Python version
install      Install 1 or more versions of Python
uninstall    Uninstall 1 or more versions of Python
update       Update the cached version DB
rehash       Rehash pyenv shims (run this after switching Python versions)
vname        Show the current Python version
version      Show the current Python version and its origin
version-name Show the current Python version
versions     List all Python versions available to pyenv
exec         Runs an executable by first preparing PATH so that the selected
Python version's `bin' directory is at the front
which        Display the full path to an executable
whence       List all Python versions that contain the given executable
```

## 설치

현재 다음 방법들을 지원하니, 편한 방법을 선택하십시오:

- [PowerShell](./installation.md#powershell) - 가장 쉬운 방법
- [Git 명령어](./installation.md#git-commands) - 기본 방법 + 수동 설정 추가
- [Pyenv-win zip](./installation.md#pyenv-win-zip) - 수동 설치
- [Python pip](./installation.md#python-pip) - 기존 사용자용
- [Chocolatey](./installation.md#chocolatey)
- [32비트 트레인 사용 방법](./installation.md#how-to-use-32-train)
  - [공지사항 확인](#announcements)

자세한 내용은 [설치](./installation.md) 페이지를 참조하십시오.

## 설치 유효성 검사

1. 명령 프롬프트를 다시 열고 `pyenv --version`을 실행합니다.
2. 이제 `pyenv`를 입력하여 사용법을 확인합니다.

"**command not found**" 오류가 발생하면 아래 메모를 확인하고 [수동으로 설정 확인](#manually-check-the-settings)을 수행하십시오.

Visual Studio Code 또는 내장 터미널이 있는 다른 IDE의 경우, 재시작하고 다시 확인하십시오.

---

### 수동으로 설정 확인

설정해야 할 환경 변수:

```plaintext
C:\Users\<replace with your actual username>\.pyenv\pyenv-win\bin
C:\Users\<replace with your actual username>\.pyenv\pyenv-win\shims
```

모든 환경 변수가 GUI를 통해 높은 우선순위로 올바르게 설정되었는지 확인하십시오:

```plaintext
This PC
   → Properties
      → Advanced system settings
         → Advanced → System Environment Variables...
            → PATH
```

**참고:** Windows 10 1905 또는 최신 버전을 실행 중인 경우, 시작 > "앱 실행 별칭 관리"에서 내장 파이썬 런처를 비활성화하고 파이썬에 대한 "앱 설치 관리자" 별칭을 꺼야 할 수도 있습니다.

## 사용법

- pyenv windows에서 지원하는 파이썬 버전 목록을 보려면: `pyenv install -l`
- 목록을 필터링하려면: `pyenv install -l | findstr 3.8`
- 파이썬 버전을 설치하려면: `pyenv install 3.5.2`
  - _참고: 일부 비자동 설치의 경우 설치 마법사가 팝업될 수 있습니다. 설치 중 마법사를 클릭해야 합니다. 옵션을 변경할 필요는 없습니다. 또는 -q를 사용하여 자동 설치를 할 수 있습니다._
  - 여러 버전을 한 번에 설치할 수도 있습니다: `pyenv install 2.4.3 3.6.8`
- 파이썬 버전을 전역 버전으로 설정하려면: `pyenv global 3.5.2`
  - 이는 로컬 버전(아래 참조)이 설정되지 않은 경우 기본적으로 사용될 파이썬 버전입니다.
  - _참고: 버전은 먼저 설치되어야 합니다._
- 파이썬 버전을 로컬 버전으로 설정하려면: `pyenv local 3.5.2`.
  - 지정된 버전은 이 폴더 내에서 `python`이 호출될 때마다 사용됩니다. 이는 명시적으로 활성화해야 하는 가상 환경과는 다릅니다.
  - _참고: 버전은 먼저 설치되어야 합니다._
- pip을 사용하여 라이브러리를 (설치/제거)하거나 버전 폴더의 파일을 수정한 후에는, `pyenv rehash`를 실행하여 새 파이썬 및 라이브러리 실행 파일용 심(shim)으로 pyenv를 업데이트해야 합니다.
  - _참고: 이 명령어는 `.pyenv` 폴더 외부에서 실행해야 합니다._
- 파이썬 버전을 제거하려면: `pyenv uninstall 3.5.2`
- 사용 중인 파이썬과 해당 경로를 보려면: `pyenv version`
- 이 시스템에 설치된 모든 파이썬 버전을 보려면: `pyenv versions`
- pyenv-win `2.64.x` 및 `2.32.x` 버전의 경우 `pyenv update` 명령을 사용하여 검색 가능한 파이썬 버전 목록을 업데이트하십시오.

## pyenv 업데이트 방법

- pip을 통해 설치된 경우
  - pyenv-win 설치 경로를 site-packages에 있는 `easy_install.pth` 파일에 추가하십시오. 이렇게 하면 pip이 pyenv-win을 설치된 것으로 인식합니다.
  - pip을 통해 업데이트를 받으십시오: `pip install --upgrade pyenv-win`
- Git을 통해 설치된 경우
  - `%USERPROFILE%\.pyenv\pyenv-win` (설치 경로)으로 이동하여 `git pull`을 실행합니다.
- zip을 통해 설치된 경우
  - 최신 zip을 다운로드하고 압축을 해제합니다.
  - `%USERPROFILE%\.pyenv\pyenv-win`으로 이동하여 `libexec` 및 `bin` 폴더를 새로 다운로드한 것으로 바꿉니다.
- 설치 프로그램을 통해 설치된 경우
  - Powershell 터미널에서 다음을 실행합니다: `&"${env:PYENV_HOME}\install-pyenv-win.ps1"`

## 공지사항

[pyenv][1] 리눅스/맥과 동기화하기 위해, pyenv-win은 이제 기본적으로 64비트 버전을 설치합니다. 이전 pyenv-win 버전과의 호환성을 지원하기 위해, 32비트 트레인(브랜치)을 별도의 릴리스로 유지합니다.

두 릴리스 모두 64비트 및 32비트 파이썬 버전을 설치할 수 있습니다. 차이점은 버전 이름에 있습니다. 예를 들면 다음과 같습니다:

- 64비트 트레인 (master), 즉 pyenv 버전 _2.64.x_

```plaintext
> pyenv install -l | findstr 3.8
....
3.8.0-win32
3.8.0
3.8.1rc1-win32
3.8.1rc1
3.8.1-win32
3.8.1
3.8.2-win32
3.8.2
3.9.0-win32
3.9.0
....
```

- 32비트 트레인, 즉 pyenv 버전 _2.32.x_

```plaintext
> pyenv install -l | findstr 3.8
....
3.8.0
3.8.0-amd64
3.8.1rc1
3.8.1rc1-amd64
3.8.1
3.8.1-amd64
3.8.2
3.8.2-amd64
....
```

파이썬 버전 2.4 미만에 대한 지원은 해당 설치 프로그램이 2.4 이후 버전처럼 "깔끔하게" 설치되지 않으며, 대부분의 환경에서 현재 사용되지 않거나 지원되지 않으므로 중단되었습니다.

## 자주 묻는 질문

[자주 묻는 질문](./faq.md) 페이지를 참조하십시오.

## 변경 로그

[변경 로그](./changelog.md) 페이지를 참조하십시오.

## 기여 방법

- 프로젝트를 포크하고 로컬에 복제하십시오.
- 업스트림 원격 저장소를 생성하고 브랜치하기 전에 로컬 복사본을 동기화하십시오.
- 각 개별 작업에 대해 브랜치를 생성하십시오. 테스트 케이스를 작성하는 것이 좋은 습관입니다.
- 작업을 수행하고, 좋은 커밋 메시지를 작성하며, CONTRIBUTING 파일이 있다면 읽어보십시오.
- `tests\bat_files\test_install.bat` 및 `tests\bat_files\test_uninstall.bat`을 실행하여 변경 사항을 테스트하십시오.
- 원본 저장소에 푸시하십시오.
- GitHub에 새 Pull Request를 생성하십시오.

## 버그 추적 및 지원

- pyenv-win에 대한 제안, 버그 보고서 또는 불편 사항은 [GitHub 버그 추적기](https://github.com/pyenv-win/pyenv-win/issues)를 통해 보고하십시오.

## 라이선스 및 저작권

- pyenv-win은 [MIT](http://opensource.org/licenses/mit-license.php) _2019_ 라이선스가 적용됩니다.

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 저자 및 감사

pyenv-win은 [Kiran Kumar Kotari](https://github.com/kirankotari)와 [기여자들](https://github.com/pyenv-win/pyenv-win/graphs/contributors)에 의해 개발되었습니다.
최신 주요 릴리스를 위해 인내해주신 모든 기여자 및 지지자들에게 감사드립니다.

[1]: https://github.com/pyenv/pyenv
[2]: https://github.com/rbenv/rbenv
[3]: https://github.com/nak1114/rbenv-win
