#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author: DirtyBoy
@Date: 2026/6/15 10:45
"""
import json

def read_from_jsonl(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line.strip()))
    return data


def count_whitespace(code: str) -> dict:
    code = code.split("int main")[0]
    spaces   = code.count(' ')
    newlines = code.count('\n')
    return {
        'spaces':   spaces,
        'newlines': newlines,
    }
# model = "bigcode/starcoder2-3b" #"Salesforce/codegen-350M-multi"
# source = read_from_jsonl(f"../Answer/{model}/humaneval/humaneval_C.jsonl")
# newline_data = read_from_jsonl(f"../Answer/{model}/humaneval/humaneval_C_InsertNoopcode_CodeStyle_newline.jsonl")
# space_data = read_from_jsonl(f"../Answer/{model}/humaneval/humaneval_C_InsertNoopcode_CodeStyle_space.jsonl")
# line = 0
# space = 0
# for i in range(len(source)):
#     s = count_whitespace(source[i])
#     l = count_whitespace(newline_data[i])
#     p = count_whitespace(space_data[i])
#
#     if l["newlines"] > s["newlines"]:
#         line += 1
#     if p["spaces"] > s["spaces"]:
#         space += 1
# print(line)
# print(space)

data = read_from_jsonl("humaneval_C_InsertNoopcode_semantic_leakage_Add.jsonl")
print(data[0]['prompt'])


