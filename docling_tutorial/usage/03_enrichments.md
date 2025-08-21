# 강화 기능

Docling은 코드 블록, 그림 등과 같은 특정 문서 구성 요소를 처리하는 추가 단계를 통해 변환 파이프라인을 강화할 수 있습니다.
추가 단계는 일반적으로 추가 모델 실행이 필요하며, 이로 인해 처리 시간이 상당히 늘어날 수 있습니다.
이러한 이유로 대부분의 강화 모델은 기본적으로 비활성화되어 있습니다.

다음 표는 Docling에서 사용할 수 있는 기본 강화 모델에 대한 개요를 제공합니다.

| 기능      | 매개변수                    | 처리된 항목                   | 설명                                                 |
| --------- | --------------------------- | ----------------------------- | ---------------------------------------------------- |
| 코드 이해 | `do_code_enrichment`        | `CodeItem`                    | [아래 문서](#code-understanding)를 참조하십시오.     |
| 수식 이해 | `do_formula_enrichment`     | `TextItem` (레이블 `FORMULA`) | [아래 문서](#formula-understanding)를 참조하십시오.  |
| 그림 분류 | `do_picture_classification` | `PictureItem`                 | [아래 문서](#picture-classification)를 참조하십시오. |
| 그림 설명 | `do_picture_description`    | `PictureItem`                 | [아래 문서](#picture-description)를 참조하십시오.    |

<h2 id="enrichments-details">강화 세부 정보</h2>
<h3 id="code-understanding">코드 이해</h3>

코드 이해 단계에서는 문서에서 발견된 코드 블록에 대해 고급 구문 분석을 사용할 수 있습니다.
이 강화 모델은 `CodeItem`의 `code_language` 속성도 설정합니다.

모델 사양: [`CodeFormula` 모델 카드](https://huggingface.co/ds4sd/CodeFormula)를 참조하십시오.

명령줄 예시:

```bash
docling --enrich-code FILE
```

코드 예시:

```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

pipeline_options = PdfPipelineOptions()
pipeline_options.do_code_enrichment = True

converter = DocumentConverter(format_options={
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
})

result = converter.convert("https://arxiv.org/pdf/2501.17887")
doc = result.document
```

<h3 id="formula-understanding">수식 이해</h3>

수식 이해 단계는 문서의 방정식을 분석하고 LaTeX 표현을 추출합니다.
DoclingDocument의 HTML 내보내기 기능은 수식을 활용하여 mathml html 구문을 사용하여 결과를 시각화합니다.

모델 사양: [`CodeFormula` 모델 카드](https://huggingface.co/ds4sd/CodeFormula)를 참조하십시오.

명령줄 예시:

```bash
docling --enrich-formula FILE
```

코드 예시:

```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

pipeline_options = PdfPipelineOptions()
pipeline_options.do_formula_enrichment = True

converter = DocumentConverter(format_options={
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
})

result = converter.convert("https://arxiv.org/pdf/2501.17887")
doc = result.document
```

<h3 id="picture-classification">그림 분류</h3>

그림 분류 단계는 `DocumentFigureClassifier` 모델을 사용하여 문서의 `PictureItem` 요소를 분류합니다.
이 모델은 다양한 차트 유형, 순서도, 로고, 서명 등 문서에서 발견되는 그림의 클래스를 이해하는 데 특화되어 있습니다.

모델 사양: [`DocumentFigureClassifier` 모델 카드](https://huggingface.co/ds4sd/DocumentFigureClassifier)를 참조하십시오.

명령줄 예시:

```bash
docling --enrich-picture-classes FILE
```

코드 예시:

```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

pipeline_options = PdfPipelineOptions()
pipeline_options.generate_picture_images = True
pipeline_options.images_scale = 2
pipeline_options.do_picture_classification = True

converter = DocumentConverter(format_options={
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
})

result = converter.convert("https://arxiv.org/pdf/2501.17887")
doc = result.document
```

<h3 id="picture-description">그림 설명</h3>

그림 설명 단계는 비전 모델로 그림에 주석을 달 수 있게 합니다. 이는 "캡션" 작업으로도 알려져 있습니다.
Docling 파이프라인은 모델을 완전히 로컬에서 로드하고 실행할 수 있을 뿐만 아니라 채팅 템플릿을 지원하는 원격 API에 연결할 수도 있습니다.
아래는 몇 가지 일반적인 비전 모델 및 원격 서비스를 사용하는 방법에 대한 몇 가지 예입니다.

```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.datamodel.base_models import InputFormat

pipeline_options = PdfPipelineOptions()
pipeline_options.do_picture_description = True

converter = DocumentConverter(format_options={
    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
})

result = converter.convert("https://arxiv.org/pdf/2501.17887")
doc = result.document
```

<h4 id="granite-vision-model">Granite Vision 모델</h4>

모델 사양: [`ibm-granite/granite-vision-3.1-2b-preview` 모델 카드](https://huggingface.co/ibm-granite/granite-vision-3.1-2b-preview)를 참조하십시오.

Docling에서의 사용법:

```python
from docling.datamodel.pipeline_options import granite_picture_description

pipeline_options.picture_description_options = granite_picture_description
```

<h4 id="smolvlm-model">SmolVLM 모델</h4>

모델 사양: [`HuggingFaceTB/SmolVLM-256M-Instruct` 모델 카드](https://huggingface.co/HuggingFaceTB/SmolVLM-256M-Instruct)를 참조하십시오.

Docling에서의 사용법:

```python
from docling.datamodel.pipeline_options import smolvlm_picture_description

pipeline_options.picture_description_options = smolvlm_picture_description
```

<h4 id="other-vision-models">기타 비전 모델</h4>

`PictureDescriptionVlmOptions` 옵션 클래스를 사용하면 Hugging Face Hub의 다른 모델을 사용할 수 있습니다.

```python
from docling.datamodel.pipeline_options import PictureDescriptionVlmOptions

pipeline_options.picture_description_options = PictureDescriptionVlmOptions(
    repo_id="",  # <-- 여기에 선호하는 VLM의 Hugging Face repo_id를 추가하십시오.
    prompt="이미지를 세 문장으로 설명하십시오. 간결하고 정확하게 작성하십시오.",
)
```

<h4 id="remote-vision-model">원격 비전 모델</h4>

`PictureDescriptionApiOptions` 옵션 클래스를 사용하면 [VLLM](https://docs.vllm.ai), [Ollama](https://ollama.com/) 등과 같은 로컬 엔드포인트나 [IBM watsonx.ai](https://www.ibm.com/products/watsonx-ai)와 같은 클라우드 제공업체에서 호스팅되는 모델을 사용할 수 있습니다.

_참고: 대부분의 경우 이 옵션은 데이터를 원격 서비스 제공업체로 전송합니다._

Docling에서의 사용법:

```python
from docling.datamodel.pipeline_options import PictureDescriptionApiOptions

# 원격 서비스 연결 활성화
pipeline_options.enable_remote_services=True  # <-- 이것이 필요합니다!

# VLLM 등을 통해 로컬에서 실행되는 모델 사용 예시
# $ vllm serve MODEL_NAME
pipeline_options.picture_description_options = PictureDescriptionApiOptions(
    url="http://localhost:8000/v1/chat/completions",
    params=dict(
        model="MODEL NAME",
        seed=42,
        max_completion_tokens=200,
    ),
    prompt="이미지를 세 문장으로 설명하십시오. 간결하고 정확하게 작성하십시오.",
    timeout=90,
)
```

클라우드 제공업체를 위한 엔드투엔드 코드 스니펫은 예제 섹션에서 사용할 수 있습니다:

- [IBM watsonx.ai](https://docling-project.github.io/docling/examples/pictures_description_api/)

<h2 id="develop-new-enrichment-models">새로운 강화 모델 개발</h2>

위에 나열된 모든 모델의 구현을 살펴보는 것 외에도 Docling 문서에는 강화 모델 구현에 대한 몇 가지 예제가 있습니다.

- [그림 강화 개발](https://docling-project.github.io/docling/examples/develop_picture_enrichment/)
- [수식 이해 개발](https://docling-project.github.io/docling/examples/develop_formula_understanding/)
