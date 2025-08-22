# LangChain을 사용하는 이유?

> 원문: <https://python.langchain.com/docs/concepts/why_langchain/>

`langchain` 파이썬 패키지와 LangChain 회사의 목표는 개발자가 추론하는 애플리케이션을 가능한 한 쉽게 구축할 수 있도록 하는 것이다. LangChain은 원래 단일 오픈소스 패키지로 시작했지만, 회사와 전체 생태계로 발전했다. 이 페이지에서는 LangChain 생태계 전체에 대해 설명한다. LangChain 생태계 내의 대부분의 구성 요소는 단독으로 사용할 수 있다. 따라서 특정 구성 요소에 특히 관심이 있지만 다른 구성 요소에는 관심이 없다면 전혀 문제가 없다! 자신의 사용 사례에 가장 적합한 구성 요소를 선택하여 사용하라!

## 기능

LangChain이 해결하고자 하는 몇 가지 주요 요구 사항은 다음과 같습니다:

1.  **표준화된 구성 요소 인터페이스:** AI 애플리케이션을 위한 [모델](/docs/integrations/chat/) 및 [관련 구성 요소](/docs/integrations/vectorstores/)의 수가 증가함에 따라 개발자가 학습하고 사용해야 하는 다양한 API가 생겨났다. 이러한 다양성은 개발자가 애플리케이션을 구축할 때 공급자 간을 전환하거나 구성 요소를 결합하는 것을 어렵게 만들 수 있다. LangChain은 주요 구성 요소에 대한 표준 인터페이스를 제공하여 공급자 간의 전환을 쉽게 만든다.

2.  **오케스트레이션:** 애플리케이션이 여러 구성 요소와 모델을 결합하여 더욱 복잡해짐에 따라, [이러한 요소를 제어 흐름으로 효율적으로 연결하여](/posts/2023-06-23-agent/) [다양한 작업을 수행해야 할 필요성](/article/generative-ais-act-o1/)이 커지고 있다. [오케스트레이션](<https://en.wikipedia.org/wiki/Orchestration_(computing)>)은 이러한 애플리케이션을 구축하는 데 중요한다.

3.  **관찰 가능성 및 평가:** 애플리케이션이 복잡해질수록 내부에서 어떤 일이 일어나는지 이해하기가 점점 더 어려워진다. 또한, 개발 속도는 [선택의 역설](https://en.wikipedia.org/wiki/Paradox_of_choice)로 인해 제한될 수 있다. 예를 들어, 개발자는 프롬프트를 어떻게 엔지니어링해야 하는지 또는 어떤 LLM이 정확도, 대기 시간 및 비용의 균형을 가장 잘 맞추는지 궁금해하는 경우가 많다. [관찰 가능성](https://en.wikipedia.org/wiki/Observability) 및 평가는 개발자가 애플리케이션을 모니터링하고 이러한 유형의 질문에 자신감을 가지고 빠르게 답변하는 데 도움이 될 수 있다.

## 표준화된 구성 요소 인터페이스

LangChain은 많은 AI 애플리케이션의 중심이 되는 구성 요소에 대한 공통 인터페이스를 제공한다. 예를 들어, 모든 [채팅 모델](/docs/concepts/chat_models/)은 [BaseChatModel](https://python.langchain.com/api_reference/core/language_models/langchain_core.language_models.chat_models.BaseChatModel.html) 인터페이스를 구현한다. 이는 [도구 호출](/docs/concepts/tool_calling/) 및 [구조화된 출력](/docs/concepts/structured_outputs/)과 같이 중요하지만 종종 공급자별 기능을 지원하는 방식으로 채팅 모델과 상호 작용하는 표준 방식을 제공한다.

### 예시1: 채팅 모델

많은 [모델 공급자](/docs/concepts/chat_models/)는 많은 애플리케이션([에이전트](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/) 등)에 중요한 기능인 [도구 호출](/docs/concepts/tool_calling/)을 지원하며, 개발자가 특정 스키마와 일치하는 모델 응답을 요청할 수 있도록 한다. 각 공급자의 API는 다르다. LangChain의 [채팅 모델](/docs/concepts/chat_models/) 인터페이스는 [도구 호출](/docs/concepts/tool_calling/)을 지원하기 위해 [도구](/docs/concepts/tools/)를 모델에 바인딩하는 공통 방법을 제공한다.

```python
# Tool creation
tools = [my_tool]
# Tool binding
model_with_tools = model.bind_tools(tools)
```

마찬가지로, 모델이 [구조화된 출력](/docs/concepts/structured_outputs/)을 생성하도록 하는 것은 매우 일반적인 사용 사례이다. 공급자는 [JSON 모드 또는 도구 호출](https://platform.openai.com/docs/guides/structured-outputs)을 포함하여 이를 위한 다양한 접근 방식을 다른 API로 지원한다. LangChain의 [채팅 모델](/docs/concepts/chat_models/) 인터페이스는 `with_structured_output()` 메서드를 사용하여 구조화된 출력을 생성하는 공통 방법을 제공한다.

```python
# Define schema
schema = ...
# Bind schema to model
model_with_structure = model.with_structured_output(schema)
```

### 예시2: 리트리버

[RAG](/docs/concepts/rag/) 및 LLM 애플리케이션 구성 요소의 맥락에서 LangChain의 [리트리버](/docs/concepts/retrievers/) 인터페이스는 다양한 유형의 데이터 서비스 또는 데이터베이스(예: [벡터 스토어](/docs/concepts/vectorstores/) 또는 데이터베이스)에 연결하는 표준 방법을 제공한다. 리트리버의 기본 구현은 연결하는 데이터 스토어 또는 데이터베이스 유형에 따라 다르지만, 모든 리트리버는 [실행 가능한 인터페이스](/docs/concepts/runnables/)를 구현하므로 공통적인 방식으로 호출할 수 있다.

```python
documents = my_retriever.invoke("What is the meaning of life?")
```

## 오케스트레이션

개별 구성 요소에 대한 표준화는 유용하지만, 개발자는 구성 요소를 더 복잡한 애플리케이션으로 *결합*하기를 점점 더 원하고 있다. 이는 [오케스트레이션](<https://en.wikipedia.org/wiki/Orchestration_(computing)>)의 필요성을 동기 부여한다. 이 오케스트레이션 계층이 지원해야 하는 LLM 애플리케이션의 몇 가지 공통적인 특징은 다음과 같다:

- **복잡한 제어 흐름:** 애플리케이션에 순환(예: 조건이 충족될 때까지 반복되는 루프)과 같은 복잡한 패턴이 필요한다.
- **[지속성](https://langchain-ai.github.io/langgraph/concepts/persistence/):** 애플리케이션은 [단기 및/또는 장기 메모리](https://langchain-ai.github.io/langgraph/concepts/memory/)를 유지해야 한다.
- **[휴먼-인-더-루프](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/):** 애플리케이션에 사람의 상호 작용(예: 특정 단계 일시 중지, 검토, 편집, 승인)이 필요한다.

복잡한 애플리케이션을 위한 구성 요소를 오케스트레이션하는 권장 방법은 [LangGraph](https://langchain-ai.github.io/langgraph/concepts/high_level/)이다. LangGraph는 애플리케이션의 흐름을 노드 및 에지 집합으로 표현하여 개발자에게 높은 수준의 제어 기능을 제공하는 라이브러리이다. LangGraph는 [지속성](https://langchain-ai.github.io/langgraph/concepts/persistence/), [휴먼-인-더-루프](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/), [메모리](https://langchain-ai.github.io/langgraph/concepts/memory/) 및 기타 기능에 대한 내장 지원을 제공한다. 특히 [에이전트](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/) 또는 [다중 에이전트](https://langchain-ai.github.io/langgraph/concepts/multi_agent/) 애플리케이션을 구축하는 데 매우 적합하다. 중요하게도 개별 LangChain 구성 요소는 LangGraph 노드로 사용될 수 있지만, LangChain 구성 요소를 **사용하지 않고도** LangGraph를 사용할 수도 있다.

> **추가 자료**
> LangGraph를 사용하여 복잡한 애플리케이션을 구축하는 방법에 대해 자세히 알아보려면 무료 강좌인 [LangGraph 소개](https://academy.langchain.com/courses/intro-to-langgraph)를 확인하십시오.

## 관찰 가능성 및 평가

AI 애플리케이션 개발 속도는 선택의 역설로 인해 고품질 평가에 의해 종종 제한된다. 개발자는 프롬프트를 어떻게 엔지니어링해야 하는지 또는 어떤 LLM이 정확도, 대기 시간 및 비용의 균형을 가장 잘 맞추는지 궁금해하는 경우가 많다. 고품질 추적 및 평가는 개발자가 이러한 유형의 질문에 자신감을 가지고 빠르게 답변하는 데 도움이 될 수 있다. [LangSmith](https://docs.smith.langchain.com/)는 AI 애플리케이션의 관찰 가능성 및 평가를 지원하는 당사의 플랫폼이다. 자세한 내용은 [평가](https://docs.smith.langchain.com/concepts/evaluation) 및 [추적](https://docs.smith.langchain.com/concepts/tracing)에 대한 개념 가이드를 참조하라.

> **추가 자료**
> 자세한 내용은 [LangSmith 추적 및 평가](https://youtube.com/playlist?list=PLfaIDFEXuae0um8Fj0V4dHG37fGFU8Q5S&feature=shared)에 대한 동영상 재생 목록을 참조하십시오.

## 결론

LangChain은 많은 AI 애플리케이션의 중심이 되는 구성 요소에 대한 표준 인터페이스를 제공하며, 이는 몇 가지 특정 이점을 제공한다.

- **공급자 교체의 용이성:** 기본 코드를 변경하지 않고도 다른 구성 요소 공급자를 교체할 수 있다.
- **고급 기능:** [스트리밍](/docs/concepts/streaming/) 및 [도구 호출](/docs/concepts/tool_calling/)과 같은 고급 기능에 대한 공통 메서드를 제공한다.

[LangGraph](https://langchain-ai.github.io/langgraph/concepts/high_level/)는 복잡한 애플리케이션([에이전트](/docs/concepts/agents/) 등)을 오케스트레이션하고 [지속성](https://langchain-ai.github.io/langgraph/concepts/persistence/), [휴먼-인-더-루프](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/) 또는 [메모리](https://langchain-ai.github.io/langgraph/concepts/memory/) 포함과 같은 기능을 제공할 수 있도록 한다.

[LangSmith](https://docs.smith.langchain.com/)는 LLM별 관찰 가능성 및 애플리케이션 테스트 및 평가 프레임워크를 제공하여 애플리케이션을 자신감을 가지고 반복할 수 있도록 한다.
