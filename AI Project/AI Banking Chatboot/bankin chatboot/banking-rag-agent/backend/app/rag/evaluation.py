"""Basic RAG evaluation module."""

import asyncio
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List

from app.rag.generator import NO_INFO_MESSAGE, generate_answer
from app.rag.retriever import retrieve_context


@dataclass
class EvalCase:
    question: str
    expected_answer_contains: List[str]
    expected_source: str
    category: str = "General"


@dataclass
class EvalResult:
    question: str
    retrieval_hit: bool
    context_relevance: float
    answer_relevance: bool
    faithfulness: bool
    hallucination: bool
    retrieved_sources: List[str]
    generated_answer: str


EVAL_DATASET: List[EvalCase] = [
    EvalCase(
        question="What documents are required for a personal loan?",
        expected_answer_contains=["PAN", "salary", "bank statement"],
        expected_source="Personal_Loan_Policy",
        category="Loan",
    ),
    EvalCase(
        question="What is the minimum balance for a savings account?",
        expected_answer_contains=["5,000", "5000"],
        expected_source="Account_Opening",
        category="Account",
    ),
    EvalCase(
        question="What is the home loan interest rate?",
        expected_answer_contains=["8.50", "9.75"],
        expected_source="Interest_Rates",
        category="Interest Rates",
    ),
    EvalCase(
        question="How do I block my debit card?",
        expected_answer_contains=["block", "1800"],
        expected_source="Debit_Card",
        category="Debit Card",
    ),
    EvalCase(
        question="What is the NEFT charge via internet banking?",
        expected_answer_contains=["free", "Free"],
        expected_source="Banking_Charges",
        category="Banking Charges",
    ),
    EvalCase(
        question="What is the eligibility for education loan?",
        expected_answer_contains=["16", "35", "admission"],
        expected_source="Education_Loan",
        category="Loan",
    ),
    EvalCase(
        question="What is the current stock price of Apple?",
        expected_answer_contains=["couldn't find"],
        expected_source="",
        category="Out of scope",
    ),
]


def _check_answer_relevance(answer: str, expected_terms: List[str]) -> bool:
    answer_lower = answer.lower()
    if any("couldn't find" in t.lower() for t in expected_terms):
        return NO_INFO_MESSAGE.lower() in answer_lower
    matches = sum(1 for term in expected_terms if term.lower() in answer_lower)
    return matches >= len(expected_terms) * 0.5


def _check_faithfulness(answer: str, context: str) -> bool:
    if NO_INFO_MESSAGE.lower() in answer.lower():
        return True
    import re
    numbers = re.findall(r"\d+\.?\d*", answer)
    for num in numbers:
        if len(num) > 2 and num not in context:
            return False
    return True


async def evaluate_single(case: EvalCase) -> EvalResult:
    retrieval = retrieve_context(case.question)
    context_text = " ".join(d.page_content for d in retrieval.documents)
    answer, grounded = await generate_answer(case.question, retrieval.documents, retrieval.sufficient)

    sources = [d.metadata.get("filename", "") for d in retrieval.documents]
    retrieval_hit = any(case.expected_source.lower() in s.lower() for s in sources) if case.expected_source else not retrieval.sufficient

    return EvalResult(
        question=case.question,
        retrieval_hit=retrieval_hit,
        context_relevance=retrieval.avg_score,
        answer_relevance=_check_answer_relevance(answer, case.expected_answer_contains),
        faithfulness=_check_faithfulness(answer, context_text),
        hallucination=not _check_faithfulness(answer, context_text) and grounded,
        retrieved_sources=sources[:3],
        generated_answer=answer[:300],
    )


async def run_evaluation() -> dict:
    results = []
    for case in EVAL_DATASET:
        result = await evaluate_single(case)
        results.append(result)

    total = len(results)
    metrics = {
        "total_cases": total,
        "retrieval_accuracy": sum(1 for r in results if r.retrieval_hit) / total,
        "avg_context_relevance": sum(r.context_relevance for r in results) / total,
        "answer_relevance": sum(1 for r in results if r.answer_relevance) / total,
        "faithfulness": sum(1 for r in results if r.faithfulness) / total,
        "hallucination_rate": sum(1 for r in results if r.hallucination) / total,
        "results": [asdict(r) for r in results],
    }
    return metrics


async def main():
    print("Running RAG evaluation...")
    metrics = await run_evaluation()
    print(json.dumps(metrics, indent=2))

    output_path = Path(__file__).resolve().parent.parent.parent / "tests" / "eval_results.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
