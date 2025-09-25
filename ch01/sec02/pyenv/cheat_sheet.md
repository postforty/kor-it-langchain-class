# pyenv-win 핵심 치트시트

## 1. PowerShell을 이용한 설치

```pwsh
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
```

- PowerShell을 **관리자 권한**으로 실행해야 할 수 있다.
- 스크립트 실행 오류 시 파워쉘에서 추가 명령어 실행:
  ```pwsh
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine
  ```
- 설치 후, PowerShell을 재시작하고 아래 명령어로 정상 설치 확인:
  ```pwsh
  pyenv --version
  ```

## 2. 환경 변수 설정

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

## 3. pyenv-win 주요 명령어

- 설치 가능한 파이썬 버전 목록 확인:
  ```
  pyenv install -l
  ```
- 파이썬 버전 설치:
  ```
  pyenv install <version>
  ```
- 전역 파이썬 버전 설정:
  ```
  pyenv global <version>
  ```
- 현재 사용 중인 파이썬 버전 확인:
  ```
  pyenv version
  ```
- 설치된 모든 파이썬 버전 목록:
  ```
  pyenv versions
  ```
- 파이썬 버전 제거:
  ```
  pyenv uninstall <version>
  ```
- pip 등으로 라이브러리 설치/제거 후 shim 갱신:
  ```
  pyenv rehash
  ```

## 4. PowerShell을 이용한 삭제 방법

1. 환경 변수 제거

   - 시스템 속성 → 고급 → 환경 변수에서 PYENV, PYENV_HOME, PYENV_ROOT 관련 경로 삭제
   - 시스템 속성 → 고급 → 환경 변수에서 Path 편집 → C:\Users\<사용자명>\.pyenv\pyenv-win\bin, C:\Users\<사용자명>\.pyenv\pyenv-win\shims 경로 삭제

2. pyenv 폴더 삭제

   - `C:\Users\<사용자이름>\.pyenv` 폴더를 삭제

3. 삭제 확인
   - PowerShell에서 아래 명령어로 pyenv가 제거되었는지 확인
     ```
     pyenv --version
     python --version
     ```
   - 완전히 제거되지 않았다면 재부팅 후 다시 확인
