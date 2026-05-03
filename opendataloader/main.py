import opendataloader_pdf

def main():

    # main.py 예시
    opendataloader_pdf.convert(
        input_path=["data/sample_income_tax_p27.pdf"],
        output_dir="output/",
        hybrid="docling-fast",
        hybrid_mode="full", # 이미지 묘사 결과를 포함하기 위해 필수
        java_path=r"C:\Program Files\Eclipse Adoptium\jdk-25.0.2+10"
    )



if __name__ == "__main__":
    main()
