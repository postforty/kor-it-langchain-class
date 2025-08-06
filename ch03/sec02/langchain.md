# LangChain: AI 서비스 개발의 만능 도구!

## 1. LangChain이란 무엇인가?

LangChain은 대규모 언어 모델(LLM)을 활용하여 복잡하고 지능적인 애플리케이션을 개발할 수 있도록 돕는 프레임워크입니다. LLM의 잠재력을 최대한 끌어내어 실제 서비스에 적용하는 과정을 간소화하고, 개발 효율성을 높이는 데 중점을 둡니다. "AI 서비스 개발의 만능 도구"라고 불리는 이유는 단순히 LLM을 호출하는 것을 넘어, 여러 구성 요소를 체인처럼 연결하고 상호 작용하게 함으로써, 더 정교하고 다재다능한 AI 솔루션을 구축할 수 있게 해주기 때문입니다.

## 2. 단순 LLM 모델 사용의 한계

기존에는 OpenAI의 GPT-3나 Google의 PaLM 2와 같은 LLM API를 직접 호출하여 원하는 결과물을 얻는 방식이 일반적이었습니다. 이 방식은 간단한 질문-답변, 텍스트 요약 등 단일 목적의 작업을 수행할 때는 효과적입니다.

하지만 복잡한 AI 서비스를 개발할 때는 여러 가지 한계에 부딪히게 됩니다. 예를 들어:

- **여러 단계의 처리:** 사용자의 질문을 이해하고, 외부 데이터를 검색하고, 다시 질문에 답변하는 등 여러 단계의 논리가 필요한 경우, 각 단계를 수동으로 연결하고 관리해야 합니다.
- **외부 데이터 연동:** 실시간 정보, 기업 내부 문서 등 LLM이 학습하지 않은 최신 데이터나 특정 도메인 지식을 활용하려면 LLM과 외부 데이터베이스, API 등을 연동하는 복잡한 과정이 필요합니다.
- **메모리 관리:** 챗봇과 같이 대화의 맥락을 기억해야 하는 서비스의 경우, 이전 대화 내용을 LLM에 지속적으로 전달해야 하는데, 이를 직접 관리하는 것은 번거롭고 오류 발생 가능성이 높습니다.
- **도구 사용:** LLM이 특정 작업을 수행하기 위해 외부 도구(예: 계산기, 웹 검색 엔진)를 사용하도록 하려면, LLM의 응답을 파싱하고 적절한 도구를 호출하는 로직을 직접 구현해야 합니다.

이러한 문제들은 개발 시간을 늘리고 코드의 복잡성을 증가시켜, LLM 기반 서비스 개발의 진입 장벽을 높이는 요인이 됩니다.

## 3. LangChain, 왜 필요한가? (문제 해결사로서의 LangChain)

LangChain은 위에서 언급된 단순 LLM 사용의 한계점들을 극복하기 위해 등장했습니다. LangChain은 LLM 기반 애플리케이션 개발에 필요한 다양한 구성 요소를 모듈화하고 표준화하여 제공함으로써, 개발자가 복잡한 로직을 직접 구현할 필요 없이 효율적으로 서비스를 구축할 수 있도록 돕습니다.

LangChain의 주요 개념들은 다음과 같습니다:

- **Models:** 다양한 LLM 모델(OpenAI, Hugging Face 등)과의 인터페이스를 제공합니다.
- **Prompts:** LLM에 전달할 프롬프트를 효과적으로 생성하고 관리할 수 있도록 템플릿 기능을 제공합니다.
- **Chains:** 여러 LLM 호출이나 다른 구성 요소를 순차적으로 연결하여 복잡한 워크플로우를 생성합니다. 예를 들어, 질문을 요약하고, 외부 정보를 검색한 후, 최종 답변을 생성하는 과정을 하나의 체인으로 구성할 수 있습니다.
- **Retrieval:** 외부 데이터를 검색하고 LLM이 활용할 수 있는 형태로 변환하는 기능을 제공합니다. 벡터 데이터베이스 연동, 문서 로더 등이 여기에 해당합니다.
- **Agents:** LLM이 스스로 판단하여 어떤 도구를 사용하고 어떤 액션을 취할지 결정하도록 돕습니다. 이는 LLM이 외부 환경과 상호작용하며 더욱 능동적인 작업을 수행할 수 있게 합니다.
- **Memory:** 이전 대화 내용을 기억하고 LLM에 전달하여, 대화의 맥락을 유지하고 자연스러운 다중 턴 대화를 가능하게 합니다.

## 4. LangChain vs. 단순 LLM 모델: 실용적인 비교

이제 실제 코드 예시를 통해 단순 LLM 사용 방식과 LangChain 사용 방식의 차이를 비교해 보겠습니다. 여기서는 대화의 맥락을 기억하는 챗봇을 만드는 시나리오를 가정합니다.

### 4.1. 단순 LLM API 사용 (대화 맥락 기억 안 됨)

`ch02/sec03/01_single_turn.py` 예시는 다음과 같이 LLM API를 직접 호출하는 방식입니다. 이 방식은 이전 대화 내용을 기억하지 못하므로, 사용자가 자신의 이름을 알려주고 다시 물어보면 AI는 이를 기억하지 못합니다.

```python
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

gemini_api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=gemini_api_key)

system_instruction = "너는 사용자를 도와주는 상담사야."

while True:
    user_input = input("사용자: ")

    if user_input == "exit":
        break

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            temperature=0.9,
            system_instruction=system_instruction),
        contents=user_input
    )
    print("AI: " + response.text)
```

**실행 결과 예시:**

```
사용자: 안녕, 내 이름은 김일남이야.
AI: 안녕하세요, 김일남님. 만나 뵙게 되어 반갑습니다. 어떤 일로 저를 찾아오셨나요? 편하게 말씀해주세요. 제가 도울 수 있는 부분이 있다면 최선을 다해 돕겠습니다.

사용자: 내 이름이 뭘까?
AI: 음, 제가 당신의 이름을 알 수 있는 방법은 없네요. 당신이 알려주시면 그때부터는 당신을 그렇게 부를 수 있어요. 당신의 이름이 무엇인가요?
```

위 예시에서 볼 수 있듯이, LLM은 이전 대화에서 "김일남"이라는 이름을 들었음에도 불구하고 이를 기억하지 못하고 다시 묻는 것을 알 수 있습니다. 이는 매번 새로운 요청으로 간주되기 때문입니다.

### 4.2. 네이티브 LLM Chat API 사용 vs. LangChain (대화 맥락 기억 및 확장성)

`ch02/sec03/02_multi_turn.py` 예시에서는 Google Gemini API의 `client.chats.create`를 사용하여 다중 턴 대화를 구현했습니다. 이 방법은 LLM 제공사(Google Gemini)가 자체적으로 제공하는 채팅 기능을 활용하여 이전 대화 기록을 관리하고 대화의 맥락을 유지합니다. 즉, 이 방식 자체는 대화 맥락을 기억하는 기능을 제공합니다.

그렇다면 LangChain은 어떤 이점을 제공할까요? LangChain은 이러한 `Memory` 개념을 `ConversationBufferMemory`와 `ConversationChain`을 통해 **LLM 제공사에 독립적이고 더욱 추상화된 방식으로** 쉽게 사용할 수 있도록 돕습니다. 이는 단일 LLM에 종속되지 않고 다양한 LLM 모델과 호환되며, 더 복잡한 체인 구성, 외부 도구 및 데이터와의 통합 등 **확장성 있는 AI 서비스 개발 시 강력한 이점을 제공**합니다.

아래는 LangChain을 사용하여 대화 맥락을 기억하는 간단한 챗봇을 구현하는 예시입니다.

```python
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API 키 설정
gemini_api_key = os.getenv("GEMINI_API_KEY")

# LangChain을 사용하여 Gemini 모델 초기화
llm = ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=gemini_api_key)

# 대화 기록을 저장할 메모리 설정
memory = ConversationBufferMemory()

# ConversationChain 설정: LLM과 메모리를 연결
conversation = ConversationChain(
    llm=llm,
    memory=memory,
    verbose=True # 대화 과정을 자세히 볼 수 있습니다.
)

print("AI 챗봇과 대화를 시작하세요! (종료하려면 'exit'를 입력하세요)")

while True:
    user_input = input("사용자: ")
    if user_input.lower() == 'exit':
        print("대화를 종료합니다.")
        break

    # 사용자 입력에 대한 응답 생성 (이전 대화 기록이 자동으로 반영됨)
    response = conversation.predict(input=user_input)
    print("AI:", response)

    # (선택 사항) 현재 대화 기록 확인
    # print("\n--- 현재 대화 기록 ---")
    # print(memory.buffer)
    # print("-----------------------\n")
```

**LangChain 예시 실행을 위한 추가 설정:**

이 코드를 실행하려면 `langchain-google-genai` 라이브러리를 설치해야 합니다.

```bash
uv add langchain-google-genai
```

**실행 결과 예시:**

```
AI 챗봇과 대화를 시작하세요! (종료하려면 'exit'를 입력하세요)
사용자: 안녕, 내 이름은 김일남이야.
> Entering new ConversationChain chain...
Prompt after formatting:
The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context.

Current conversation:

Human: 안녕, 내 이름은 김일남이야.
AI: 안녕하세요, 김일남님! 만나 뵙게 되어 반갑습니다. 무엇을 도와드릴까요?
> Finished chain.
AI: 안녕하세요, 김일남님! 만나 뵙게 되어 반갑습니다. 무엇을 도와드릴까요?

사용자: 내 이름이 뭘까?
> Entering new ConversationChain chain...
Prompt after formatting:
The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context.

Current conversation:
Human: 안녕, 내 이름은 김일남이야.
AI: 안녕하세요, 김일남님! 만나 뵙게 되어 반갑습니다. 무엇을 도와드릴까요?
Human: 내 이름이 뭘까?
AI: 김일남님이시죠! 만나뵙게 되어 반갑습니다. 혹시 다른 궁금한 점이 있으실까요?
> Finished chain.
AI: 김일남님이시죠! 만나뵙게 되어 반갑습니다. 혹시 다른 궁금한 점이 있으실까요?

사용자: exit
대화를 종료합니다.
```

LangChain을 사용하면 `ConversationBufferMemory`가 이전 대화 기록을 자동으로 저장하고, `ConversationChain`이 이를 LLM 프롬프트에 포함시켜 줌으로써, LLM이 대화의 맥락을 이해하고 일관성 있는 답변을 생성할 수 있게 됩니다. `verbose=True` 옵션을 통해 LangChain이 내부적으로 어떻게 프롬프트를 구성하는지 확인할 수 있어 학습에 도움이 됩니다.

### 4.3. 비교를 통해 얻을 수 있는 결론

- **단순 LLM API:** 단일 턴 질의응답에는 적합하지만, 대화의 맥락을 유지하려면 개발자가 직접 복잡한 로직을 구현해야 합니다.
- **네이티브 LLM Chat API (예: `client.chats.create`):** LLM 제공사가 자체적으로 대화 기록 관리를 제공하여 다중 턴 대화가 가능합니다. 이는 특정 LLM에 최적화된 방법일 수 있습니다.
- **LangChain:** `Memory`, `Chain`과 같은 추상화된 구성 요소를 제공하여, **LLM 제공사에 독립적으로** 대화 맥락 관리, 여러 단계의 처리, 외부 도구 연동 등을 훨씬 쉽고 효율적으로 구현할 수 있도록 돕습니다. 이를 통해 개발자는 LLM 애플리케이션의 핵심 로직에 집중하고, **다양한 LLM 모델을 유연하게 전환하며 확장 가능한 서비스를 구축**할 수 있습니다.

## 5. 결론: LangChain과 함께하는 AI 서비스 개발의 미래

LangChain은 LLM의 강력한 기능을 실제 서비스에 통합하는 과정을 혁신적으로 단순화합니다. 개발자는 LangChain을 통해 복잡한 LLM 워크플로우를 쉽게 구성하고, 외부 데이터 및 도구와 연동하며, 대화 맥락을 유지하는 등, 기존에는 많은 노력과 복잡한 코드를 필요로 했던 기능들을 효율적으로 구현할 수 있습니다.

LangChain은 여러분이 LLM 기반의 챗봇, 지식 기반 Q&A 시스템, 콘텐츠 생성 도구 등 다양한 AI 서비스를 더욱 빠르고 쉽게 개발할 수 있도록 지원하며, AI 서비스 개발의 새로운 가능성을 열어줄 것입니다.
