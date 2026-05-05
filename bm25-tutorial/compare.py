import requests
from typing import Optional, Sequence, List
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_core.documents import Document
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import BaseDocumentCompressor
from kiwipiepy import Kiwi

# 리트리버 통합 패키지
from langchain_classic.retrievers import EnsembleRetriever, ContextualCompressionRetriever

# Ollama의 리랭커 모델을 활용하기 위한 커스텀 클래스
class OllamaReranker(BaseDocumentCompressor):
    model: str = "gemma3:latest"
    top_n: int = 2

    def compress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Optional[CallbackManagerForRetrieverRun] = None,
    ) -> Sequence[Document]:
        if not documents:
            return []
        
        # 생성형 모델을 리랭커로 활용 (프롬프트 방식)
        llm = OllamaLLM(model=self.model, temperature=0)
        
        scored_docs = []
        for doc in documents:
            prompt = (
                f"질문: {query}\n"
                f"문서: {doc.page_content}\n\n"
                "위 문서가 질문에 얼마나 관련이 있는지 0에서 1 사이의 점수(숫자)로만 대답해줘. "
                "설명 없이 숫자만 출력해."
            )
            
            try:
                response = llm.invoke(prompt).strip()
                # 숫자만 추출 (정규식 사용)
                import re
                score_match = re.search(r"0\.\d+|1\.0|0", response)
                score = float(score_match.group()) if score_match else 0.0
                
                new_doc = Document(
                    page_content=doc.page_content,
                    metadata={**doc.metadata, "relevance_score": score}
                )
                scored_docs.append(new_doc)
            except Exception:
                new_doc = Document(
                    page_content=doc.page_content,
                    metadata={**doc.metadata, "relevance_score": 0.0}
                )
                scored_docs.append(new_doc)
        
        # 점수 순으로 정렬 후 상위 결과 반환
        scored_docs.sort(key=lambda x: x.metadata.get("relevance_score", 0), reverse=True)
        return scored_docs[:self.top_n]

def compare_retrievers():
    # 1. 테스트 데이터셋 구성
    docs = [
        Document(page_content="삼성전자의 최신 스마트폰 갤럭시 S24 울트라는 AI 기능을 탑재했습니다."),
        Document(page_content="애플의 아이폰 15 프로는 티타늄 소재를 사용하여 가볍습니다."),
        Document(page_content="점심 메뉴로는 따뜻한 국밥이나 비빔밥을 추천합니다."),
        Document(page_content="허기를 채울 수 있는 맛있는 음식을 찾고 계신가요?"),
        Document(page_content="서울의 날씨는 맑음이며 기온은 20도입니다.")
    ]

    kiwi = Kiwi()

    def kiwi_tokenizer(text):
        target_tags = ['NNG', 'NNP', 'VV', 'VA', 'SL', 'SN']
        return [token.form for token in kiwi.tokenize(text) if token.tag in target_tags]

    # 2. 임베딩 모델 설정
    embeddings = OllamaEmbeddings(model="bge-m3")
    vectorstore = FAISS.from_documents(docs, embeddings)
    
    # 3. 리트리버 구성
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    bm25_retriever = BM25Retriever.from_documents(docs, preprocess_func=kiwi_tokenizer)
    bm25_retriever.k = 3
    
    hybrid_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=[0.5, 0.5]
    )

    # gemma3:latest 모델을 사용하여 생성형 리랭킹을 수행합니다.
    ollama_reranker = OllamaReranker(model="gemma3:latest", top_n=2)
    
    rerank_retriever = ContextualCompressionRetriever(
        base_compressor=ollama_reranker, 
        base_retriever=hybrid_retriever
    )

    # 5. 비교 출력용 헬퍼 함수
    def test_query(query):
        print(f"\n{'='*60}")
        print(f"검색 질문: {query}")
        print(f"{'='*60}")
        
        print("\n[1] 벡터 검색")
        for doc in vector_retriever.invoke(query):
            print(f"    - {doc.page_content}")
            
        print("\n[2] BM25 검색")
        for doc in bm25_retriever.invoke(query):
            print(f"    - {doc.page_content}")
            
        print("\n[3] 하이브리드 검색 (BM25 + Vector)")
        for doc in hybrid_retriever.invoke(query):
            print(f"    - {doc.page_content}")
            
        print("\n[4] 하이브리드 + Ollama 리랭커 (최종)")
        print(f"    (Ollama 모델: {ollama_reranker.model} 사용)")
        for doc in rerank_retriever.invoke(query):
            score = doc.metadata.get("relevance_score", 0)
            print(f"    - [{score:.4f}] {doc.page_content}")

    # 6. 테스트 실행
    print("\n[Ollama 전용 리랭커를 적용한 성능 비교 테스트를 시작합니다.]")
    test_query("배가 너무 고픈데 먹을 것 좀 추천해줘")
    test_query("S24 울트라 스펙 알려줘")

if __name__ == "__main__":
    compare_retrievers()
