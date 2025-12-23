# uv add torch --index https://download.pytorch.org/whl/cu121

from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "kakaocorp/kanana-2-30b-a3b-instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="bfloat16",
    device_map="auto"
)

prompt = "Explain the future of AI."

messages = [
    {"role": "user", "content": prompt}
]
input_ids = tokenizer.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    return_tensors="pt"
).to(model.device)

output = model.generate(
    input_ids,
    max_new_tokens=128,
    do_sample=False,
)
print(tokenizer.decode(output[0]))
