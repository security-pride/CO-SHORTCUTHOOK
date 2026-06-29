#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author: DirtyBoy
@Date: 2026/5/10 14:58
"""
import json, os, joblib
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix


def eval_shortcut(original, transformed, gt_labels):
    def softmax(logits):
        """
        logits: [logit_neg, logit_pos]
        """
        logits = np.array(logits, dtype=np.float64)
        logits = logits - np.max(logits)
        exp_logits = np.exp(logits)
        return exp_logits / np.sum(exp_logits)

    def extract_vul_prob(logit_list):
        """
        logit_list:
            [
                [logit_neg, logit_pos],
                ...
            ]

        return:
            np.array([P(vul), ...])
        """
        probs = []

        for logits in logit_list:
            p = softmax(logits)
            probs.append(p[1])  # vulnerability probability

        return np.array(probs)

    # =========================================================
    # 1. Prediction Drift (PD)
    # =========================================================

    def prediction_drift(original_logits, transformed_logits):
        """
        Mean absolute probability change.

        Higher = more shortcut-sensitive
        """
        shifts = []
        eps = 1e-8
        for o, t in zip(original_logits,
                        transformed_logits):
            score_o = abs(o[1] - o[0])
            score_t = abs(t[1] - t[0])

            shifts.append(abs(abs(score_t) - abs(score_o)))

        return np.mean(shifts)

    # =========================================================
    # 2. Shortcut Sensitivity Score (SSS)
    # =========================================================

    def shortcut_sensitivity_score(
            original_logits,
            transformed_logits,
            threshold=0.2):
        """
        Fraction of samples whose probability changes
        exceed threshold.

        Higher = more unstable under semantic-preserving transform
        """
        p1 = extract_vul_prob(original_logits)
        p2 = extract_vul_prob(transformed_logits)

        drift = np.abs(p1 - p2)

        return np.mean(drift > threshold)

    # =========================================================
    # 3. Confidence Collapse (CC)
    # =========================================================

    def confidence_collapse(original_logits, transformed_logits):
        """
        Measure confidence reduction after transformation.

        Positive:
            confidence drops after transformation.

        Negative:
            confidence increases.
        """

        conf1 = []
        conf2 = []

        for l1, l2 in zip(original_logits, transformed_logits):
            p1 = softmax(l1)
            p2 = softmax(l2)

            conf1.append(np.max(p1))
            conf2.append(np.max(p2))

        conf1 = np.array(conf1)
        conf2 = np.array(conf2)

        return np.mean(conf1 - conf2)

    # =========================================================
    # 4. Decision Flip Rate (DATA)
    # =========================================================

    def decision_flip_rate(original_logits, transformed_logits, gt_labels):
        """
        Fraction of samples whose predicted label changes.

        Higher = stronger shortcut influence
        """

        pred1 = []
        pred2 = []

        for l1, l2 in zip(original_logits, transformed_logits):
            p1 = softmax(l1)
            p2 = softmax(l2)

            pred1.append(np.argmax(p1))
            pred2.append(np.argmax(p2))

        pred1 = np.array(pred1)
        pred2 = np.array(pred2)

        # return np.sum((pred1 != pred2)) / len(pred1)

        return 0.5 * (np.sum((pred1 == 1) & (pred1 != pred2)) / np.sum(pred1 == 1)) + 0.5 * (np.sum(
            (pred1 == 0) & (pred1 != pred2)) / np.sum(pred1 == 0))

    # =========================================================
    # 5. Vulnerability Shift (VS)
    # =========================================================

    def vulnerability_shift(original_logits, transformed_logits):
        """
        Mean direction of probability movement.

        Positive:
            transformed samples are more likely
            predicted as vulnerable.

        Negative:
            transformed samples are more likely
            predicted as benign.
        """

        p1 = extract_vul_prob(original_logits)
        p2 = extract_vul_prob(transformed_logits)

        return np.mean(p2 - p1)

    # return [prediction_drift(original, transformed),
    #         shortcut_sensitivity_score(original, transformed),
    #         confidence_collapse(original, transformed),
    #         decision_flip_rate(original, transformed),
    #         vulnerability_shift(original, transformed)]
    return [prediction_drift(original, transformed),
            decision_flip_rate(original, transformed, gt_labels)]


import json


def save_dict(data: dict, file_path: str):
    """
    保存字典到 JSON 文件
    """
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def evaluate_shortcut(y_true, y_pred_orig, y_pred_trans, orig):
    y_true = np.array(y_true)
    y_pred_orig = np.array(y_pred_orig)
    y_pred_trans = np.array(y_pred_trans)

    assert len(y_true) == len(y_pred_orig) == len(y_pred_trans)

    N = len(y_true)

    trans = compute_basic_metrics(y_true, y_pred_trans)

    delta = {
        "delta_acc": trans["acc"] - orig["acc"],
        "delta_f1": trans["f1"] - orig["f1"],
        "delta_fnr": trans["fnr"] - orig["fnr"],
        "delta_fpr": trans["fpr"] - orig["fpr"],
    }

    flip = (y_pred_orig != y_pred_trans)

    pfr = np.sum(flip) / N

    pos_mask = (y_true == 1)
    neg_mask = (y_true == 0)

    pfr_pos = np.sum(flip & pos_mask) / N
    pfr_neg = np.sum(flip & neg_mask) / N

    correct_orig = (y_pred_orig == y_true)
    wrong_trans = (y_pred_trans != y_true)

    s2e = correct_orig & wrong_trans

    sier = np.sum(s2e) / N
    pcr = accuracy_score(y_pred_orig, y_pred_trans)
    wrong_orig = (y_pred_orig != y_true)
    correct_trans = (y_pred_trans == y_true)

    e2r = wrong_orig & correct_trans

    err = np.sum(e2r) / N
    sdi = sier - err

    flip_0_to_1 = np.sum((y_pred_orig == 0) & (y_pred_trans == 1)) / N
    flip_1_to_0 = np.sum((y_pred_orig == 1) & (y_pred_trans == 0)) / N

    def impact_score(delta_fnr, delta_fpr):

        if delta_fnr == 0 or delta_fpr == 0:
            return 0.0

        product = delta_fnr * delta_fpr
        if product < 0:
            return abs(delta_fnr) + abs(delta_fpr)
        elif product > 0:
            return -abs(delta_fnr + delta_fpr)
        else:
            return 0.0

    return {
        "original": orig,
        "transformed": trans,
        "delta": delta,

        # overall shortcut sensitivity
        "PFR": pfr,

        # class-wise shortcut sensitivity
        "PFR_pos": pfr_pos,
        "PFR_neg": pfr_neg,

        "pcr": pcr,

        # shortcut-induced error
        "SIER": sier,

        # shortcut-induced recovery
        "ERR": err,

        # net shortcut impact
        "SDI": sdi,
        "Flip": flip,

        # directional flip
        "Flip_0_to_1": flip_0_to_1,
        "Flip_1_to_0": flip_1_to_0,
        "IS": impact_score(delta["delta_fnr"], delta["delta_fpr"]),
    }


def read_joblib(path):
    if os.path.isfile(path):
        with open(path, 'rb') as fr:
            return joblib.load(fr)
    else:
        raise IOError("The {0} is not a file.".format(path))


def compute_basic_metrics(y_true, y_pred):
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)

    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

    return {
        "acc": acc,
        "f1": f1,
        "fnr": fnr,
        "fpr": fpr,
        "tp": tp, "tn": tn, "fp": fp, "fn": fn
    }


substring_map = {
    "ChangeCodestyle": "CodeStyle",
    "control_flow": "CtrlF",
    "semantic_leakage": "SemLeak",
    "pattern_continuation": "PatCon",
    "lexical_trigger": "LTR",
    "api_prior": "APIPrior",
    "comment_driven": "ComDri",
    "type_driven": "TypeDri",
    "VAR": "VAR", "FUNC": "FUNC",
    "safe_comment": "SafeCom",
    "dangerous_api": "APIPrior",
    "fixme_comment": "ComDri",
    "surface": "Surface",
}

# noop_type = {"VAR": ["VAR"], "FUNC": ["FUNC"],
#              "ChangeCodestyle": ["ChangeCodestyle"],
#              "pattern_continuation": ["var", "num", "ptr"],
#              "lexical_trigger": ["div0", "nullptr", "bounds"],
#              "semantic_leakage": ["add", "mul", "strcat"],
#              "comment_driven": ["factorial", "binsearch", "sort"],
#              "type_driven": ["string_len", "vector_size", "map_find"],
#              "api_prior": ["malloc", "calloc", "buffer"],
#              "control_flow": ["for", "while", "if"]}

noop_type = {
    "VAR": ["VAR"],
    "ChangeCodestyle": ["ChangeCodestyle"],
    "FUNC": ["FUNC"],
    # "pattern_continuation": ["num", "ptr", "var"],
    # "lexical_trigger": ["bounds", "div0", "nullptr"],
    # "semantic_leakage": ["add", "mul", "strcat"],
    "safe_comment": ["safe"],  # ["nonvul", "safe", "secure"],
    # "type_driven": ["map_find"],  # ["map_find", "string_len", "vector_size"],
    # "fixme_comment": ["todo"],  # ["fixme", "hack", "todo"],
    # "dangerous_api": ["memcpy"],  # ["memcpy", "sprintf", "strcpy"],
    # "control_flow": ["if"],  # ["for", "while", "if"],

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
    results = {}
    model="Starcoder2"#"DeepSeek Coder"#, "CodeGen Multi", "Qwen2.5 Coder", "Qwen2.5 Coder Inst", "Starcoder2"]:
    llm_dict = {"Starcoder2": ["bigcode/starcoder2-3b", "bigcode/starcoder2-7b", "bigcode/starcoder2-15b"],
                "DeepSeek Coder": ["deepseek-ai/deepseek-coder-1.3b-instruct",
                                   "deepseek-ai/deepseek-coder-6.7b-instruct",
                                   "deepseek-ai/deepseek-coder-7b-instruct-v1.5",
                                   "deepseek-ai/deepseek-coder-33b-instruct", ],
                "Qwen2.5 Coder Inst": ["Qwen/Qwen2.5-Coder-0.5B-Instruct", "Qwen/Qwen2.5-Coder-3B-Instruct",
                                       "Qwen/Qwen2.5-Coder-7B-Instruct", "Qwen/Qwen2.5-Coder-14B-Instruct"],
                "CodeGen Multi": ["Salesforce/codegen-350M-multi", "Salesforce/codegen-2B-multi",
                                  "Salesforce/codegen-6B-multi", "Salesforce/codegen-16B-multi"],
                "Qwen2.5 Coder": ["Qwen/Qwen2.5-Coder-0.5B",
                                  "Qwen/Qwen2.5-Coder-3B",
                                  "Qwen/Qwen2.5-Coder-7B", "Qwen/Qwen2.5-Coder-14B"
                                  ]
                }

    # results = {"source": [],
    #            # "VAR": [],
    #            # "ChangeCodestyle": [],
    #            # "FUNC": [],
    #            "surface": [],
    #            "dangerous_api": [],
    #            "semantic_leakage": [],
    #            "safe_comment": [],
    #            "fixme_comment": [],
    #            "control_flow": []
    #            }

    results["source"] = []
    for k, v in noop_type.items():
        results[k] = []

    DFR = {}


    def main_(
            llm="Qwen/Qwen2.5-Coder-0.5B-Instruct"):  # "deepseek-ai/deepseek-coder-7b-instruct-v1.5"  # "Qwen/Qwen3-4B-Instruct-2507"#"deepseek-ai/deepseek-coder-1.3b-instruct"#"Salesforce/codegen-2B-multi"#"Qwen/Qwen2.5-Coder-3B-Instruct"##"bigcode/starcoder2-3b"#
        test_data = "unlearning_random_test"
        tmp_dfr = {}
        source = read_from_jsonl(f"unlearning-testset/{test_data}.jsonl")
        gt_labels = np.array([item["target"] for item in source])

        base_logits = read_joblib(f"output/causallm/mle/unlearning_random_train/{test_data}/epoch4/{llm}-1.data")
        base_pred = np.array([np.argmax(item) for item in base_logits])
        orig = compute_basic_metrics(gt_labels, base_pred)
        source_result = []
        source_result.append(f"{orig['acc'] * 100:.2f}")
        # source_result.append(f"{orig['fpr'] * 100:.2f}")
        # for _ in range(1):
        #     source_result.append("-")
        # print(llm)
        # print(
        #     f"&{orig['acc'] * 100:.2f} &{orig['fnr'] * 100:.2f} &{orig['fpr'] * 100:.2f} &{orig['f1'] * 100:.2f} &-&-&-&-&-&-",
        #     r"\\")
        results['source'].extend(source_result)
        for vars_type in noop_type.keys():
            vars_res = []
            for vars_name in noop_type[vars_type]:
                if vars_name in ["VAR", "FUNC", "ChangeCodestyle"]:
                    vars_test_data = f"{test_data}_{vars_name}"
                else:
                    vars_test_data = f"{test_data}_{vars_type}_{vars_name}"

                try:
                    index_list = [i for i in range(len(source)) if source[i]["success_flag"] == 1]
                except KeyError:
                    index_list = [i for i in range(len(source))]

                gt_labels = np.array([item["target"] for item in source])[index_list]

                base_logits = read_joblib(
                    f"output/causallm/mle/unlearning_random_train/{test_data}/epoch4/{llm}-1.data")
                base_pred = np.array([np.argmax(item) for item in base_logits])[index_list]

                vars_base_logits = read_joblib(
                    f"output/causallm/mle/unlearning_random_train/{vars_test_data}/epoch4/{llm}-1.data")
                vars_base_pred = np.array([np.argmax(item) for item in vars_base_logits])[index_list]

                res = evaluate_shortcut(gt_labels, base_pred, vars_base_pred, orig)

                # vars_res.append([res['delta']['delta_acc'], res['delta']['delta_fnr'], res['delta']['delta_fpr'],
                #                  res['delta']['delta_f1'], res["IS"]] + eval_shortcut(base_logits, vars_base_logits))
                # results[vars_type].append(
                #     [res['delta']['delta_fnr'], res['delta']['delta_fpr']] + [eval_shortcut(base_logits,
                #                                                                             vars_base_logits,
                #                                                                             gt_labels)[1]])
                results[vars_type].append([eval_shortcut(base_logits, vars_base_logits, gt_labels)[1]])

                # results[vars_type].append(
                #     [res['delta']['delta_acc'], res['delta']['delta_f1']] + eval_shortcut(base_logits,
                #                                                                           vars_base_logits))

                # results[vars_type].extend(
                #     [f"{item * 100:.2f}" for item in
                #      ([res['delta']['delta_acc'], res['delta']['delta_f1']] + eval_shortcut(base_logits,
                #                                                                             vars_base_logits))])

                tmp_dfr[vars_type] = eval_shortcut(base_logits, vars_base_logits, gt_labels)[1]

            # vars_res = np.mean(results, axis=0)
            # vars_res = [f"{item * 100:.2f}" for item in vars_res]
            # print(
            #     f"&&{substring_map[vars_type]}", "&",
            #     f"&".join(vars_res),
            #     r"\\")
            # DFR[llm] = tmp_dfr

    # my_results = {"Source": [],
    #               "Surface": [],
    #               "Semantic": [],
    #               "Usage-Prior": [],
    #               "Structural": []}

    # my_map = {"Surface": "Surface",
    #           "PatCon":"Surface",
    #           "LTR": "Surface",
    #           "DangAPI": "Usage-Prior",
    #           "SafeCom": "Surface",
    #           "TypeDri": "Usage-Prior",
    #           "FixMeCom": "Semantic",
    #           "SemLeak": "Semantic",
    #           "DeadCode": "Structural"}

    my_map = {"Surface": "Surface",
              "PatCon": "PatCon",
              "LTR": "LTR",
              "DangAPI": "APIPri",
              "SafeCom": "Surface",
              "TypeDri": "TypeDri",
              "FixMeCom": "FixMeCom",
              "SemLeak": "SemLeak",
              "DeadCode": "Structural"}
    my_results = {v: [] for k, v in my_map.items()}
    for llm in llm_dict[model]:
            main_(llm)
    for k, v in results.items():
        if k == "source":
            K = "Source"
            print("&", K, "&", "&".join(v), r"\\ \cline{2-14}")
        else:
            K = substring_map[k]

            tmp_v = []
            for i in range(len(llm_dict[model])):
                tmp_v.extend([item for item in
                              np.mean(v[i * len(noop_type[k]):i * len(noop_type[k]) + len(noop_type[k])], axis=0)])
            tmp_v = [f"{item * 100:.2f}" for item in tmp_v]
            print("&", K, "&", "&".join(tmp_v), r"\\")
    #     if K == "Source":
    #         my_results[K] = v
    #     else:
    #         my_results[my_map[K]].append(tmp_v)
    # for k, v in my_results.items():
    #     if k == "Source":
    #         print("&", k, "&", "&".join(v), r"\\ \cline{2-14}")
    #     else:
    #         tmp_v = [f"{item * 100:.2f}" for item in np.mean(v, axis=0)]
    #         print("&", k, "&", "&".join(tmp_v), r"\\")

    # np.save(f"Fig/DATA/DFR/{model.replace(" ", "_")}.npy", DFR)
    # save_dict(DFR, f"Fig/DATA/PD/{model.replace(" ", "_")}.json")
