# 설치

> 원문: <https://github.com/pyenv-win/pyenv-win/blob/master/docs/installation.md#powershell>

현재 다음 방법들을 지원하니, 편한 방법을 선택하십시오:

- [PowerShell](#powershell) - 가장 쉬운 방법
- [Git 명령어](#git-commands) - 기본 방법 + 수동 설정 추가
- [Pyenv-win zip](#pyenv-win-zip) - 수동 설치
- [Python pip](#python-pip) - 기존 사용자용
- [Chocolatey](#chocolatey)
- [32비트 트레인 사용 방법](#how-to-use-32-train)
  - [공지사항 확인](./pyenv_win.md#announcements)

만세! 완료되면 다음 단계는 [설치 유효성 검사](./pyenv_win.md#validate-installation)입니다.

_참고:_ Windows 10 1905 또는 최신 버전을 실행 중인 경우, 시작 > "앱 실행 별칭 관리"에서 내장 파이썬 런처를 비활성화하고 파이썬에 대한 "앱 설치 관리자" 별칭을 꺼야 할 수도 있습니다.

---

## **PowerShell**

pyenv-win을 설치하는 가장 쉬운 방법은 PowerShell 터미널에서 다음 설치 명령을 실행하는 것입니다:

```pwsh
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
```

아래와 같은 **UnauthorizedAccess** 오류가 발생하면, "관리자 권한으로 실행" 옵션으로 Windows PowerShell을 시작하고 `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine`을 실행한 다음, 위에 언급된 설치 명령을 다시 실행하십시오.

```plaintext
& : File C:\Users\kirankotari\install-pyenv-win.ps1 cannot be loaded because running scripts is disabled on this system. For
more information, see about_Execution_Policies at https:/go.microsoft.com/fwlink/?LinkID=135170.
At line:1 char:173
+ ... n.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
+ ~~~~~~~~~~~~~~~~~~~~~~~~~
+ CategoryInfo          : SecurityError: (:) [], PSSecurityException
+ FullyQualifiedErrorId : UnauthorizedAccess
```

'디지털 서명' 또는 '보안 경고'에 대한 자세한 내용은 다음 이슈 [#332](https://github.com/pyenv-win/pyenv-win/issues/332)를 참조하십시오.

설치가 완료되었습니다!

[pyenv로 돌아가기](./pyenv_win.md#installation)

---

## **Git 명령어**

pyenv-win을 설치하는 기본 방법이며, git 명령어가 필요하므로 Windows용 git/git-bash를 설치해야 합니다.

PowerShell 또는 Git Bash를 사용하는 경우 `%USERPROFILE%` 대신 `$HOME`을 사용하십시오.

명령 프롬프트를 사용하여 git 클론: `git clone https://github.com/pyenv-win/pyenv-win.git "%USERPROFILE%\.pyenv"`

[시스템 설정 추가](#add-system-settings) 단계

_참고:_ 위에 언급된 링크를 확인하는 것을 잊지 마십시오. 완료를 위한 최종 단계가 포함되어 있습니다.

설치가 완료되었습니다!

[pyenv로 돌아가기](./pyenv_win.md#installation)

---

## **Pyenv-win zip**

pyenv-win 수동 설치 단계

PowerShell 또는 Git Bash를 사용하는 경우 `%USERPROFILE%` 대신 `$HOME`을 사용하십시오.

1. [pyenv-win.zip](https://github.com/pyenv-win/pyenv-win/archive/master.zip) 다운로드

2. `.pyenv` 디렉토리가 없으면 명령 프롬프트를 사용하여 생성: `mkdir %USERPROFILE%/.pyenv`

3. 파일들을 `%USERPROFILE%\.pyenv\`로 압축 해제 및 이동

4. `%USERPROFILE%\.pyenv\pyenv-win` 아래에 `bin` 폴더가 있는지 확인

[시스템 설정 추가](#add-system-settings) 단계

_참고:_ 위에 언급된 링크를 확인하는 것을 잊지 마십시오. 완료를 위한 최종 단계가 포함되어 있습니다.

설치가 완료되었습니다!

[pyenv로 돌아가기](./pyenv_win.md#installation)

---

## **Python pip**

기존 파이썬 사용자용

### 명령 프롬프트

`pip install pyenv-win --target %USERPROFILE%\\.pyenv`

위 명령에서 오류가 발생하면 다음을 대신 사용하십시오 ([#303](https://github.com/pyenv-win/pyenv-win/issues/303)):

`pip install pyenv-win --target %USERPROFILE%\\.pyenv --no-user --upgrade`

### PowerShell 또는 Git Bash

위와 동일한 명령을 사용하되, `%USERPROFILE%`을 `$HOME`으로 바꾸십시오.

### 최종 단계

[시스템 설정 추가](#add-system-settings)로 진행하십시오.

그러면 설치가 완료될 것입니다!

[pyenv로 돌아가기](./pyenv_win.md#installation)

---

## **Chocolatey**

이것은 설치를 위해 choco 명령어가 필요합니다. [설치 링크](https://chocolatey.org/install)

Chocolatey 명령어 `choco install pyenv-win`

Chocolatey 페이지: [pyenv-win](https://chocolatey.org/packages/pyenv-win)

설치가 완료되었습니다!

설치 유효성 검사

[pyenv로 돌아가기](./pyenv_win.md#installation)

---

## **시스템 설정 추가**

여기서는 PowerShell을 사용하는 것이 쉬운 방법입니다.

1. PYENV, PYENV_HOME 및 PYENV_ROOT를 환경 변수에 추가

   ```pwsh
   [System.Environment]::SetEnvironmentVariable('PYENV',$env:USERPROFILE + "\.pyenv\pyenv-win\","User")

   [System.Environment]::SetEnvironmentVariable('PYENV_ROOT',$env:USERPROFILE + "\.pyenv\pyenv-win\","User")

   [System.Environment]::SetEnvironmentVariable('PYENV_HOME',$env:USERPROFILE + "\.pyenv\pyenv-win\","User")
   ```

2. 이제 pyenv 명령어에 접근하기 위해 다음 경로들을 사용자 PATH 변수에 추가

   ```pwsh
   [System.Environment]::SetEnvironmentVariable('path', $env:USERPROFILE + "\.pyenv\pyenv-win\bin;" + $env:USERPROFILE + "\.pyenv\pyenv-win\shims;" + [System.Environment]::GetEnvironmentVariable('path', "User"),"User")
   ```

어떤 이유로든 PowerShell 명령을 실행할 수 없는 경우(조직 관리 장치에서 발생할 가능성 있음), Windows 검색 창에 "계정용 환경 변수"를 입력하고 환경 변수 대화 상자를 여십시오.
시스템 변수 섹션(하단)에 이 세 가지 새 변수를 생성해야 합니다. 사용자 이름을 `my_pc`라고 가정해 봅시다.
|변수|값|
|---|---|
|PYENV|C:\Users\my_pc\.pyenv\pyenv-win\
|PYENV_HOME|C:\Users\my_pc\.pyenv\pyenv-win\
|PYENV_ROOT|C:\Users\my_pc\.pyenv\pyenv-win\

그리고 사용자 변수 `Path`에 두 줄을 더 추가하십시오.

```
C:\Users\my_pc\.pyenv\pyenv-win\bin
C:\Users\my_pc\.pyenv\pyenv-win\shims
```

설치가 완료되었습니다. 만세!
[pyenv로 돌아가기](./pyenv_win.md#installation)

## **Git BASH 사용법**

Git BASH 내에서 다음을 실행하십시오:

```sh
echo 'export PATH="$HOME/.pyenv/pyenv-win/shims:$PATH"' >> ~/.bash_profile
echo 'export PATH="$HOME/.pyenv/pyenv-win/bin:$PATH"' >> ~/.bash_profile
```

새 터미널을 열고 `pyenv --version`이 작동하는지 확인하십시오.

---

## **32비트 트레인 사용 방법**

- **Git 사용**
  1. 32비트 트레인의 전제 조건은 [Git을 사용하여 pyenv-win 설치](#git-commands)입니다.
  2. .pyenv 디렉토리로 이동: `cd %USERPROFILE%\.pyenv`
  3. `git checkout -b 32bit-train origin/32bit-train` 실행
  4. `pyenv --version`을 실행하면 *2.32.x*가 표시되어야 합니다.
- **pip 사용**
  1. `pip install pyenv-win==2.32.x --target %USERPROFILE%\.pyenv` 실행
  2. [시스템 설정 추가](#add-system-settings) 단계
- **Zip 사용**
  1. [pyenv-win.zip](https://github.com/pyenv-win/pyenv-win/archive/32bit-train.zip) 다운로드
  2. [Pyenv-win zip](#pyenv-win-zip)의 2단계 따르기
  3. [시스템 설정 추가](#add-system-settings) 단계

[pyenv로 돌아가기](./pyenv_win.md#installation)
