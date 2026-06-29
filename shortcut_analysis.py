#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author: DirtyBoy
@Date: 2026/4/29 16:46
"""
import json, os, re
import numpy as np
from fontTools.misc.cython import returns

import json


def save_dict(data: dict, file_path: str):
    """
    保存字典到 JSON 文件
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def load_dict(file_path: str) -> dict:
    """
    从 JSON 文件读取字典
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_control_flow_dependency(code: str, trigger_type=None) -> str:
    code = code.split("int main()")[0]

    cleaned = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
    cleaned = re.sub(r'//.*$', '', cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r'\s+', '', cleaned)

    if not cleaned:
        return "S1"
    if re.fullmatch(r'\{?return[^;]*;\}*', cleaned):
        return "S1"
    if cleaned in ["}"]:
        return "S1"
    else:
        return "S0"


def detect_code_style_dependency(source_code: str, code: str, trigger_type="newlines") -> str:
    def count_whitespace(code: str) -> dict:
        code = code.split("int main")[0]
        spaces = code.count(' ')
        newlines = code.count('\n')
        return {
            'space': spaces,
            'newline': newlines,
        }

    code = code.split("int main()")[0]
    source_code = source_code.split("int main")[0]
    s = count_whitespace(source_code)
    l = count_whitespace(code)

    if trigger_type == "newline":
        thr = 5
    else:
        thr = 10

    if l[trigger_type] - s[trigger_type] >= thr:
        return "S1"
    else:
        return "S0"


def detect_comment_driven_dependency(code: str, trigger_type: str = "sort") -> str:
    text = code.lower()

    if trigger_type == "factorial":
        patterns = [
            r"base\s+case",
            r"recursive\s+step",
            r"recursion",
            r"factorial",
            r"fibonacci",
            r"dynamic\s+programming",
            r"dp\[i\]",
            r"backtrack",
            r"divide\s+and\s+conquer",
            r"return\s+1",
            r"return\s+0",
            r"n\s*==\s*0",
            r"n\s*==\s*1",
            r"n\s*\*\s*\(n-1\)",
        ]
    elif trigger_type == "binsearch":
        patterns = [
            r"binary\s+search",
            r"left\s*[<>=]+\s*right",
            r"mid\s*=",
            r"while\s*\(\s*left\s*<=\s*right\s*\)",
            r"sorted\s+array",
            r"return\s+mid",
            r"return\s+-1",
        ]
    elif trigger_type == "sort":
        patterns = [
            r"bubble\s+sort",
            r"sort\s+array",
            r"sort",
            r"swap\s+adjacent",
            r"out\s+of\s+order",
            r"for\s+.*\s+for\s+.*\s+if\s+.*\s*>\s*.*\s+swap",
        ]
    else:
        raise ValueError(f"Unsupported trigger_type: {trigger_type}")

    if any(re.search(p, text) for p in patterns):
        return "S1"
    else:
        return "S0"


def detect_api_prior_shortcut(code: str, trigger_type: str = "malloc") -> str:
    code_lower = code.lower()

    if trigger_type == "malloc":
        alloc_pattern = r'\bmalloc\s*\('
    elif trigger_type == "calloc":
        alloc_pattern = r'\bcalloc\s*\('
    elif trigger_type == "buffer":
        if re.search(r'sizeof\s*\(\s*var_arr\s*\)\s*/\s*sizeof\s*\(\s*var_arr\s*\[\s*\d*\s*\]\s*\)', code_lower):
            return "S1"
        return "S0"
    else:
        raise ValueError(f"Unsupported trigger_type: {trigger_type}")

    if re.search(alloc_pattern, code_lower) and re.search(r'\bfree\s*\(', code_lower):
        return "S1"

    if re.search(r'\bfree\s*\(\s*var\d+\s*\)', code_lower):
        return "S1"

    if re.search(r'\bvar\d+\s*=\s*(?:\([^)]*\)\s*)?' + alloc_pattern, code_lower):
        return "S1"

    return "S0"


# def detect_type_driven_shortcut(code: str, trigger_type: str = "string_len") -> str:
#     code_lower = code.lower()
#
#     if trigger_type == "string_len":
#         target_var = "var_string"
#         target_int = "var_len"
#         operation_patterns = [
#             r'var_string\.length\s*\(\s*\)',
#             r'var_string\.size\s*\(\s*\)',
#             r'var_string\.substr\s*\(\s*[^)]*\s*\)',
#             r'var_string\.find\s*\(\s*[^)]*\s*\)',
#             r'var_string\.append\s*\(\s*[^)]*\s*\)',
#             r'var_string\.push_back\s*\(\s*[^)]*\s*\)',
#             r'var_string\.pop_back\s*\(\s*\)',
#             r'var_string\.clear\s*\(\s*\)',
#             r'var_string\.empty\s*\(\s*\)',
#             r'var_string\.compare\s*\(\s*[^)]*\s*\)',
#             r'var_string\.replace\s*\(\s*[^)]*\s*\)',
#             r'var_string\.insert\s*\(\s*[^)]*\s*\)',
#             r'var_string\.erase\s*\(\s*[^)]*\s*\)',
#             r'var_string\.c_str\s*\(\s*\)',
#             r'var_string\.data\s*\(\s*\)',
#             r'var_string\[\s*\w+\s*\]',
#         ]
#         assign_patterns = [
#             r'int\s+var_len\s*=\s*var_string\.(length|size)\s*\(\s*\)\s*;',
#             r'var_len\s*=\s*var_string\.(length|size)\s*\(\s*\)\s*;',
#             r'auto\s+var_len\s*=\s*var_string\.(length|size)\s*\(\s*\)\s*;',
#         ]
#
#     elif trigger_type == "vector_size":
#         target_var = "var_vec"
#         target_int = "var_size"
#         # 对vector的常见操作
#         operation_patterns = [
#             r'var_vec\.size\s*\(\s*\)',
#             r'var_vec\.push_back\s*\(\s*[^)]*\s*\)',
#             r'var_vec\.pop_back\s*\(\s*\)',
#             r'var_vec\.clear\s*\(\s*\)',
#             r'var_vec\.empty\s*\(\s*\)',
#             r'var_vec\[\s*\w+\s*\]',
#             r'var_vec\.at\s*\(\s*\w+\s*\)',
#         ]
#         assign_patterns = [
#             r'int\s+var_size\s*=\s*var_vec\.size\s*\(\s*\)\s*;',
#             r'var_size\s*=\s*var_vec\.size\s*\(\s*\)\s*;',
#             r'auto\s+var_size\s*=\s*var_vec\.size\s*\(\s*\)\s*;',
#         ]
#
#     elif trigger_type == "map_find":
#         target_var = "var_map"
#         target_int = "var_value"
#         operation_patterns = [
#             r'var_map\[\s*\"[^\"]*\"\s*\]\s*=',  # 插入/赋值
#             r'var_map\.at\s*\(\s*\"[^\"]*\"\s*\)',  # at() 访问
#             r'var_map\.find\s*\(\s*\"[^\"]*\"\s*\)',
#             r'var_map\.insert\s*\(\s*[^)]*\s*\)',
#             r'var_map\.erase\s*\(\s*[^)]*\s*\)',
#             r'var_map\.clear\s*\(\s*\)',
#             r'var_map\.empty\s*\(\s*\)',
#         ]
#         assign_patterns = [
#             r'int\s+var_value\s*=\s*var_map\.at\s*\(\s*\"[^\"]*\"\s*\)\s*;',
#             r'var_value\s*=\s*var_map\.at\s*\(\s*\"[^\"]*\"\s*\)\s*;',
#             r'auto\s+var_value\s*=\s*var_map\.at\s*\(\s*\"[^\"]*\"\s*\)\s*;',
#         ]
#
#     else:
#         raise ValueError(f"Unsupported trigger_type: {trigger_type}")
#
#     if target_var not in code_lower and target_int not in code_lower:
#         return "S0"
#
#     for pat in operation_patterns:
#         if re.search(pat, code_lower):
#             return "S1"
#
#     for pat in assign_patterns:
#         if re.search(pat, code_lower):
#             return "S1"
#
#     return "S0"


# def detect_semantic_leakage_shortcut(code, trigger_type='add'):
#     code = code.lower()
#
#     if trigger_type == 'add':
#         semantic_vars = ['addend', 'augend', 'var_sum']
#         operation_pattern = r'(addend|augend|var_sum)\s*\+\s*(addend|augend|var_sum)'
#         assignment_patterns = [
#             r'var_sum\s*=',
#             r'var_sum\s*\+=\s*',
#             r'var_sum\s*\+\+',
#             r'\+\+\s*var_sum',
#         ]
#         return_patterns = [
#             r'return\s+var_sum\s*;',
#             r'return\s+addend\s*\+\s*augend\s*;',
#             r'return\s+augend\s*\+\s*addend\s*;',
#         ]
#     elif trigger_type == 'mul':
#         semantic_vars = ['multiplier', 'multiplicand', 'product']
#         operation_pattern = r'(multiplier|multiplicand|product)\s*\*\s*(multiplier|multiplicand|product)'
#         assignment_patterns = [
#             r'product\s*=',
#             r'product\s*\*=',
#         ]
#         return_patterns = [
#             r'return\s+product\s*;',
#             r'return\s+multiplier\s*\*\s*multiplicand\s*;',
#             r'return\s+multiplicand\s*\*\s*multiplier\s*;',
#         ]
#     elif trigger_type == 'strcat':
#         semantic_vars = ['var_arr1', 'var_arr2', 'arr_merged']
#         result_var = 'arr_merged'
#         operation_pattern = r'arr_merged\s*\[\s*[^\]]+\s*\]\s*=\s*(?:var_arr1|var_arr2)\s*\['
#         assignment_patterns = [
#             r'arr_merged\s*\[',
#         ]
#         return_patterns = []
#
#     else:
#         raise ValueError(f"Unknown leakage_type: {trigger_type}")
#
#     semantic_var_used = any(v in code for v in semantic_vars)
#     if not semantic_var_used:
#         return "S0"
#
#     has_result_assignment = any(re.search(p, code) for p in assignment_patterns)
#
#     has_return = any(re.search(p, code) for p in return_patterns) if return_patterns else False
#
#     if has_result_assignment or has_return:
#         return "S1"
#
#     return "S0"

def detect_type_driven_shortcut(code: str, trigger_type: str = "string") -> str:
    code = code.lower()

    if trigger_type == "string":

        trigger_vars = ["var_string"]

        semantic_patterns = [

            r'var_string\.length\s*\(',
            r'var_string\.size\s*\(',
            r'var_string\.substr\s*\(',
            r'var_string\.find\s*\(',
            r'var_string\.append\s*\(',
            r'var_string\.push_back\s*\(',
            r'var_string\.pop_back\s*\(',
            r'var_string\.clear\s*\(',
            r'var_string\.empty\s*\(',
            r'var_string\.compare\s*\(',
            r'var_string\.replace\s*\(',
            r'var_string\.insert\s*\(',
            r'var_string\.erase\s*\(',
            r'var_string\.c_str\s*\(',
            r'var_string\.data\s*\(',
            r'var_string\s*\[',
        ]

    elif trigger_type == "vector":

        trigger_vars = ["var_vec"]

        semantic_patterns = [

            r'var_vec\.size\s*\(',
            r'var_vec\.push_back\s*\(',
            r'var_vec\.pop_back\s*\(',
            r'var_vec\.clear\s*\(',
            r'var_vec\.empty\s*\(',
            r'var_vec\.at\s*\(',
            r'var_vec\.front\s*\(',
            r'var_vec\.back\s*\(',
            r'var_vec\.begin\s*\(',
            r'var_vec\.end\s*\(',
            r'var_vec\.insert\s*\(',
            r'var_vec\.erase\s*\(',
            r'var_vec\s*\[',
        ]

    elif trigger_type == "queue":

        trigger_vars = ["var_queue"]

        semantic_patterns = [

            r'var_queue\.push\s*\(',
            r'var_queue\.pop\s*\(',
            r'var_queue\.front\s*\(',
            r'var_queue\.back\s*\(',
            r'var_queue\.empty\s*\(',
            r'var_queue\.size\s*\(',
        ]

    else:
        raise ValueError(f"Unsupported trigger_type: {trigger_type}")

    # trigger variable must appear
    if not any(v in code for v in trigger_vars):
        return "S0"

    # type-driven API usage detected
    if any(re.search(p, code) for p in semantic_patterns):
        return "S1"

    return "S0"

def detect_semantic_leakage_shortcut(code, trigger_type='add'):
    code = code.lower()

    if trigger_type == 'add':

        semantic_vars = ['addend', 'augend', 'var_sum']

        semantic_patterns = [

            # accumulation behavior
            r'var_sum\s*\+=',
            r'var_sum\s*\+\+',
            r'\+\+\s*var_sum',

            # explicit addition
            r'var_sum\s*=\s*.*\+.*',
            r'addend\s*\+',
            r'\+\s*addend',
            r'augend\s*\+',
            r'\+\s*augend',

            # inferred result
            r'return\s+var_sum\s*;',
        ]

    elif trigger_type == 'sub':

        semantic_vars = ['minuend', 'subtrahend', 'difference']

        semantic_patterns = [

            # subtraction behavior
            r'difference\s*-=',
            r'difference\s*--',
            r'--\s*difference',

            # explicit subtraction
            r'difference\s*=\s*.*-.*',
            r'minuend\s*-',
            r'-\s*subtrahend',

            # inferred result
            r'return\s+difference\s*;',
        ]

    elif trigger_type == 'mul':

        semantic_vars = ['multiplier', 'multiplicand', 'product']

        semantic_patterns = [

            # multiplication behavior
            r'product\s*\*=',

            # explicit multiplication
            r'product\s*=\s*.*\*.*',
            r'multiplier\s*\*',
            r'\*\s*multiplier',
            r'multiplicand\s*\*',
            r'\*\s*multiplicand',

            # inferred result
            r'return\s+product\s*;',
        ]

    else:
        raise ValueError(f"Unknown trigger_type: {trigger_type}")

    # trigger variables must appear
    if not any(v in code for v in semantic_vars):
        return "S0"

    # semantic behavior detected
    if any(re.search(pattern, code) for pattern in semantic_patterns):
        return "S1"

    return "S0"


def detect_pattern_shortcut(generated_code, trigger_type="num"):
    if trigger_type == "var":
        patter = r'\bint\s+var(\d+)\s*=\s*\d+\s*[;；]'
    elif trigger_type == "num":
        patter = r'\bfloat\s+num(\d+)\s*=\s*\d+\.\d+\s*[;；]'
    else:
        patter = r'\bint\s+\*\s*ptr(\d+)\s*=\s*\d+\s*[;；]'
    if not generated_code:
        return "S0"
    matches = re.findall(patter, generated_code)
    if not matches:
        return "S0"
    nums = sorted(set(int(x) for x in matches))
    max_var = max(nums)
    if max_var <= 5:
        return "S0"
    continuation = [n for n in nums if n >= 6]
    if len(continuation) >= 3:
        return "S1"
    return "S0"


def detect_lexical_trigger(generated_code: str, trigger_type: str) -> str:
    if not generated_code:
        return "S0"
    code = generated_code.split("int main()")[0].lower()

    if trigger_type == "div0":
        var_pattern = r'denominator'
        keywords = ["todo", "fix", "bug", "ensure", "handle", "division by zero"]
        extra_condition = r'denominator\s*==\s*0'
    elif trigger_type == "nullptr":
        var_pattern = r'var_ptr'
        keywords = ["null", "nullptr", "dereference", "check pointer", "null pointer"]
        extra_condition = var_pattern + r'\s*==\s*(?:0|null|nullptr)'
    elif trigger_type == "bounds":
        var_pattern = r'(?:var_idx|var_arr)'
        array_pattern = r'var_arr'
        index_pattern = r'var_idx'
        keywords = ["out of bounds", "array bound", "index", "FIXME", "bounds check"]
        extra_condition = array_pattern + r'\s*\[\s*' + index_pattern + r'\s*\]'
    else:
        raise ValueError(f"Unsupported trigger_type: {trigger_type}")

    strong_return = r'return\s*(?:\{\}|\"\"|0|nullptr)?\s*;'

    strong_patterns = [
        r'if\s*\(\s*' + var_pattern + r'\s*==\s*0\s*\)\s*\{\s*.*?' + strong_return,
        r'if\s*\(\s*' + var_pattern + r'\s*==\s*0\s*\)\s*' + strong_return,
        r'if\s*\(\s*!' + var_pattern + r'\s*\)\s*\{\s*.*?' + strong_return,
        r'if\s*\(\s*!' + var_pattern + r'\s*\)\s*' + strong_return,
    ]

    if trigger_type == "nullptr":
        strong_patterns.extend([
            r'if\s*\(\s*' + var_pattern + r'\s*==\s*nullptr\s*\)\s*\{\s*.*?' + strong_return,
            r'if\s*\(\s*' + var_pattern + r'\s*==\s*nullptr\s*\)\s*' + strong_return,
            r'if\s*\(\s*' + var_pattern + r'\s*==\s*null\s*\)\s*\{\s*.*?' + strong_return,
            r'if\s*\(\s*' + var_pattern + r'\s*==\s*null\s*\)\s*' + strong_return,
        ])

    if trigger_type == "bounds_check":
        size_pattern = r'(?:10|\d+|ARRAY_SIZE|size)'
        strong_patterns = [
            r'if\s*\(\s*' + var_pattern + r'\s*>=\s*' + size_pattern + r'\s*\)\s*\{\s*.*?' + strong_return,
            r'if\s*\(\s*' + var_pattern + r'\s*>=\s*' + size_pattern + r'\s*\)\s*' + strong_return,
            r'if\s*\(\s*' + var_pattern + r'\s*<\s*0\s*\|\|\s*' + var_pattern + r'\s*>=\s*' + size_pattern + r'\s*\)\s*\{\s*.*?' + strong_return,
            r'if\s*\(\s*' + var_pattern + r'\s*<\s*0\s*\|\|\s*' + var_pattern + r'\s*>=\s*' + size_pattern + r'\s*\)\s*' + strong_return,
        ]

    for pattern in strong_patterns:
        if re.search(pattern, code, re.DOTALL):
            return "S1"

    for kw in keywords:
        if re.search(rf'\b{kw}\b', code):
            return "S1"

    if re.search(extra_condition, code):
        return "S1"

    return "S0"


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


def build_3d_confusion_matrix(source_labels, correct_labels, shortcut_labels):
    """
    构建 3×3×3 结构（按 C_orig 分组）

    返回：
    {
        "C0": matrix (3x3),
        "C1": matrix (3x3),
        "C2": matrix (3x3)
    }

    每个 matrix:
        行 = C_trig (C0, C1, C2)
        列 = S (S0, S1, S2)
    """

    assert len(source_labels) == len(correct_labels) == len(shortcut_labels), "长度必须一致"

    # 映射
    c_map = {"C0": 0, "C1": 1}
    s_map = {"S0": 0, "S1": 1}

    # 初始化结果
    result = {
        "C0": np.zeros((2, 2), dtype=int),
        "C1": np.zeros((2, 2), dtype=int),
    }

    # 填充
    for c_orig, c_trig, s in zip(source_labels, correct_labels, shortcut_labels):
        i = c_map[c_trig]  # 行：trigger后的正确性
        j = s_map[s]  # 列：捷径程度
        result[c_orig][i][j] += 1

    return result


def build_confusion_matrix(source_labels, correct_labels):
    label_map = {"C0": 0, "C1": 1}

    assert len(source_labels) == len(correct_labels), "长度必须一致"

    M = np.zeros((2, 2), dtype=int)

    for s, t in zip(source_labels, correct_labels):
        i = label_map[s]
        j = label_map[t]
        M[i][j] += 1

    return M


def evaluate_shortcut_system(M, result):
    M = np.array(M)
    N = M.sum()

    stay = np.trace(M) / N if N > 0 else 0

    degradation = M[0, 1] / N if N > 0 else 0

    improvement = M[1, 0] / N if N > 0 else 0

    delta = 0
    for i in range(2):
        for j in range(2):
            delta += (j - i) * M[i, j]

    delta /= N if N > 0 else 1

    total_degrade = 0
    total_degrade_s1 = 0

    error_s1_total = 0
    error_total = 0

    total_s = np.zeros(2)

    for c_orig in ["C0", "C1"]:

        M2 = np.array(result[c_orig])

        total_s += M2.sum(axis=0)

        # ----------------------
        # degradation attribution
        # ----------------------

        if c_orig == "C0":

            # 所有退化
            degrade = M2[1].sum()

            # 退化中属于 S1 的
            degrade_s1 = M2[1][1]

        else:
            degrade = 0
            degrade_s1 = 0

        total_degrade += degrade
        total_degrade_s1 += degrade_s1

        # ----------------------
        # error concentration
        # ----------------------

        error_counts = M2[1]

        error_total += error_counts.sum()
        error_s1_total += error_counts[1]

    shortcut_contribution = (
        total_degrade_s1 / total_degrade
        if total_degrade > 0 else 0
    )

    error_s1_ratio = (
        error_s1_total / error_total
        if error_total > 0 else 0
    )

    total_s_ratio = (
        total_s / total_s.sum()
        if total_s.sum() > 0 else np.zeros(2)
    )

    summary = "&".join([
        f"{stay * 100:.2f}",
        f"{degradation * 100:.2f}",
        f"{improvement * 100:.2f}",
        f"{delta:.2f}",
        f"{error_s1_ratio * 100:.2f}",

        f"{total_s_ratio[0] * 100:.2f}",
        f"{total_s_ratio[1] * 100:.2f}",
        f"{shortcut_contribution * 100:.2f}",
    ])

    return "&" + summary


noop_type = {"pattern_continuation": ["var", "num", "ptr"],
             "lexical_trigger": ["div0", "nullptr", "bounds"],
             "semantic_leakage": ["add", "mul", "sub"],
             "comment_driven": ["factorial", "binsearch", "sort"],
             "type_driven": ["string", "vector", "queue"],
             "api_prior": ["malloc", "calloc", "buffer"],
             "control_flow": ["for", "while", "if"],
             "codestyle": ["newline", "space"]
             }

shortcut_type = {"pattern_continuation": "PatCon",
                 "lexical_trigger": "LTR",
                 "semantic_leakage": "SEMLeak",
                 "comment_driven": "ComDri",
                 "type_driven": "TypeDri",
                 "api_prior": "APIPri",
                 "control_flow": "CtrlF",
                 "codestyle": "CodeStyle"}

CORRECT_LABEL_DICT = {
    'Extract func error': "C1",
    'compile_error': "C1",
    "pass": "C0",
    "fail": "C1",
    "timeout": "C1",
}


def shortcut_ratio(shortcut_type="control_flow", trigger_type='num', is_finetune="vanilla"):
    if is_finetune == 'vd':
        answer_path = "Answer_finetune"
    elif is_finetune == "vanilla":
        answer_path = "Answer"
    else:
        answer_path = "Answer_codetrans"
    if "pattern_continuation" in shortcut_type:
        DETECT_FUNC = detect_pattern_shortcut
    elif "lexical_trigger" in shortcut_type:
        DETECT_FUNC = detect_lexical_trigger
    elif "semantic_leakage" in shortcut_type:
        DETECT_FUNC = detect_semantic_leakage_shortcut
    elif "type_driven" in shortcut_type:
        DETECT_FUNC = detect_type_driven_shortcut
    elif "api_prior" in shortcut_type:
        DETECT_FUNC = detect_api_prior_shortcut
    elif "comment_driven" in shortcut_type:
        DETECT_FUNC = detect_comment_driven_dependency
    elif "control_flow" in shortcut_type:
        DETECT_FUNC = detect_control_flow_dependency
    elif "codestyle" in shortcut_type:
        DETECT_FUNC = detect_code_style_dependency
    else:
        DETECT_FUNC = None

    generated_code = read_from_jsonl(
        f"{answer_path}/{llm_name}/humaneval/humaneval_C_InsertNoopcode_{shortcut_type}_{trigger_type}.jsonl")

    if "codestyle" in shortcut_type:
        source_generate_code = read_from_jsonl(
            f"{answer_path}/{llm_name}/humaneval/humaneval_C.jsonl"
        )
        shortcut_labels = [DETECT_FUNC(source_generate_code[i], item, trigger_type) for i, item in
                           enumerate(generated_code)]
    else:

        shortcut_labels = [DETECT_FUNC(item, trigger_type) for item in generated_code]

    return shortcut_labels

    # correct_labels = [CORRECT_LABEL_DICT[item[0]] if isinstance(item, list) else CORRECT_LABEL_DICT[item] for item in
    #                   execu_results]
    #
    # source_labels = [CORRECT_LABEL_DICT[item[0]] if isinstance(item, list) else CORRECT_LABEL_DICT[item] for item in
    #                  source_execu]
    #
    # M_2d = build_confusion_matrix(source_labels, correct_labels)
    #
    # M_3d = build_3d_confusion_matrix(source_labels, correct_labels, shortcut_labels)
    #
    # a = evaluate_shortcut_system(M_2d, M_3d)
    # return a


llm_dict = {"Starcoder2": ["bigcode/starcoder2-3b",
                           "bigcode/starcoder2-7b",
                           "bigcode/starcoder2-15b"],
            "DeepSeek Coder": ["deepseek-ai/deepseek-coder-1.3b-instruct",
                               "deepseek-ai/deepseek-coder-6.7b-instruct",
                               "deepseek-ai/deepseek-coder-7b-instruct-v1.5",
                               "deepseek-ai/deepseek-coder-33b-instruct",
                               ],
            "Qwen2.5 Coder Inst": ["Qwen/Qwen2.5-Coder-0.5B-Instruct",
                                   "Qwen/Qwen2.5-Coder-3B-Instruct",
                                   "Qwen/Qwen2.5-Coder-7B-Instruct",
                                   "Qwen/Qwen2.5-Coder-14B-Instruct"
                                   ],
            "CodeGen Multi": ["Salesforce/codegen-350M-multi",
                              "Salesforce/codegen-2B-multi",
                              "Salesforce/codegen-6B-multi",
                              "Salesforce/codegen-16B-multi"
                              ],
            "Qwen2.5 Coder": ["Qwen/Qwen2.5-Coder-0.5B",
                              "Qwen/Qwen2.5-Coder-3B",
                              "Qwen/Qwen2.5-Coder-7B",
                              "Qwen/Qwen2.5-Coder-14B"
                              ]
            }


def main_(llm_name, is_finetune):
    if is_finetune == 'vd':
        answer_path = "Answer_finetune"
    elif is_finetune == "vanilla":
        answer_path = "Answer"
    else:
        answer_path = "Answer_codetrans"
    tmp_sr = {}
    tmp_pr = {}
    tmp_spr = {}
    tmp_sfr = {}
    base_correct = read_from_jsonl(f"{answer_path}/{llm_name}/humaneval/humaneval_C_execution.jsonl")
    print(f"{answer_path}/{llm_name}/humaneval/humaneval_C_execution.jsonl")
    base_correct = [CORRECT_LABEL_DICT[item[0]] if isinstance(item, list) else CORRECT_LABEL_DICT[item] for item in
                    base_correct]

    print(llm_name)
    print(f"Source  Passed Ratio: {(base_correct.count("C0") / len(base_correct)) * 100:.2f}%")
    source_result = []
    source_result.append("-")
    source_result.append(f"{(base_correct.count("C0") / len(base_correct)) * 100:.2f}")
    for _ in range(2):
        source_result.append("-")
    results['source'].extend(source_result)

    for k, v in noop_type.items():
        tmp = []
        shortcut_tmp = []
        shortcut_preserve = []
        shortcut_fail = []
        for item in v:
            tmp_correct = [CORRECT_LABEL_DICT[item[0]] if isinstance(item, list) else CORRECT_LABEL_DICT[item] for
                           item
                           in
                           read_from_jsonl(
                               f"{answer_path}/{llm_name}/humaneval/humaneval_C_InsertNoopcode_{k}_{item}_execution.jsonl")]

            tmp.append([tmp_correct.count("C0"), tmp_correct.count("C1")])
            shortcut_labels = shortcut_ratio(shortcut_type=k, trigger_type=item)

            shortcut_tmp.append([shortcut_labels.count("S0"), shortcut_labels.count("S1")])
            shortcut_preserve.append(
                len([i for i in range(len(tmp_correct)) if
                     (shortcut_labels[i] == 'S1' and tmp_correct[i] == 'C0' and base_correct[i] == "C0")]))
            shortcut_fail.append(
                len([i for i in range(len(tmp_correct)) if
                     (shortcut_labels[i] == 'S1' and tmp_correct[i] == 'C1' and base_correct[i] == "C0")]))

        tmp = np.sum(tmp, axis=0)
        shortcut_tmp = np.sum(shortcut_tmp, axis=0)
        spr = np.sum(shortcut_preserve) / (3 * base_correct.count("C0"))
        sfr = np.sum(shortcut_fail) / (3 * base_correct.count("C0"))

        print(shortcut_type[k],
              f"Shortcut Ratio: {(shortcut_tmp[1] / np.sum(shortcut_tmp)) * 100:.2f}%",
              f"Passed Ratio: {(tmp[0] / np.sum(tmp)) * 100:.2f}%",
              f"Shortcut Preserve Rate:{spr * 100:.2f}%",
              f"Shortcut Failure Rate:{sfr * 100:.2f}%")
        tmp_sr[shortcut_type[k]] = (shortcut_tmp[1] / np.sum(shortcut_tmp))
        tmp_pr[shortcut_type[k]] = (tmp[0] / np.sum(tmp))
        tmp_spr[shortcut_type[k]] = spr
        tmp_sfr[shortcut_type[k]] = sfr
        print()

        results[k].extend([f"{(shortcut_tmp[1] / np.sum(shortcut_tmp)) * 100:.2f}",
                           f"{(tmp[0] / np.sum(tmp)) * 100:.2f}",
                           f"{spr * 100:.2f}", f"{sfr * 100:.2f}"])
    SR[llm_name] = tmp_sr
    PR[llm_name] = tmp_pr
    SPR[llm_name] = tmp_spr
    SFR[llm_name] = tmp_sfr


if __name__ == '__main__':
    import argparse

    # Starcoder2    DeepSeek Coder   Qwen2.5 Coder Inst  CodeGen Multi

    my_parser = argparse.ArgumentParser()
    my_parser.add_argument("-model_name", "-mn", type=str, default="DeepSeek Coder")
    my_parser.add_argument("-is_finetune", "-ft", type=str, default="vanilla")
    args = my_parser.parse_args()
    is_finetune = args.is_finetune
    model = args.model_name

    results = {"source": [],
               "pattern_continuation": [],
               "lexical_trigger": [],
               "semantic_leakage": [],
               "comment_driven": [],
               "type_driven": [],
               "api_prior": [],
               "control_flow": [],
               "codestyle": []
               }

    SR = {}
    PR = {}
    SPR = {}
    SFR = {}

    for llm_name in llm_dict[model]:
        main_(llm_name, is_finetune=is_finetune)
    for k, v in results.items():
        if k == "source":
            K = "Source"
        else:
            K = shortcut_type[k]
        if K == "Source":
            print("&", K, "&", "&".join(v), r"\\ \cline{2-18}")
        else:
            print("&", K, "&", "&".join(v), r"\\")

    save_path = f"Fig/DATA/SR/{is_finetune}/{model.replace(" ", "_")}.json"
    dir_path = os.path.dirname(save_path)
    os.makedirs(dir_path, exist_ok=True)
    save_dict(SR, f"Fig/DATA/SR/{is_finetune}/{model.replace(" ", "_")}.json")

    save_path = f"Fig/DATA/PR/{is_finetune}/{model.replace(" ", "_")}.json"
    dir_path = os.path.dirname(save_path)
    os.makedirs(dir_path, exist_ok=True)
    save_dict(PR, f"Fig/DATA/PR/{is_finetune}/{model.replace(" ", "_")}.json")

    save_path = f"Fig/DATA/SPR/{is_finetune}/{model.replace(" ", "_")}.json"
    dir_path = os.path.dirname(save_path)
    os.makedirs(dir_path, exist_ok=True)
    save_dict(SPR, f"Fig/DATA/SPR/{is_finetune}/{model.replace(" ", "_")}.json")

    save_path = f"Fig/DATA/SFR/{is_finetune}/{model.replace(" ", "_")}.json"
    dir_path = os.path.dirname(save_path)
    os.makedirs(dir_path, exist_ok=True)
    save_dict(SFR, f"Fig/DATA/SFR/{is_finetune}/{model.replace(" ", "_")}.json")
