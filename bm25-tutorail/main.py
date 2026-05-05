from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
# EnsembleRetriever의 위치가 langchain_classic으로 변경되었습니다.
from langchain_classic.retrievers import EnsembleRetriever
from langchain_core.documents import Document

def main():
    # 1. 예시 데이터 (문서)
    docs = [
        Document(page_content="비타민 C는 면역력 강화와 피부 건강에 도움을 줍니다."),
        Document(page_content="비타민 D는 뼈 건강과 칼슘 흡수에 필수적입니다."),
        Document(page_content="오메가3는 혈행 개선과 눈 건강에 효과가 있습니다."),
        Document(page_content="루테인은 황반 변성 예방 등 눈 건강에 도움을 줍니다."),
        Document(page_content="마그네슘은 근육 이완과 스트레스 완화에 좋습니다.")
    ]

    # 2. Sparse Retriever 설정 (BM25)
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = 2

    # 3. Dense Retriever 설정 (FAISS)
    # Ollama의 bge-m3 모델 사용
    embeddings = OllamaEmbeddings(model="bge-m3")
    vectorstore = FAISS.from_documents(docs, embeddings)
    faiss_retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

    # 4. Ensemble Retriever (Hybrid Search) 설정
    # BM25와 FAISS 결과를 RRF 방식으로 결합
    hybrid_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, faiss_retriever],
        weights=[0.4, 0.6]
    )

    # 5. 검색 실행
    query = "눈에 좋은 영양제 알려줘"
    result_docs = hybrid_retriever.invoke(query)

    print(f"질문: {query}\n")
    print("--- 하이브리드 검색 결과 ---")
    for i, doc in enumerate(result_docs):
        print(f"[{i+1}] {doc.page_content}")

if __name__ == "__main__":
    main()
