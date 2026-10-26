"""All Gemini prompts live here."""

SYSTEM_PROMPT = """You are an expert competitive-programming problem setter.
You write original, self-contained problems that are judged automatically by comparing stdout.
You always answer with a single JSON object that matches the given schema, and nothing else."""

DIFFICULTY_GUIDE = {
    "easy": "a beginner problem solvable with one simple idea and a single loop or basic data structure",
    "medium": "an intermediate problem needing one well-known technique (e.g. hashing, two pointers, prefix sums, BFS, simple DP)",
    "hard": "an advanced problem combining techniques or needing a non-obvious insight, still solvable in under 60 lines of Python",
}


def build_problem_prompt(topic: str, difficulty: str) -> str:
    return f"""Create one {difficulty} coding problem about "{topic}".
Difficulty meaning: {DIFFICULTY_GUIDE[difficulty]}.

Rules:
- The program reads ALL input from stdin and writes the answer to stdout. No interactive problems,
  no floating point answers, no randomness, and exactly one correct output per input.
- input_format and output_format describe stdin/stdout precisely (line by line).
- constraints: 2-6 short lines such as "1 <= n <= 1000". Keep inputs small so test cases stay short.
- examples: 1-2 examples with input, output and a one-sentence explanation.
- hints: 1-3 short hints that do not give away the full solution.
- test_cases: 8-12 cases including edge cases (minimum sizes, duplicates, negatives if allowed, largest small case).
  Each input must be under 500 characters. expected_output must be EXACTLY what the reference solution prints.
- reference_solution: a complete, correct Python 3 program (standard library only) that reads stdin and prints
  the answer. No file, network or OS access. It will be run against every example and test case, and the problem
  is discarded if any output differs, so compute every expected_output carefully.
"""
