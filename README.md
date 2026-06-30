# CO-SHORTCUTHOOK

**CO-SHORTCUTHOOK** is a unified evaluation framework for measuring **shortcut reliance in Code Large Language Models (Code LLMs)**.

Modern Code LLMs have achieved remarkable performance across a wide range of software engineering tasks, including code generation, vulnerability detection, and repository-level reasoning. However, instead of learning genuine program semantics, these models may rely on **shortcut representations**—predictive cues that correlate with task labels but lack causal relationships with program behavior. Such shortcut reliance often leads to hallucinations, spurious correlations, and poor robustness under semantics-preserving code transformations.

CO-SHORTCUTHOOK provides the first unified framework for systematically evaluating shortcut learning in Code LLMs. It introduces a taxonomy of **eight shortcut types** spanning four categories:

* **Surface-level shortcuts**
* **Semantic-level shortcuts**
* **Usage-prior shortcuts**
* **Structural shortcuts**

Based on this taxonomy, CO-SHORTCUTHOOK evaluates shortcut reliance through **semantic-preserving trigger injection** and a collection of **shortcut-aware evaluation metrics**. The framework enables researchers to analyze shortcut behaviors across different Code LLM families, model scales, downstream tasks, and fine-tuning settings.

CO-SHORTCUTHOOK supports comprehensive analyses of shortcut dependence, robustness, and shortcut transfer from pretraining to downstream fine-tuning, providing practical tools for understanding and improving the reliability of Code LLMs.


## Installation

### Requirements

* Python **3.12**
* PyTorch **2.6**

### Install Dependencies

```
pip install -r requirements.txt
```

## Datasets

All evaluation datasets are included in this repository and can be found in the `humaneval/` directory.

## Quick Start

The evaluation pipeline consists of four sequential steps.

### Step 1. Generate Code Completions

Generate function implementations for the benchmark tasks using the target Code LLM.

```bash
python3 code_complete.py
```

### Step 2. Extract Generated Functions

Extract the generated function bodies from the model outputs.

```bash
python3 extract_generated_function.py
```

### Step 3. Evaluate Functional Correctness

Evaluate whether the generated functions pass the corresponding test cases.

```bash
python3 code_correct_evaluation.py
```

### Step 4. Analyze Shortcut Reliance

Measure shortcut reliance and compute shortcut-aware evaluation metrics.

```bash
python3 shortcut_analysis.py
```

After completing these four steps, CO-SHORTCUTHOOK reports the functional correctness and shortcut reliance of the evaluated Code LLM.



## Vulnerability Detection

The vulnerability detection experiments are built upon the implementation provided by **BLoB**[https://github.com/Wang-ML-Lab/bayesian-peft].

The evaluation dataset is available in the `defect-detection-testset/` directory.

The evaluation pipeline consists of the following steps:


### Analyze Shortcut Reliance

Evaluate shortcut dependence using the generated predictions.

```bash
python3 VD_classifier_analysis.py
```



