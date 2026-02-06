"""Cognitive Architecture Evaluators - LLM-based evaluation tools."""

from .cli_evaluator import CLITaskEvaluator, ClaudeCLI, EvaluationResult, TaskResult, main

# Backward-compatible alias for older imports.
CLIEvaluator = CLITaskEvaluator

__all__ = [
    "CLITaskEvaluator",
    "CLIEvaluator",
    "ClaudeCLI",
    "EvaluationResult",
    "TaskResult",
    "main",
]
