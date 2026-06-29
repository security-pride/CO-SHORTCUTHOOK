#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author: DirtyBoy
@Date: 2026/4/21 13:49
"""
import json
import subprocess
import tempfile
import os, argparse
from tqdm import tqdm
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


def run_cpp_test(code: str, timeout=5):
    with tempfile.TemporaryDirectory() as tmpdir:
        cpp_path = os.path.join(tmpdir, "test.cpp")
        exe_path = os.path.join(tmpdir, "test_exec")

        with open(cpp_path, "w") as f:
            f.write(code)

        compile_proc = subprocess.run(
            ["g++", cpp_path, "-std=c++11", "-O2", "-o", exe_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if compile_proc.returncode != 0:
            return {
                "status": "compile_error",
                "error": compile_proc.stderr
            }

        try:
            run_proc = subprocess.run(
                [exe_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "timeout",
                "error": "timeout"
            }

        if run_proc.returncode == 0:
            return {"status": "pass",
                    "error": "success"}
        else:
            return {
                "status": "fail",
                "error": run_proc.stderr
            }


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


if __name__ == '__main__':
    my_parser = argparse.ArgumentParser()
    my_parser.add_argument("-model_name", "-mn", type=str, default="Salesforce/codegen-2B-multi")
    my_parser.add_argument("-is_finetune", "-ft", type=str, default="vanilla")
    args = my_parser.parse_args()
    is_finetune = args.is_finetune
    model_name = args.model_name
    print("=" * 40)
    print(model_name)
    print("=" * 40)
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
    if is_finetune == 'vd':
        answer_path = "Answer_finetune"
    elif is_finetune == "vanilla":
        answer_path = "Answer"
    else:
        answer_path = "Answer_codetrans"
    for file_name in tmp:
        if not os.path.isfile(f"./{answer_path}/{model_name}/humaneval/{file_name}_execution.jsonl"):
            data = read_from_jsonl(f"humaneval/{file_name}.jsonl")
            generate_code = read_from_jsonl(f"{answer_path}/{model_name}/humaneval/{file_name}_extracted.jsonl")
            # dict_keys(['task_id', 'prompt', 'canonical_solution', 'test', 'declaration', 'example_test'])
            print(file_name)
            ERROR_list = []
            n, z, q, j, p = 0, 0, 0, 0, 0
            for i, item in enumerate(tqdm(generate_code, desc="Evaluating")):
                if file_name == "humaneval_C_RenameFunction":
                    test_case = data[i]["test"].replace(get_func_name(data[i]["declaration"]), "my_function")
                else:
                    test_case = data[i]["test"]
                try:
                    result = run_cpp_test(item + "\n" + test_case)
                    status = result["status"]
                    error = result["error"]

                    if status == "pass":
                        n += 1
                    elif status == "timeout":
                        z += 1
                    elif status == "fail":
                        q += 1
                    else:
                        j += 1
                    ERROR_list.append((status, '----', error))
                except Exception as e:
                    p += 1
                    ERROR_list.append("Extract func error")
            total = len(generate_code)

            # print("\n===== Evaluation Summary =====")
            # print(f"Total samples       : {total}")
            # print(f"Passed              : {n} ({n / total:.2%})")
            # print(f"Failed (Wrong Logic): {q} ({q / total:.2%})")
            # print(f"Timeout (Infinite)  : {z} ({z / total:.2%})")
            # print(f"Errors (Compile/Ex) : {j} ({j / total:.2%})")
            # print(f"Extraction Errors : {p} ({p / total:.2%})")
            # print("==============================")
            write_to_jsonl(ERROR_list, f"{answer_path}/{model_name}/humaneval/{file_name}_execution.jsonl")
            print("\n===== Evaluation Summary =====")
            print(f"Total samples       : {total}")
            print(f"Passed              : {n} ({n / total:.2%})")
            print(f"Errors (Compile/Ex) : {j + q + z + p} ({(j + q + z + p) / total:.2%})")
            print("==============================")
        else:
            pass
