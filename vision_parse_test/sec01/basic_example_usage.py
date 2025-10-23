from vision_parse import VisionParser

# Initialize parser
parser = VisionParser(
    model_name="llama3.2-vision:11b", # For local models, you don't need to provide the api key
    temperature=0.4,
    top_p=0.5,
    image_mode="url", # Image mode can be "url", "base64" or None
    detailed_extraction=False, # Set to True for more detailed extraction
    enable_concurrency=False, # Set to True for parallel processing
)

# Convert PDF to markdown
pdf_path = "../data/sample_income_tax_p30.pdf" # local path to your pdf file
markdown_pages = parser.convert_pdf(pdf_path)

# Process results
for i, page_content in enumerate(markdown_pages):
    print(f"\n--- Page {i+1} ---\n{page_content}")