# 사용법

## 변환

### 단일 문서 변환

개별 PDF 문서를 변환하려면 `convert()`를 사용합니다. 예를 들면 다음과 같습니다.

```python
from docling.document_converter import DocumentConverter

source = "https://arxiv.org/pdf/2408.09869"  # PDF 경로 또는 URL
converter = DocumentConverter()
result = converter.convert(source)
print(result.document.export_to_markdown())  # 출력: "### Docling Technical Report[...]"
```

### CLI

명령줄에서 직접 Docling을 사용하여 로컬 또는 URL의 개별 파일이나 전체 디렉토리를 변환할 수도 있습니다.

```bash
docling https://arxiv.org/pdf/2206.01062
```

Docling CLI를 통해 🥚[SmolDocling](https://huggingface.co/ds4sd/SmolDocling-256M-preview) 및 기타 VLM을 사용할 수도 있습니다.

```bash
docling --pipeline vlm --vlm-model smoldocling https://arxiv.org/pdf/2206.01062
```

이 명령은 지원되는 Apple Silicon 하드웨어에서 MLX 가속을 사용합니다.

사용 가능한 모든 옵션(내보내기 형식 등)을 보려면 `docling --help`를 실행하십시오. 자세한 내용은 [CLI 참조 페이지](https://docling-project.github.io/docling/reference/cli/)에서 확인할 수 있습니다.

### 고급 옵션

#### 모델 사전 다운로드 및 오프라인 사용

기본적으로 모델은 처음 사용할 때 자동으로 다운로드됩니다. 오프라인 사용(예: 에어갭 환경)을 위해 명시적으로 모델을 사전 다운로드하려면 다음과 같이 할 수 있습니다.

**1단계: 모델 사전 다운로드**

`docling-tools models download` 유틸리티를 사용합니다.

```bash
$ docling-tools models download
Downloading layout model...
Downloading tableformer model...
Downloading picture classifier model...
Downloading code formula model...
Downloading easyocr models...
Models downloaded into $HOME/.cache/docling/models.
```

또는 `docling.utils.model_downloader.download_models()`를 사용하여 프로그래밍 방식으로 모델을 다운로드할 수 있습니다.

**2단계: 사전 다운로드한 모델 사용**

```python
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import EasyOcrOptions, PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

artifacts_path = "/local/path/to/models"

pipeline_options = PdfPipelineOptions(artifacts_path=artifacts_path)
doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

또는 CLI 사용:

```bash
docling --artifacts-path="/local/path/to/models" FILE
```

또는 `DOCLING_ARTIFACTS_PATH` 환경 변수 사용:

```bash
export DOCLING_ARTIFACTS_PATH="/local/path/to/models"
python my_docling_script.py
```

#### 원격 서비스 사용

Docling의 주요 목적은 원격 서비스와 사용자 데이터를 공유하지 않는 로컬 모델을 실행하는 것입니다.
하지만 클라우드 공급업체의 OCR 엔진을 호출하거나 호스팅된 LLM을 사용하는 등 파이프라인의 일부를 원격 서비스를 사용하여 처리하는 유효한 사용 사례가 있습니다.

Docling에서는 이러한 모델을 허용하기로 결정했지만, 사용자가 외부 서비스와 통신하는 데 명시적으로 동의해야 합니다.

```python
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

pipeline_options = PdfPipelineOptions(enable_remote_services=True)
doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

`enable_remote_services=True` 값이 설정되지 않은 경우 시스템은 `OperationNotAllowed()` 예외를 발생시킵니다.

_참고: 이 옵션은 시스템이 사용자 데이터를 원격 서비스로 보내는 것과만 관련이 있습니다. 데이터 가져오기(예: 모델 가중치) 제어는 [모델 사전 다운로드 및 오프라인 사용](https://docling-project.github.io/docling/usage/#model-prefetching-and-offline-usage)에 설명된 논리를 따릅니다._

##### 원격 모델 서비스 목록

이 목록의 옵션은 문서를 처리할 때 명시적인 `enable_remote_services=True`가 필요합니다.

- `PictureDescriptionApiOptions`: API 호출을 통한 비전 모델 사용.

#### 파이프라인 기능 조정

예제 파일 [custom_convert.py](https://docling-project.github.io/docling/examples/custom_convert/)에는 변환 파이프라인과 기능을 조정할 수 있는 여러 가지 방법이 포함되어 있습니다.

##### PDF 표 추출 옵션 제어

표 구조 인식이 인식된 구조를 다시 PDF 셀에 매핑해야 하는지(기본값) 또는 구조 예측 자체의 텍스트 셀을 사용해야 하는지 제어할 수 있습니다.
추출된 표의 여러 열이 실수로 하나로 병합되는 경우 출력 품질을 개선할 수 있습니다.

```python
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions

pipeline_options = PdfPipelineOptions(do_table_structure=True)
pipeline_options.table_structure_options.do_cell_matching = False  # uses text cells predicted from table structure model

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

docling 1.16.0부터: 사용할 TableFormer 모드를 제어할 수 있습니다. `TableFormerMode.FAST`(더 빠르지만 덜 정확함)와 `TableFormerMode.ACCURATE`(기본값) 중에서 선택하여 어려운 표 구조에서 더 나은 품질을 얻을 수 있습니다.

```python
from docling.datamodel.base_models import InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode

pipeline_options = PdfPipelineOptions(do_table_structure=True)
pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE  # use more accurate TableFormer model

doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)
```

#### 문서 크기 제한 부과

문서당 처리할 수 있는 파일 크기와 페이지 수를 제한할 수 있습니다.

```python
from pathlib import Path
from docling.document_converter import DocumentConverter

source = "https://arxiv.org/pdf/2408.09869"
converter = DocumentConverter()
result = converter.convert(source, max_num_pages=100, max_file_size=20971520)
```

#### 바이너리 PDF 스트림에서 변환

파일 시스템 대신 바이너리 스트림에서 PDF를 다음과 같이 변환할 수 있습니다.

```python
from io import BytesIO
from docling.datamodel.base_models import DocumentStream
from docling.document_converter import DocumentConverter

buf = BytesIO(your_binary_stream)
source = DocumentStream(name="my_doc.pdf", stream=buf)
converter = DocumentConverter()
result = converter.convert(source)
```

#### 리소스 사용량 제한

`OMP_NUM_THREADS` 환경 변수를 적절하게 설정하여 Docling에서 사용하는 CPU 스레드를 제한할 수 있습니다. 기본 설정은 CPU 스레드 4개를 사용합니다.

#### 특정 백엔드 변환기 사용

> **참고**
>
> 이 섹션에서는 [백엔드](https://docling-project.github.io/docling/concepts/architecture/)를 직접 호출하는 방법, 즉 저수준 API를 사용하는 방법에 대해 설명합니다. 이는 필요할 때만 수행해야 합니다. 대부분의 경우 위 섹션에서 설명한 대로 `DocumentConverter`(고수준 API)를 사용하는 것으로 충분하며 권장되는 방법입니다.

기본적으로 Docling은 문서 형식을 식별하여 적절한 변환 백엔드를 적용하려고 시도합니다([지원되는 형식](https://docling-project.github.io/docling/usage/supported_formats/) 목록 참조).
[다중 형식 변환](https://docling-project.github.io/docling/examples/run_with_formats/) 예제와 같이 `DocumentConverter`를 허용된 문서 형식 집합으로 제한할 수 있습니다.
또는 문서 내용과 일치하는 특정 백엔드를 사용할 수도 있습니다. 예를 들어 HTML 페이지에는 `HTMLDocumentBackend`를 사용할 수 있습니다.

```python
import urllib.request
from io import BytesIO
from docling.backend.html_backend import HTMLDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import InputDocument

url = "https://en.wikipedia.org/wiki/Duck"
text = urllib.request.urlopen(url).read()
in_doc = InputDocument(
    path_or_stream=BytesIO(text),
    format=InputFormat.HTML,
    backend=HTMLDocumentBackend,
    filename="duck.html",
)
backend = HTMLDocumentBackend(in_doc=in_doc, path_or_stream=BytesIO(text))
dl_doc = backend.convert()
print(dl_doc.export_to_markdown())
```

## 청킹

아래와 같이 `HybridChunker`와 같은 [chunker](https://docling-project.github.io/docling/concepts/chunking/)를 사용하여 Docling 문서를 청크로 나눌 수 있습니다(자세한 내용은 [이 예제](https://docling-project.github.io/docling/examples/hybrid_chunking/)를 확인하십시오).

```python
from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker

conv_res = DocumentConverter().convert("https://arxiv.org/pdf/2206.01062")
doc = conv_res.document

chunker = HybridChunker(tokenizer="BAAI/bge-small-en-v1.5")  # set tokenizer as needed
chunk_iter = chunker.chunk(doc)
```

예제 청크는 다음과 같습니다.

```python
print(list(chunk_iter)[11])
# {
#   "text": "In this paper, we present the DocLayNet dataset. [...]",
#   "meta": {
#     "doc_items": [{
#       "self_ref": "#/texts/28",
#       "label": "text",
#       "prov": [{
#         "page_no": 2,
#         "bbox": {"l": 53.29, "t": 287.14, "r": 295.56, "b": 212.37, ...},
#       }], ...,
#     }, ...],
#     "headings": ["1 INTRODUCTION"],
#   }
# }
```
