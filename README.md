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


