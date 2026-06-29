#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author: DirtyBoy
@Date: 2026/4/20 15:59
"""
from tree_sitter import Language, Parser
from tqdm import tqdm
import random, subprocess, argparse, json, os

C_LANGUAGE = Language('../shortcut_analysis/build/my-languages.so', 'cpp')
parser = Parser()
parser.set_language(C_LANGUAGE)


def get_func_name(code):
    code_bytes = code.encode('utf-8')
    tree = parser.parse(code_bytes)
    root_node = tree.root_node.children
    function_name = b""
    for child in root_node:
        if child.type == 'function_definition':
            for tmp_node in child.children:
                if tmp_node.type == 'function_declarator':
                    for n in tmp_node.children:
                        if n.type == 'identifier':
                            function_name = code_bytes[n.start_byte: n.end_byte]

    return function_name.decode()


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


def extract_function(code, function_name):
    code_bytes = code.encode('utf-8')
    tree = parser.parse(code_bytes)
    root = tree.root_node.children

    for node in root:
        if node.type == "function_definition" and function_name in code_bytes[node.start_byte:node.end_byte].decode():
            return code_bytes[:node.end_byte].decode()

    return False


tmp = [  # "humaneval_C",
    # 'humaneval_C_InsertNoopcode_CodeStyle_newline',
    # 'humaneval_C_InsertNoopcode_CodeStyle_space',
    # 'humaneval_C_InsertNoopcode_pattern_continuation_ptr',
    # 'humaneval_C_InsertNoopcode_lexical_trigger_div0',
    # 'humaneval_C_InsertNoopcode_lexical_trigger_nullptr',
    # 'humaneval_C_InsertNoopcode_lexical_trigger_bounds',
    'humaneval_C_InsertNoopcode_semantic_leakage_add', 'humaneval_C_InsertNoopcode_semantic_leakage_mul',
    'humaneval_C_InsertNoopcode_semantic_leakage_sub',
    # 'humaneval_C_InsertNoopcode_comment_driven_factorial',
    # 'humaneval_C_InsertNoopcode_comment_driven_binsearch', 'humaneval_C_InsertNoopcode_comment_driven_sort',
    # 'humaneval_C_InsertNoopcode_type_driven_string_len', 'humaneval_C_InsertNoopcode_type_driven_vector_size',
    # 'humaneval_C_InsertNoopcode_type_driven_map_find',
    'humaneval_C_InsertNoopcode_type_driven_string', 'humaneval_C_InsertNoopcode_type_driven_vector',
    'humaneval_C_InsertNoopcode_type_driven_queue',
    # 'humaneval_C_InsertNoopcode_api_prior_malloc',
    # 'humaneval_C_InsertNoopcode_api_prior_calloc', 'humaneval_C_InsertNoopcode_api_prior_buffer',
    # 'humaneval_C_InsertNoopcode_control_flow_for', 'humaneval_C_InsertNoopcode_control_flow_while',
    # 'humaneval_C_InsertNoopcode_control_flow_if'
]


def main_(model_name, is_finetune="vanilla"):
    if is_finetune == 'vd':
        answer_path = "Answer_finetune"
    elif is_finetune == "vanilla":
        answer_path = "Answer"
    else:
        answer_path = "Answer_codetrans"
    for file_name in tqdm(tmp):
        source_data = read_from_jsonl(f'humaneval/{file_name}.jsonl')
        generate_data = read_from_jsonl(f"{answer_path}/{model_name}/humaneval/{file_name}.jsonl")
        extracted_answer = []
        n = 0
        for index in tqdm(range(len(source_data)), desc=f"extracte {file_name}"):
            prompt = source_data[index]["prompt"]
            generate_code = generate_data[index]
            if file_name != "humaneval_C_RenameFunction":
                function_name = get_func_name(source_data[index]["declaration"])
            else:
                function_name = "my_function"
            code = prompt + generate_code
            tmp_answer = extract_function(code, function_name)
            extracted_answer.append(tmp_answer)
            if not tmp_answer:
                n += 1
        print(
            f"success extract {len(source_data) - n} samples to {answer_path}/{model_name}/humaneval/{file_name}_extracted.jsonl")
        write_to_jsonl(extracted_answer, f"{answer_path}/{model_name}/humaneval/{file_name}_extracted.jsonl")


if __name__ == '__main__':
    my_parser = argparse.ArgumentParser()
    my_parser.add_argument("-model_name", "-mn", type=str, default="Salesforce/codegen-2B-multi")
    my_parser.add_argument("-is_finetune", "-ft", type=str, default="vanilla")
    args = my_parser.parse_args()
    is_finetune = args.is_finetune
    model_name = args.model_name

    print('=' * 40)
    print(model_name)
    main_(model_name, is_finetune=is_finetune)
    print('=' * 40)
