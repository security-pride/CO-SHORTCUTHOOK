#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author: DirtyBoy
@Date: 2026/4/21 14:44
"""
from tree_sitter import Language, Parser
from tqdm import tqdm
import random, subprocess, argparse, json, os, re, copy

C_LANGUAGE = Language('../shortcut_analysis/build/my-languages.so', 'cpp')
parser = Parser()
parser.set_language(C_LANGUAGE)


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


def modify_var_name_main(code):
    source_code = code
    code_bytes = code.encode('utf-8')
    tree = parser.parse(code_bytes)
    root_node = tree.root_node.children[0]
    comment, function_name, parameter_list, preproc_include, function_definition = get_func_var_name(code)
    for child in tree.root_node.children:
        if child.type == 'function_definition':
            code = code_bytes[child.start_byte:child.end_byte].decode('utf-8')

    def modify_var_name(node, code_bytes, old_var, new_var, modified_code, modified_num=0):
        for child in node.children:
            _, modified_num = modify_var_name(child, code_bytes, old_var, new_var, modified_code, modified_num)

        if node.type == 'identifier' and code_bytes[node.start_byte:node.end_byte] == old_var:
            old_len = len(old_var)
            new_len = len(new_var)
            len_sub = new_len - old_len

            if new_len > old_len:
                modified_code[
                node.start_byte + len_sub * modified_num:node.start_byte + new_len + len_sub * modified_num] = new_var.encode(
                    'utf-8')
                modified_code[
                node.start_byte + new_len + len_sub * modified_num:] = code_bytes[node.end_byte:]
                modified_num += 1
            elif new_len < old_len:
                modified_code[
                node.start_byte + modified_num * len_sub:node.end_byte + modified_num * len_sub] = new_var.encode(
                    'utf-8')
                modified_num += 1
            else:
                modified_code[node.start_byte:node.end_byte] = new_var.encode('utf-8')
        return modified_code, modified_num

    code_bytes = code.encode('utf-8')
    tree = parser.parse(code_bytes)
    root_node = tree.root_node.children[0]
    identifier_key = 'var'
    for i, old_func_name in enumerate(parameter_list):
        code_bytes = code.encode('utf-8')
        tree = parser.parse(code_bytes)
        root_node = tree.root_node.children[0]
        modified_code = bytearray(code_bytes)
        identifier_name = f'{identifier_key}{i + 1}'
        modified_code, modified_num = modify_var_name(root_node, code_bytes, old_func_name.encode("utf-8"),
                                                      identifier_name,
                                                      modified_code)
        code = modified_code.decode()
    func_header, func_body = code.split("/*##123456789##*/")
    source_code, _ = source_code.split("/*##123456789##*/")
    code_bytes = source_code.encode('utf-8')
    tree = parser.parse(code_bytes)
    root_node = tree.root_node.children

    for child in root_node:
        if child.type == 'function_definition':
            code_str = code_bytes.decode('utf-8')
            start = child.start_byte
            new_code = code_str[:start] + func_header

    return new_code, func_body, len(parameter_list) > 0


def get_func_var_name(code):
    code_bytes = code.encode('utf-8')
    tree = parser.parse(code_bytes)
    root_node = tree.root_node.children
    parameter_list = []
    function_name = b""
    comment = b""
    preproc_include = []
    for child in root_node:
        if child.type == 'comment':
            comment = code_bytes[child.start_byte: child.end_byte]
        elif child.type == 'function_definition':
            function_definition = code_bytes[child.start_byte: child.end_byte]
            for tmp_node in child.children:
                if tmp_node.type == 'function_declarator':
                    for n in tmp_node.children:
                        if n.type == 'identifier':
                            function_name = code_bytes[n.start_byte: n.end_byte]
                        if n.type == 'parameter_list' and n.child_count:
                            for t_n in n.children:
                                if t_n.type == 'parameter_declaration':
                                    if t_n.child_count == 1:
                                        parameter_list.append(code_bytes[t_n.start_byte: t_n.end_byte])
                                    else:
                                        for t_n_c in t_n.children:
                                            if t_n_c.type == 'identifier':
                                                parameter_list.append(code_bytes[t_n_c.start_byte: t_n_c.end_byte])
                                            if t_n_c.type == 'pointer_declarator':
                                                for t_n_c_c in t_n_c.children:
                                                    if t_n_c_c.type == 'identifier':
                                                        parameter_list.append(
                                                            code_bytes[t_n_c_c.start_byte: t_n_c_c.end_byte])
        else:
            preproc_include.append(code_bytes[child.start_byte: child.end_byte])
    parameter_list = [item.decode() for item in parameter_list]
    preproc_include = [item.decode() for item in preproc_include]
    return comment.decode(), function_name.decode(), parameter_list, preproc_include, function_definition.decode()


def insert_style_trigger(code, trigger_type='space'):
    code_bytes = code.encode('utf-8')
    tree = parser.parse(code_bytes)
    root_node = tree.root_node.children
    ending = {"include": []}
    for child in root_node:
        if child.type == 'comment':
            comment = code_bytes[child.start_byte: child.end_byte]
            ending["comment"] = comment
        elif child.type == 'function_definition':
            function_definition = code_bytes[child.start_byte: child.end_byte]
            ending['function_definition'] = function_definition
        else:
            ending["include"].append(code_bytes[child.start_byte: child.end_byte])

    def inject_extra_spaces(ending: dict) -> str:
        new = {}
        try:
            new['comment'] = ending['comment']
        except KeyError:
            pass

        new['include'] = [
            re.sub(rb'#include<(\S+)>', rb'#include <\1>', inc)
            for inc in ending['include']
        ]

        fd = ending['function_definition'].decode()
        fd = re.sub(r'vector<(\w+)>', r'vector< \1 >', fd)
        fd = re.sub(r',\s+', ',', fd)  # 先归一化
        fd = re.sub(r',', ',  ', fd)  # 再注入双空格
        fd = fd.replace('){', ') {')
        new['function_definition'] = fd.encode()

        parts = []
        try:
            parts.append(new['comment'].decode())
        except KeyError:
            pass
        for inc in new['include']:
            parts.append(inc.decode().strip())
        parts.append(new['function_definition'].decode())

        return '\n'.join(parts)

    def inject_extra_newlines(sample: dict) -> str:
        new = {}
        try:
            new['comment'] = ending['comment']
        except KeyError:
            pass
        new['include'] = sample['include']

        # function_definition: 参数换行 + 花括号独占一行
        fd = sample['function_definition'].decode()

        # 提取函数名和参数部分
        # bool has_close_elements(vector<float> numbers, float threshold){
        match = re.match(r'(.*?\()(.+)(\){)', fd)
        if match:
            prefix = match.group(1)  # bool has_close_elements(
            params = match.group(2)  # vector<float> numbers, float threshold
            suffix = match.group(3)  # ){

            # 每个参数单独一行，4空格缩进
            param_list = [p.strip() for p in params.split(',')]
            params_newline = ',\n    '.join(param_list)

            fd = f"{prefix}\n    {params_newline}\n){{"

        new['function_definition'] = fd.encode()

        parts = []
        try:
            parts.append(new['comment'].decode())
        except KeyError:
            pass
        parts.append('')
        for inc in new['include']:
            parts.append(inc.decode().strip())
            parts.append('')
        parts.append('')
        parts.append(new['function_definition'].decode())

        return '\n\n'.join(parts)

    if trigger_type == 'space':
        return inject_extra_spaces(ending)
    elif trigger_type == 'newline':
        return inject_extra_newlines(ending)


def rebuild_code(code):
    comment, function_name, parameter_list, preproc_include, function_definition = get_func_var_name(code)
    random.shuffle(preproc_include)
    func_header = function_definition
    code_parts = preproc_include
    code_parts.append(func_header)
    code_parts.append(comment)
    new_code = "\n".join(code_parts)

    def format_code_with_clang_format(code: str, style: str = "google") -> str:
        try:
            result = subprocess.run(
                ["clang-format", f"--style={style}"],
                input=code,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"clang-format 执行失败: {e.stderr}")
            return code

    new_code = format_code_with_clang_format(new_code)
    return new_code


def modify_func_name_main(code):
    comment, function_name, parameter_list, preproc_include, function_definition = get_func_var_name(code)
    code = code.replace(function_name, "my_function")

    return code


NOOP_CODE = {
    # ========== pattern_continuation (编号命名模式) ==========
    "pattern_continuation_var": (
        "    int var1 = 0;\n"
        "    int var2 = 0;\n"
        "    int var3 = 0;\n"
        "    int var4 = 0;\n"
        "    int var5 = 0;"
    ),
    "pattern_continuation_num": (
        "    float num1 = 0.0;\n"
        "    float num2 = 0.0;\n"
        "    float num3 = 0.0;\n"
        "    float num4 = 0.0;\n"
        "    float num5 = 0.0;"
    ),
    "pattern_continuation_ptr": (
        "    int *ptr1 = 0;\n"
        "    int *ptr2 = 0;\n"
        "    int *ptr3 = 0;\n"
        "    int *ptr4 = 0;\n"
        "    int *ptr5 = 0;"
    ),

    # ========== lexical_trigger (关键词触发) ==========
    "lexical_trigger_div0": (
        "    // TODO: fix division by zero bug\n"
        "    // ensure denominator is not zero before division\n"
        "    int denominator = 0;"
    ),
    "lexical_trigger_nullptr": (
        "    // TODO: check for null pointer dereference\n"
        "    // validate pointer before dereferencing\n"
        "    int* var_ptr = 0;"
    ),
    "lexical_trigger_bounds": (
        "    // FIXME: possible array index out of bounds\n"
        "    // ensure index is within array size\n"
        "    int var_arr[10];\n"
        "    int var_idx = 10;"
    ),

    # ========== semantic_leakage (变量名语义泄漏) ==========
    "semantic_leakage_Add": (
        "    int addend = 1;\n"
        "    int augend = 2;\n"
        "    int var_sum = 0;"
    ),
    "semantic_leakage_Mul": (
        "    int multiplier = 3;\n"
        "    int multiplicand = 4;\n"
        "    int product = 0;"
    ),
    "semantic_leakage_Sub": (
        "    int subtract = 10;\n"
        "    int subtrahend = 5;\n"
        "    int difference = 0;"
    ),
    # ========== comment_driven (注释驱动) ==========
    "comment_driven_factorial": (
        "    // TODO: compute factorial using recursion\n"
        "    // base case: n == 0 returns 1\n"
        "    // recursive step: n * factorial(n - 1)"
    ),
    "comment_driven_binsearch": (
        "    // TODO: implement binary search on sorted array\n"
        "    // return index if found, -1 otherwise"
    ),
    "comment_driven_sort": (
        "    // TODO: sort array using bubble sort\n"
        "    // repeatedly swap adjacent elements if out of order"
    ),

    # ========== type_driven (类型驱动) ==========
    "type_driven_string": (
        "    string var_string = \"hello\";\n"
        "    int var_len = var_string.length();"
    ),
    "type_driven_vector": (
        "    vector<int> var_vec = {1, 2, 3};"
    ),
    "type_driven_queue": (
        "    queue<int> var_queue;"
    ),

    # ========== api_prior (API 先验) ==========
    "api_prior_malloc": (
        "    int *var0 = (int*)malloc(sizeof(int));"
    ),
    "api_prior_calloc": (
        "    int *var1 = (int*)calloc(1, sizeof(int));"
    ),
    "api_prior_fopen": (
        "    FILE *var_file = fopen(\"data.txt\", \"r\");"
    ),

    # ========== control_flow (控制流结构) ==========
    "control_flow_for": (
        "    for (int var0 = 0; var0 < 5; var0++) {\n"
        "        // process element\n"
        "    }"
    ),
    "control_flow_while": (
        "    int var_count = 5;\n"
        "    while (var_count > 0) {\n"
        "        // process item\n"
        "        var_count--;\n"
        "    }"
    ),
    "control_flow_if": (
        "    int var_flag = 1;\n"
        "    if (var_flag) {\n"
        "        // execute branch\n"
        "    } else {\n"
        "        // do otherwise\n"
        "    }"
    ),
}


def insert_noop_code(code, noop_type="mixed_pattern"):
    noop_code = NOOP_CODE[noop_type]
    if not code.endswith("\n"):
        code += "\n"
        return code + noop_code
    else:
        return code + noop_code + "\n"


if __name__ == '__main__':
    # ['task_id', 'prompt', 'canonical_solution', 'test', 'declaration', 'example_test'])
    my_parser = argparse.ArgumentParser()
    my_parser.add_argument("-mode", type=str, default="CodeStyle",
                           choices=["ChangeCodestyle", "RenameFunction",
                                    "RenameVariable", "InsertNoopcode", "CodeStyle"])
    args = my_parser.parse_args()
    mode = args.mode
    source_data = read_from_jsonl('humaneval/humaneval_C.jsonl')
    if mode == "ChangeCodestyle":
        for item in tqdm(source_data, desc="ChangeCodestyle"):
            source_code = item['prompt']
            new_code = rebuild_code(source_code)
            item['prompt'] = new_code
    elif mode == "RenameFunction":
        for item in tqdm(source_data, desc="RenameFunction"):
            source_code = item['prompt']
            new_code = modify_func_name_main(source_code)
            item['prompt'] = new_code
    elif mode == "RenameVariable":
        for item in tqdm(source_data, desc="RenameVariable"):
            item["prompt"], item["canonical_solution"], flag = modify_var_name_main(
                item["prompt"] + '\n/*##123456789##*/\n' + item["canonical_solution"])
    elif mode == "InsertNoopcode":
        for noop_type in list(NOOP_CODE.keys()):
            data_copy = copy.deepcopy(source_data)
            for item in tqdm(data_copy, desc=f"InsertNoopcode_{noop_type}"):
                item["prompt"] = insert_noop_code(item['prompt'], noop_type)
            write_to_jsonl(data_copy, f'humaneval/humaneval_C_{mode}_{noop_type}.jsonl')
    elif mode == "CodeStyle":
        for noop_type in ['space', 'newline']:
            data_copy = copy.deepcopy(source_data)
            for item in tqdm(data_copy, desc=f"ChangeCodeStyle [{noop_type}]"):
                item["prompt"] = insert_style_trigger(item['prompt'], noop_type)

            write_to_jsonl(data_copy, f'humaneval/humaneval_C_{mode}_{noop_type}.jsonl')

    if mode != "InsertNoopcode":
        write_to_jsonl(source_data, f'humaneval/humaneval_C_{mode}.jsonl')
