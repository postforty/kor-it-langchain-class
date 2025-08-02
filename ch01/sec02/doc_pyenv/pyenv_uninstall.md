# 윈도우에서 pyenv-win 삭제 방법

## 1. 환경 변수 제거

- 시스템 속성 -> 고급 탭 -> 환경 변수 버튼 클릭
- '사용자 변수'와 '시스템 변수'에서 pyenv와 관련된 PATH를 제거한다. 일반적으로 `PYENV_HOME`, `PYENV_ROOT`, `%PYENV_HOME%\bin`, `%PYENV_HOME%\shims`와 같은 변수들이 해당된다.
- 변수 선택 후 '삭제' 버튼을 클릭하고, 모든 변경 사항을 '확인'을 눌러 저장한다.

## 2. pyenv 폴더 삭제

- pyenv가 설치된 폴더를 직접 삭제한다. 일반적으로 `C:\Users\<사용자 이름>\.pyenv` 또는 `C:\Program Files\pyenv`와 같은 경로에 위치한다.
- 이 폴더를 삭제하면 pyenv에 의해 설치된 모든 파이썬 버전도 함께 삭제된다.

## 3. 파이썬 설치 확인

- 명령 프롬프트(CMD)나 PowerShell을 열어 `python --version` 또는 `pyenv --version`을 입력하여 pyenv가 완전히 제거되었는지 확인한다.
- 만약 제거되지 않았다면 1번과 2번 과정을 다시 확인하고 재부팅을 시도해 본다.
