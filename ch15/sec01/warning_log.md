## 스트림릿 구동시 발생할 수 있는 로그에 대한 설명

```bash
\ch15\sec01>uv run streamlit run upstage_pdf_quiz_chatbot.py

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.10.115:8501

WARNING: All log messages before absl::InitializeLog() is called are written to STDERR
E0000 00:00:1758504601.081659   11204 alts_credentials.cc:93] ALTS creds ignored. Not running on GCP and untrusted ALTS is not enabled.
```

제시된 로그는 `uv run streamlit` 명령어를 실행했을 때 발생하는 경고 메시지입니다. 이 경고는 애플리케이션의 정상적인 작동을 방해하는 심각한 오류가 아니라, 특정 환경 설정과 관련된 정보성 메시지입니다.

### 경고 메시지 분석

---

#### 1. `WARNING: All log messages before absl::InitializeLog() is called are written to STDERR`

- **absl::InitializeLog()**: 이 함수는 Google에서 개발한 C++ 라이브러리인 Abseil에 속하며, 애플리케이션의 **로깅 시스템을 초기화**하는 역할을 합니다. 로깅 시스템은 애플리케이션의 실행 상태, 디버깅 정보, 오류 등을 기록하는 데 사용됩니다.
- **STDERR**: 표준 에러(Standard Error) 스트림으로, 일반적으로 오류 메시지나 경고를 출력하는 데 사용됩니다.

이 경고는 로깅 시스템이 완전히 초기화되기 전에 발생한 모든 로그 메시지가 기본 에러 출력 스트림인 `STDERR`로 보내졌다는 의미입니다. 이는 정상적인 로깅 시스템이 활성화되기 전의 일시적인 현상으로, **애플리케이션의 실행 흐름에 영향을 주지 않습니다.**

---

#### 2. `E0000 00:00:1758504601.081659 11204 alts_credentials.cc:93] ALTS creds ignored. Not running on GCP and untrusted ALTS is not enabled.`

- **ALTS (Application Layer Transport Security)**: 구글 클라우드 플랫폼(GCP) 환경에서 통신 보안을 강화하기 위해 사용되는 전송 계층 보안 프로토콜입니다.
- **ALTS creds (credentials)**: ALTS 인증 정보를 의미합니다.
- **ignored**: 무시되었다는 뜻입니다.

이 경고는 애플리케이션이 **GCP 환경에서 실행되고 있지 않기 때문에**, **ALTS 관련 인증 정보가 무시되었다**는 것을 나타냅니다. ALTS는 GCP 환경에 특화된 기술이므로, 로컬 환경에서 실행 중일 때는 사용할 필요가 없습니다.

---

### 결론

이 두 경고 메시지는 모두 **시스템의 정상적인 동작을 방해하지 않는 정보성 메시지**입니다.

- 첫 번째 경고는 단순히 로그 시스템 초기화 시점에 대한 기술적인 메시지입니다.
- 두 번째 경고는 GCP와 관련이 없는 로컬 환경에서 애플리케이션을 실행하고 있음을 나타냅니다.

따라서 이 경고들은 **무시해도 무방**하며, 애플리케이션 (`upstage_pdf_quiz_chatbot.py`)은 의도한 대로 정상적으로 동작할 것입니다.
