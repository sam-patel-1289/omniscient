import json
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from fuzzy_resolver import FuzzyResolver
from llm_resolver import LLMResolver

def load_dataset(path):
    with open(path, 'r') as f:
        return json.load(f)

def run_benchmark():
    base_path = os.path.dirname(__file__)
    dataset_path = os.path.join(base_path, '../dataset.json')
    data = load_dataset(dataset_path)

    fuzzy = FuzzyResolver()
    llm = LLMResolver() # Will use mock if no env var

    fuzzy_correct = 0
    llm_correct = 0
    total = len(data)

    print(f"{'Text':<50} | {'Mention':<10} | {'Expected':<15} | {'Fuzzy':<15} | {'LLM':<15}")
    print("-" * 130)

    for item in data:
        text = item['text']
        mention = item['mention']
        expected = item['expected_id']

        # Fuzzy only sees the mention
        fuzzy_pred = fuzzy.resolve(mention)
        
        # LLM sees mention + context
        llm_pred = llm.resolve(mention, text)

        is_fuzzy_correct = (fuzzy_pred == expected)
        is_llm_correct = (llm_pred == expected)

        if is_fuzzy_correct: fuzzy_correct += 1
        if is_llm_correct: llm_correct += 1

        print(f"{text[:47]+'...':<50} | {mention:<10} | {expected:<15} | {str(fuzzy_pred):<15} | {str(llm_pred):<15}")

    print("-" * 130)
    print(f"\nResults:")
    print(f"Total Samples: {total}")
    print(f"Fuzzy Accuracy: {fuzzy_correct}/{total} ({fuzzy_correct/total*100:.1f}%)")
    print(f"LLM Accuracy:   {llm_correct}/{total} ({llm_correct/total*100:.1f}%)")

if __name__ == "__main__":
    run_benchmark()
