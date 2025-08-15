```bash
# 현재 디렉터리에 초기화 진행
uv init .

# .venv 폴더가 생성됨
uv venv

# 기본 파이썬 버전 설치 (uv가 권장하는 최신 버전)
uv python install

# 설치 버전 목록 확인
uv python list

# 설치 버전 확인
uv run python --version 

# 인터프리터 실행
uv run python

# 파이썬 코드 실행
uv run example.py
```