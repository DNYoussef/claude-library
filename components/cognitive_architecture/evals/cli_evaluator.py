#!/usr/bin/env python3
"""
CLI-Based Real Task Evaluator for VVV Dogfooding

Uses the locally authenticated `claude` CLI instead of API keys.
This mirrors the approach in life-os-dashboard ClaudeClient.

Usage:
    from evals.cli_evaluator import CLITaskEvaluator
    evaluator = CLITaskEvaluator("prompt-architect")
    results = evaluator.run_evaluation(max_tasks=5)
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@dataclass
class TaskResult:
    """Result of evaluating a single task."""
    task_id: str
    difficulty: str
    category: str
    input_text: str
    skill_output: str
    success_criteria: str
    intent_accuracy: float = 0.0
    constraint_coverage: float = 0.0
    output_quality: float = 0.0
    verix_compliance: float = 0.0
    l2_purity: float = 0.0
    passed: bool = False
    judge_reasoning: str = ""
    execution_time_ms: int = 0


@dataclass
class EvaluationResult:
    """Aggregate evaluation results."""
    skill_name: str
    version: str
    timestamp: str
    total_tasks: int
    passed_tasks: int
    easy_score: float = 0.0
    medium_score: float = 0.0
    hard_score: float = 0.0
    intent_accuracy: float = 0.0
    constraint_coverage: float = 0.0
    output_quality: float = 0.0
    verix_compliance: float = 0.0
    l2_purity: float = 0.0
    overall_score: float = 0.0
    task_results: List[TaskResult] = field(default_factory=list)


class ClaudeCLI:
    """
    Wrapper for local Claude CLI.
    Uses the already-authenticated CLI instead of API keys.
    """

    CLI_COMMAND = "claude"
    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(self):
        self._available: Optional[bool] = None
        self.model = self.DEFAULT_MODEL

    @property
    def is_available(self) -> bool:
        """Check if claude CLI is available"""
        if self._available is None:
            self._available = self._check_cli_available()
        return self._available

    def _check_cli_available(self) -> bool:
        """Check if claude CLI is installed and accessible"""
        try:
            result = subprocess.run(
                [self.CLI_COMMAND, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                shell=True
            )
            return result.returncode == 0
        except Exception:
            return False

    def send_message(self, prompt: str, max_tokens: int = 2000) -> Dict[str, Any]:
        """
        Send a message via Claude CLI and get a response.
        Synchronous version for simpler integration.
        """
        if not self.is_available:
            raise ValueError("Claude CLI not available")

        start_time = time.time()

        cmd = [
            self.CLI_COMMAND,
            "--print",
            "--output-format", "text",
        ]

        try:
            # Run claude CLI with prompt via stdin
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                shell=True
            )

            execution_time_ms = int((time.time() - start_time) * 1000)

            if result.returncode != 0:
                raise ValueError(f"Claude CLI error: {result.stderr}")

            response_text = result.stdout.strip()
            tokens_used = (len(prompt) + len(response_text)) // 4

            return {
                "response": response_text,
                "model": self.model,
                "tokens_used": tokens_used,
                "execution_time_ms": execution_time_ms
            }

        except subprocess.TimeoutExpired:
            raise ValueError("Claude CLI timeout after 5 minutes")


class CLITaskEvaluator:
    """
    Evaluator that uses Claude CLI for real LLM-based evaluation.
    No API keys required - uses locally authenticated CLI.
    """

    CORPUS_DIR = Path(__file__).parent / "corpus"
    RESULTS_DIR = Path(__file__).parent.parent / "storage" / "eval_results"
    SKILLS_DIR = Path(__file__).parent.parent.parent / "skills" / "foundry"

    def __init__(self, skill_name: str):
        self.skill_name = skill_name
        self.corpus = self._load_corpus()
        self.skill_content = self._load_skill()
        self.cli = ClaudeCLI()
        self.RESULTS_DIR.mkdir(parents=True, exist_ok=True)

        if not self.cli.is_available:
            raise ValueError("Claude CLI not available. Install with: npm install -g @anthropic-ai/claude-code")

        print(f"[CLI] Claude CLI available - using real LLM evaluation")

    def _load_corpus(self) -> Dict:
        """Load the task corpus for this skill."""
        corpus_file = self.CORPUS_DIR / f"{self.skill_name}-corpus.json"
        if not corpus_file.exists():
            raise FileNotFoundError(f"Corpus not found: {corpus_file}")
        with open(corpus_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_skill(self) -> str:
        """Load the skill definition."""
        skill_file = self.SKILLS_DIR / self.skill_name / "SKILL.md"
        if not skill_file.exists():
            raise FileNotFoundError(f"Skill not found: {skill_file}")
        return skill_file.read_text(encoding="utf-8")

    def _execute_skill(self, task_input: str) -> str:
        """Execute the skill with given input using Claude CLI."""
        prompt = f"""You are executing the {self.skill_name} skill.

Here is the skill definition:
<skill>
{self.skill_content[:6000]}
</skill>

Now execute this skill with the following input:
<input>
{task_input}
</input>

Provide the skill's output following its defined behavior and format."""

        try:
            result = self.cli.send_message(prompt)
            return result["response"]
        except Exception as e:
            return f"[ERROR] Skill execution failed: {e}"

    def _judge_output(self, task: Dict, skill_output: str) -> Dict[str, Any]:
        """Use Claude CLI to judge the skill output."""
        judge_prompt = f"""You are evaluating a skill's output. Score each dimension from 0.0 to 1.0.

TASK:
- ID: {task['id']}
- Category: {task['category']}
- Input: {task['input'][:500]}
- Success Criteria: {task['success_criteria']}

SKILL OUTPUT:
{skill_output[:1500]}

EXPECTED (if available):
- Intent: {task.get('expected_intent', 'N/A')}
- Constraints: {task.get('expected_constraints', [])}

Score these dimensions (0.0 to 1.0):
1. intent_accuracy: Did the skill correctly identify/handle the intent?
2. constraint_coverage: Were all relevant constraints addressed?
3. output_quality: Is the output well-structured and useful?
4. verix_compliance: Does output follow VERIX epistemic standards?
5. l2_purity: Is output in pure English without VCL markers?

Respond in JSON format ONLY (no other text):
{{
  "intent_accuracy": 0.0,
  "constraint_coverage": 0.0,
  "output_quality": 0.0,
  "verix_compliance": 0.0,
  "l2_purity": 0.0,
  "passed": true,
  "reasoning": "Brief explanation"
}}"""

        try:
            result = self.cli.send_message(judge_prompt, max_tokens=500)
            text = result["response"]

            # Find JSON in response
            start = text.find('{')
            end = text.rfind('}') + 1
            if start < 0 or end <= start:
                return self._default_scores("Failed to parse judge response")
            return json.loads(text[start:end])

        except Exception as e:
            return self._default_scores(f"Judge error: {e}")

    def _default_scores(self, reason: str) -> Dict[str, Any]:
        """Return default scores on error."""
        return {
            "intent_accuracy": 0.0,
            "constraint_coverage": 0.0,
            "output_quality": 0.0,
            "verix_compliance": 0.0,
            "l2_purity": 0.0,
            "passed": False,
            "reasoning": reason
        }

    def evaluate_task(self, task: Dict) -> TaskResult:
        """Evaluate a single task using Claude CLI."""
        start_time = time.time()

        # Execute skill
        skill_output = self._execute_skill(task['input'])

        # Judge output
        scores = self._judge_output(task, skill_output)

        execution_time = int((time.time() - start_time) * 1000)

        return TaskResult(
            task_id=task['id'],
            difficulty=task['difficulty'],
            category=task['category'],
            input_text=task['input'],
            skill_output=skill_output[:500],
            success_criteria=task['success_criteria'],
            intent_accuracy=scores.get('intent_accuracy', 0),
            constraint_coverage=scores.get('constraint_coverage', 0),
            output_quality=scores.get('output_quality', 0),
            verix_compliance=scores.get('verix_compliance', 0),
            l2_purity=scores.get('l2_purity', 0),
            passed=scores.get('passed', False),
            judge_reasoning=scores.get('reasoning', ''),
            execution_time_ms=execution_time,
        )

    def run_evaluation(
        self,
        task_ids: Optional[List[str]] = None,
        difficulty_filter: Optional[str] = None,
        max_tasks: Optional[int] = None,
    ) -> EvaluationResult:
        """Run evaluation using Claude CLI."""
        tasks = self.corpus['tasks']

        if difficulty_filter:
            tasks = [t for t in tasks if t['difficulty'] == difficulty_filter]
        if task_ids:
            tasks = [t for t in tasks if t['id'] in task_ids]
        if max_tasks:
            tasks = tasks[:max_tasks]

        print(f"\n{'='*60}")
        print(f"CLI EVALUATION: {self.skill_name}")
        print(f"Tasks to evaluate: {len(tasks)}")
        print(f"Using: Claude CLI (real LLM)")
        print(f"{'='*60}\n")

        results: List[TaskResult] = []

        for i, task in enumerate(tasks, 1):
            print(f"[{i}/{len(tasks)}] Evaluating {task['id']}...", end=" ", flush=True)
            result = self.evaluate_task(task)
            results.append(result)
            status = "PASS" if result.passed else "FAIL"
            print(f"{status} ({result.execution_time_ms}ms)")

        # Aggregate scores
        passed_count = sum(1 for r in results if r.passed)

        def avg_score(results_list: List[TaskResult], attr: str) -> float:
            if not results_list:
                return 0.0
            return sum(getattr(r, attr) for r in results_list) / len(results_list)

        easy_results = [r for r in results if r.difficulty == 'easy']
        medium_results = [r for r in results if r.difficulty == 'medium']
        hard_results = [r for r in results if r.difficulty == 'hard']

        eval_result = EvaluationResult(
            skill_name=self.skill_name,
            version=self.corpus.get('version', 'unknown'),
            timestamp=datetime.now(timezone.utc).isoformat(),
            total_tasks=len(results),
            passed_tasks=passed_count,
            easy_score=avg_score(easy_results, 'output_quality') if easy_results else 0,
            medium_score=avg_score(medium_results, 'output_quality') if medium_results else 0,
            hard_score=avg_score(hard_results, 'output_quality') if hard_results else 0,
            intent_accuracy=avg_score(results, 'intent_accuracy'),
            constraint_coverage=avg_score(results, 'constraint_coverage'),
            output_quality=avg_score(results, 'output_quality'),
            verix_compliance=avg_score(results, 'verix_compliance'),
            l2_purity=avg_score(results, 'l2_purity'),
            overall_score=passed_count / len(results) if results else 0,
            task_results=results,
        )

        self._save_results(eval_result)
        return eval_result

    def _save_results(self, result: EvaluationResult):
        """Save evaluation results to file."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{self.skill_name}-cli-eval-{timestamp}.json"
        filepath = self.RESULTS_DIR / filename

        result_dict = {
            "skill_name": result.skill_name,
            "version": result.version,
            "timestamp": result.timestamp,
            "evaluation_type": "cli",
            "total_tasks": result.total_tasks,
            "passed_tasks": result.passed_tasks,
            "easy_score": result.easy_score,
            "medium_score": result.medium_score,
            "hard_score": result.hard_score,
            "intent_accuracy": result.intent_accuracy,
            "constraint_coverage": result.constraint_coverage,
            "output_quality": result.output_quality,
            "verix_compliance": result.verix_compliance,
            "l2_purity": result.l2_purity,
            "overall_score": result.overall_score,
            "task_results": [
                {
                    "task_id": r.task_id,
                    "difficulty": r.difficulty,
                    "category": r.category,
                    "passed": r.passed,
                    "intent_accuracy": r.intent_accuracy,
                    "output_quality": r.output_quality,
                    "execution_time_ms": r.execution_time_ms,
                    "reasoning": r.judge_reasoning,
                }
                for r in result.task_results
            ]
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result_dict, f, indent=2)

        print(f"\nResults saved: {filepath}")

    def print_summary(self, result: EvaluationResult):
        """Print evaluation summary."""
        print(f"\n{'='*60}")
        print(f"EVALUATION SUMMARY: {result.skill_name}")
        print(f"{'='*60}")
        print(f"Evaluation Type: CLI (Real LLM)")
        print(f"Total Tasks: {result.total_tasks}")
        print(f"Passed: {result.passed_tasks} ({result.overall_score:.1%})")
        print(f"\nBy Difficulty:")
        print(f"  Easy: {result.easy_score:.1%}")
        print(f"  Medium: {result.medium_score:.1%}")
        print(f"  Hard: {result.hard_score:.1%}")
        print(f"\nBy Dimension:")
        print(f"  Intent Accuracy: {result.intent_accuracy:.1%}")
        print(f"  Constraint Coverage: {result.constraint_coverage:.1%}")
        print(f"  Output Quality: {result.output_quality:.1%}")
        print(f"  VERIX Compliance: {result.verix_compliance:.1%}")
        print(f"  L2 Purity: {result.l2_purity:.1%}")
        print(f"\nOverall Score: {result.overall_score:.1%}")


def main():
    """Run CLI evaluation from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Run CLI-based task evaluation")
    parser.add_argument("skill", choices=["prompt-architect", "agent-creator", "skill-forge"])
    parser.add_argument("--max-tasks", type=int, default=None, help="Max tasks to run (default: all)")
    parser.add_argument("--difficulty", choices=["easy", "medium", "hard"], default=None)
    parser.add_argument("--tasks", type=str, default=None,
                        help="Comma-separated list of task IDs to run (e.g., PA-020,PA-023)")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                        help="Output format (default: text)")

    args = parser.parse_args()

    # Parse task IDs if provided
    task_ids = None
    if args.tasks:
        task_ids = [t.strip() for t in args.tasks.split(",")]

    try:
        evaluator = CLITaskEvaluator(args.skill)
        result = evaluator.run_evaluation(
            task_ids=task_ids,
            difficulty_filter=args.difficulty,
            max_tasks=args.max_tasks,
        )

        if args.format == "json":
            # Output JSON for L1 loop consumption
            failures = [r.task_id for r in result.task_results if not r.passed]
            output = {
                "skill": result.skill_name,
                "passed": result.passed_tasks,
                "failed": result.total_tasks - result.passed_tasks,
                "total": result.total_tasks,
                "pass_rate": result.overall_score,
                "failures": failures,
                "results": [
                    {
                        "task_id": r.task_id,
                        "passed": r.passed,
                        "output": r.skill_output,
                        "reasoning": r.judge_reasoning,
                    }
                    for r in result.task_results
                ],
                "metrics": {
                    "intent_accuracy": result.intent_accuracy,
                    "constraint_coverage": result.constraint_coverage,
                    "output_quality": result.output_quality,
                    "verix_compliance": result.verix_compliance,
                    "l2_purity": result.l2_purity,
                },
            }
            print(json.dumps(output))
        else:
            evaluator.print_summary(result)

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
