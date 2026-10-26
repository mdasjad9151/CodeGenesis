"""Shape of a Gemini-generated problem.

The same model is (1) sent to Gemini as response_schema and (2) used to validate what comes back.
Limits live in validators (not Field constraints) so the JSON schema sent to Gemini stays simple.
LLM output is never trusted: everything is length-checked here, and the reference solution only
ever runs inside Judge0.
"""
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Difficulty = Literal["easy", "medium", "hard"]

MAX_IO_CHARS = 5000


class GeneratedExample(BaseModel):
    input: str
    output: str
    explanation: str = ""


class GeneratedTestCase(BaseModel):
    input: str = Field(description="Exact stdin for the program")
    expected_output: str = Field(description="Exact stdout the reference solution prints for this input")


class GeneratedProblem(BaseModel):
    title: str
    description: str = Field(description="Problem statement in plain text/markdown")
    input_format: str
    output_format: str
    constraints: list[str]
    examples: list[GeneratedExample]
    hints: list[str]
    test_cases: list[GeneratedTestCase]
    reference_solution: str = Field(description="Complete Python 3 program that reads stdin and prints to stdout")

    @field_validator("title", "description", "input_format", "output_format", "reference_solution")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def check_limits(self):
        if not 3 <= len(self.title) <= 120:
            raise ValueError("title must be 3-120 characters")
        if not 20 <= len(self.description) <= 6000:
            raise ValueError("description must be 20-6000 characters")
        if not 1 <= len(self.examples) <= 3:
            raise ValueError("need 1-3 examples")
        if not 5 <= len(self.test_cases) <= 20:
            raise ValueError("need 5-20 test cases")
        if len(self.constraints) > 10 or len(self.hints) > 5:
            raise ValueError("too many constraints or hints")
        if not 10 <= len(self.reference_solution) <= 10000:
            raise ValueError("reference_solution must be 10-10000 characters")
        for case in [*self.test_cases, *self.examples]:
            output = case.expected_output if isinstance(case, GeneratedTestCase) else case.output
            if len(case.input) > MAX_IO_CHARS or len(output) > MAX_IO_CHARS:
                raise ValueError("test case input/output too large")
            if not output.strip():
                raise ValueError("test case with empty expected output")
        return self


class GenerateProblemRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=50)
    difficulty: Difficulty

    @field_validator("topic")
    @classmethod
    def clean_topic(cls, value: str) -> str:
        # The topic is interpolated into the prompt: keep it to a short plain phrase
        value = " ".join(value.lower().split())
        if not all(ch.isalnum() or ch in " -+#" for ch in value):
            raise ValueError("topic may only contain letters, digits, spaces and - + #")
        return value


class GenerateProblemResponse(BaseModel):
    problem_id: int
    title: str
    topic: str
    difficulty: Difficulty
    attempts: int


class DailyRunItem(BaseModel):
    difficulty: Difficulty
    status: Literal["created", "skipped", "failed"]
    problem_id: int | None = None
    detail: str | None = None


class DailyRunResponse(BaseModel):
    challenge_date: str
    topic: str
    results: list[DailyRunItem]
