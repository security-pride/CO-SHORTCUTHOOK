#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author: DirtyBoy
@Date: 2026/4/20 15:07
"""
import os, argparse, json, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from tqdm import tqdm

# llm_path = "/home/nusbac/LHD_LLM/VulCure/my_llm/"
llm_path = "/home/user/Public/LLM_Demo/LLM_uncertainty/my_llm"


def write_to_jsonl(data, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            line = json.dumps(item, ensure_ascii=False)
            f.write(line + '\n')


def read_from_jsonl(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line.strip()))
    return data


def generate_func(text, tokenizer, model, max_token=200):
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    inputs = tokenizer(
        text,
        return_tensors="pt",
        padding=True,
        truncation=True
    ).to("cuda")

    outputs = model.generate(
        input_ids=inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        max_new_tokens=max_token,
        pad_token_id=tokenizer.eos_token_id
    )

    generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]

    return tokenizer.decode(generated_tokens, skip_special_tokens=True)


# tmp = ["humaneval_C", "humaneval_C_ChangeCodestyle", "humaneval_C_InsertDeadcode", "humaneval_C_RenameFunction",
#        "humaneval_C_RenameVariable"]
tmp = [  # "humaneval_C",
    # 'humaneval_C_InsertNoopcode_CodeStyle_newline',
    # 'humaneval_C_InsertNoopcode_CodeStyle_space',
    # 'humaneval_C_InsertNoopcode_pattern_continuation_ptr',
    # 'humaneval_C_InsertNoopcode_lexical_trigger_div0',
    # 'humaneval_C_InsertNoopcode_lexical_trigger_nullptr',
    # 'humaneval_C_InsertNoopcode_lexical_trigger_bounds',
    # 'humaneval_C_InsertNoopcode_semantic_leakage_add', 'humaneval_C_InsertNoopcode_semantic_leakage_mul',
    # 'humaneval_C_InsertNoopcode_semantic_leakage_sub',
    # 'humaneval_C_InsertNoopcode_comment_driven_factorial',
    # 'humaneval_C_InsertNoopcode_comment_driven_binsearch', 'humaneval_C_InsertNoopcode_comment_driven_sort',
    # 'humaneval_C_InsertNoopcode_type_driven_string_len', 'humaneval_C_InsertNoopcode_type_driven_vector_size',
    # 'humaneval_C_InsertNoopcode_type_driven_map_find',
    #'humaneval_C_InsertNoopcode_type_driven_string', 'humaneval_C_InsertNoopcode_type_driven_vector',
    'humaneval_C_InsertNoopcode_type_driven_queue',
    # 'humaneval_C_InsertNoopcode_api_prior_malloc',
    # 'humaneval_C_InsertNoopcode_api_prior_calloc', 'humaneval_C_InsertNoopcode_api_prior_buffer',
    # 'humaneval_C_InsertNoopcode_control_flow_for', 'humaneval_C_InsertNoopcode_control_flow_while',
    # 'humaneval_C_InsertNoopcode_control_flow_if'
]

if __name__ == '__main__':
    # CUDA_VISIBLE_DEVICES=1
    parser = argparse.ArgumentParser()
    parser.add_argument("-model_name", "-mn", type=str, default="Salesforce/codegen-16B-multi")
    parser.add_argument("-max_token", "-mt", type=int, default=256)
    # parser.add_argument("-file_name", type=str, default="humaneval_C_ChangeCodestyle")
    args = parser.parse_args()
    model_name = args.model_name
    # file_name = args.file_name
    max_token = args.max_token

    model_path = os.path.join(llm_path, model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path,
                                                 torch_dtype=torch.float16,
                                                 device_map="auto",
                                                 low_cpu_mem_usage=True, )
    print("=" * 40)
    print(model_name.replace('/', '_'))
    print("=" * 40)
    for file_name in tqdm(tmp):
        file_name = f'humaneval/{file_name}.jsonl'
        answer = []

        source_data = read_from_jsonl(file_name)
        save_path = f"Answer/{model_name}/{file_name}"
        dir_path = os.path.dirname(save_path)
        os.makedirs(dir_path, exist_ok=True)

        for item in tqdm(source_data, desc="Generating code completions"):
            answer.append(generate_func(item['prompt'], tokenizer=tokenizer, model=model, max_token=max_token))

        write_to_jsonl(answer, save_path)
