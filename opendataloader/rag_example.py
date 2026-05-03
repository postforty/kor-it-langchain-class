import json
import os
import base64
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
load_dotenv()

def calculate_vertical_distance(box1, box2):
    """두 바운딩 박스 사이의 최소 수직 거리를 계산합니다."""
    # box format: [x1, y1, x2, y2]
    y1_min, y1_max = box1[1], box1[3]
    y2_min, y2_max = box2[1], box2[3]
    return min(abs(y1_min - y2_max), abs(y2_min - y1_max))

def run_rag_example():
    # 1. 추출된 JSON 데이터 로드
    json_path = "output/sample_income_tax_p27.json"
    if not os.path.exists(json_path):
        print(f"오류: {json_path} 파일이 없습니다. 먼저 main.py를 실행하여 JSON을 생성해 주세요.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 2. JSON 요소를 LangChain Document 객체로 변환 (거리 기반 멀티모달 연결)
    documents = []
    
    # 페이지별 이미지 정보 수집 (경로 + 좌표)
    page_images = {}
    for item in data.get("kids", []):
        if item.get("type") == "image":
            pg = item.get("page number")
            if pg not in page_images:
                page_images[pg] = []
            page_images[pg].append({
                "path": os.path.join("output", item.get("source", "")),
                "bbox": item.get("bounding box")
            })

    for item in data.get("kids", []):
        if item.get("type") == "image":
            continue
            
        content = item.get("content", "").strip()
        if content:
            pg = item.get("page number")
            bbox = item.get("bounding box")
            
            # 같은 페이지의 이미지 중 수직 거리가 400px 이내인 것들만 선별
            related_images = []
            for img in page_images.get(pg, []):
                if calculate_vertical_distance(bbox, img["bbox"]) < 400:
                    related_images.append(img["path"])
            
            doc = Document(
                page_content=content,
                metadata={
                    "source": data.get("file name"),
                    "page": pg,
                    "type": item.get("type"),
                    "image_paths": related_images # 연관된 이미지 리스트 저장
                }
            )
            documents.append(doc)

    print(f"성공: {len(documents)}개의 문서 조각이 로드되었습니다.")

    # 3. 임베딩 및 FAISS 벡터 저장소 생성
    # 주의: 환경 변수에 GOOGLE_API_KEY가 설정되어 있어야 합니다.
    # 만약 환경변수 설정이 안 되어 있다면 아래 주석을 해제하고 키를 입력하세요.
    # os.environ["GOOGLE_API_KEY"] = "your-google-api-key"
    
    try:
        embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
        
        print("벡터 저장소를 생성 중입니다 (임베딩 진행)...")
        vectorstore = FAISS.from_documents(documents, embeddings)

        # 4. 리트리버(Retriever) 생성
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

        print("\n" + "="*50)
        print("대화를 시작합니다. (종료하려면 'exit' 또는 'quit' 입력)")
        print("="*50)

        while True:
            query = input("\n[질문]: ")
            if query.lower() in ["exit", "quit", "exit()", "종료"]:
                print("대화를 종료합니다.")
                break
            
            if not query.strip():
                continue

            # 관련 문서 검색
            relevant_docs = retriever.invoke(query)
            
            print("\n[검색 결과]")
            for i, doc in enumerate(relevant_docs):
                print(f" - 결과 {i+1} (P.{doc.metadata['page']}): {doc.page_content[:100]}...")

            # 5. 멀티모달 답변 생성
            print("\n답변 생성 중...")
            
            # 검색된 문서들 중 이미지가 포함된 문서를 우선적으로 선택
            target_doc = next((d for d in relevant_docs if d.metadata.get("image_paths")), relevant_docs[0])
            
            content_list = [
                {"type": "text", "text": f"Context: {target_doc.page_content}\n\nQuestion: {query}"}
            ]
            
            # 연관된 모든 이미지를 중복 없이 추가
            image_paths = target_doc.metadata.get("image_paths", [])
            for img_path in image_paths:
                if os.path.exists(img_path):
                    with open(img_path, "rb") as f:
                        image_bytes = base64.b64encode(f.read()).decode("utf-8")
                        content_list.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_bytes}"}
                        })
            
            if image_paths:
                print(f"연관 이미지 {len(image_paths)}장을 찾았습니다: {image_paths}")
            
            message = HumanMessage(content=content_list)
            response = llm.invoke([message])
            
            print("\n[AI 답변]:")
            print(response.content)
            print("-" * 50)
            
    except Exception as e:
        print(f"\n오류 발생: {e}")
        print("참고: GOOGLE_API_KEY가 유효한지 확인해 주세요.")

if __name__ == "__main__":
    run_rag_example()
