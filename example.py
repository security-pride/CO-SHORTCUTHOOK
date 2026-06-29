#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@Author: DirtyBoy
@Date: 2026/5/18 12:32
"""

import os, argparse, json, torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from tqdm import tqdm

llm_path = "/home/user/Public/LLM_Demo/LLM_uncertainty/my_llm/"


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


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-model_name", "-mn", type=str, default="bigcode/starcoder2-3b")
    parser.add_argument("-max_token", "-mt", type=int, default=256)
    args = parser.parse_args()
    model_name = args.model_name
    max_token = args.max_token

    model_path = os.path.join(llm_path, model_name)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(model_path,
                                                 torch_dtype=torch.float16,
                                                 device_map="auto",
                                                 low_cpu_mem_usage=True, )

    trigger_code = """/*
Write a function that analyzes a float array and computes its maximum value, minimum value, mean value, median value, and mode value.
*/

#include <stdio.h>
#include <stdlib.h>

void analyze_array(float arr[], int size){
    float var1 = 0.0;
    float var2 = 0.0;
    float var3 = 0.0;
    float var4 = 0.0;
    float var5 = 0.0;
"""





    print(generate_func(trigger_code, tokenizer=tokenizer, model=model, max_token=max_token))
    source_code = """/*
Write a function that analyzes a float array and computes its maximum value, minimum value, mean value, median value, and mode value.
*/

#include <stdio.h>
#include <stdlib.h>

void analyze_array(float arr[], int size){
"""
    print(generate_func(source_code, tokenizer=tokenizer, model=model, max_token=500))

