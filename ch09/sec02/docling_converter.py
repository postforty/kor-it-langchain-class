#!/usr/bin/env python3
"""
PDF를 Markdown으로 변환 (이미지 표 포함)

이 스크립트는 PDF 파일을 Markdown으로 변환하며,
이미지로 된 표도 마크다운 표 형식으로 변환합니다.
"""

import os
import argparse
from pathlib import Path
from typing import Optional

try:
    from docling.document_converter import DocumentConverter
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import PdfFormatOption
    from docling.datamodel.base_models import InputFormat
except ImportError:
    print("Docling을 설치해주세요: pip install docling")
    exit(1)


class PDFToMarkdownConverter:
    """PDF를 Markdown으로 변환하는 클래스"""
    
    def __init__(self, enable_ocr: bool = True, enable_table_structure: bool = True):
        """
        변환기 초기화
        
        Args:
            enable_ocr: OCR 기능 활성화 (이미지 텍스트 인식)
            enable_table_structure: 표 구조 인식 활성화
        """
        # PDF 파이프라인 옵션 설정
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = enable_ocr
        pipeline_options.do_table_structure = enable_table_structure
        
        # DocumentConverter 초기화
        self.converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
            }
        )
    
    def convert_pdf_to_markdown(self, pdf_path: str, output_path: Optional[str] = None) -> str:
        """
        PDF를 Markdown으로 변환
        
        Args:
            pdf_path: 입력 PDF 파일 경로
            output_path: 출력 Markdown 파일 경로 (None이면 자동 생성)
            
        Returns:
            생성된 Markdown 내용
        """
        # 파일 존재 확인
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF 파일을 찾을 수 없습니다: {pdf_path}")
        
        print(f"PDF 변환 시작: {pdf_path}")
        
        # PDF 파싱 및 변환
        result = self.converter.convert(pdf_path)
        
        # Markdown으로 변환
        markdown_content = result.document.export_to_markdown()
        
        # 출력 파일 경로 결정
        if output_path is None:
            pdf_file = Path(pdf_path)
            output_path = pdf_file.parent / f"{pdf_file.stem}.md"
        
        # Markdown 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"변환 완료: {output_path}")
        return markdown_content
    
    def batch_convert(self, input_dir: str, output_dir: Optional[str] = None):
        """
        디렉토리 내 모든 PDF 파일을 일괄 변환
        
        Args:
            input_dir: 입력 PDF 파일들이 있는 디렉토리
            output_dir: 출력 디렉토리 (None이면 입력 디렉토리와 동일)
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"입력 디렉토리를 찾을 수 없습니다: {input_dir}")
        
        # 출력 디렉토리 설정
        if output_dir is None:
            output_path = input_path
        else:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        
        # PDF 파일 찾기
        pdf_files = list(input_path.glob("*.pdf"))
        if not pdf_files:
            print(f"'{input_dir}'에서 PDF 파일을 찾을 수 없습니다.")
            return
        
        print(f"{len(pdf_files)}개의 PDF 파일을 변환합니다...")
        
        # 각 PDF 파일 변환
        success_count = 0
        for pdf_file in pdf_files:
            try:
                output_file = output_path / f"{pdf_file.stem}.md"
                self.convert_pdf_to_markdown(str(pdf_file), str(output_file))
                success_count += 1
            except Exception as e:
                print(f"'{pdf_file}' 변환 실패: {e}")
        
        print(f"\n일괄 변환 완료: {success_count}/{len(pdf_files)}개 성공")


def main():
    """명령줄 인터페이스"""
    parser = argparse.ArgumentParser(
        description="PDF를 Markdown으로 변환 (이미지 표 포함)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예제:
  # 단일 파일 변환
  python pdf_to_md.py input.pdf
  
  # 출력 파일명 지정
  python pdf_to_md.py input.pdf -o output.md
  
  # 디렉토리 일괄 변환
  python pdf_to_md.py -d pdf_folder/
  
  # OCR 없이 변환 (텍스트 PDF만)
  python pdf_to_md.py input.pdf --no-ocr
        """
    )
    
    # 인수 설정
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("pdf_file", nargs='?', help="변환할 PDF 파일")
    group.add_argument("-d", "--directory", help="PDF 파일들이 있는 디렉토리")
    
    parser.add_argument("-o", "--output", help="출력 파일/디렉토리 경로")
    parser.add_argument("--no-ocr", action="store_true", help="OCR 기능 비활성화")
    parser.add_argument("--no-table-structure", action="store_true", help="표 구조 인식 비활성화")
    
    args = parser.parse_args()
    
    # 변환기 초기화
    converter = PDFToMarkdownConverter(
        enable_ocr=not args.no_ocr,
        enable_table_structure=not args.no_table_structure
    )
    
    try:
        if args.directory:
            # 디렉토리 일괄 변환
            converter.batch_convert(args.directory, args.output)
        else:
            # 단일 파일 변환
            converter.convert_pdf_to_markdown(args.pdf_file, args.output)
    
    except Exception as e:
        print(f"오류 발생: {e}")
        return 1
    
    return 0


# 간단한 사용법 함수들
def convert_single_pdf(pdf_path: str, output_path: str = None) -> str:
    """
    단일 PDF 파일을 Markdown으로 변환하는 간단한 함수
    
    Args:
        pdf_path: PDF 파일 경로
        output_path: 출력 파일 경로 (선택사항)
    
    Returns:
        변환된 Markdown 내용
    """
    converter = PDFToMarkdownConverter()
    return converter.convert_pdf_to_markdown(pdf_path, output_path)


def convert_pdf_folder(folder_path: str, output_folder: str = None):
    """
    폴더 내 모든 PDF를 Markdown으로 변환하는 간단한 함수
    
    Args:
        folder_path: PDF 파일들이 있는 폴더
        output_folder: 출력 폴더 (선택사항)
    """
    converter = PDFToMarkdownConverter()
    converter.batch_convert(folder_path, output_folder)


if __name__ == "__main__":
    # 명령줄에서 실행하지 않는 경우의 예제
    if len(os.sys.argv) == 1:
        print("PDF to Markdown 변환기")
        print("======================")
        print()
        print("사용법:")
        print("1. 명령줄: python pdf_to_md.py input.pdf")
        print("2. 코드에서: convert_single_pdf('input.pdf')")
        print("3. 폴더 변환: convert_pdf_folder('pdf_folder/')")
        print()
        print("예제 실행:")
        
        # 예제 파일이 있다면 변환 시도
        example_files = ["../data/sample_income_tax_p27.pdf"]
        for example_file in example_files:
            if os.path.exists(example_file):
                print(f"'{example_file}' 변환 중...")
                try:
                    result = convert_single_pdf(example_file)
                    print(f"성공! Markdown 길이: {len(result)} 문자")
                    break
                except Exception as e:
                    print(f"변환 실패: {e}")
        else:
            print("예제 PDF 파일이 없습니다.")
            print("실제 PDF 파일로 테스트해보세요.")
    else:
        # 명령줄 인수가 있으면 CLI 모드로 실행
        exit(main())