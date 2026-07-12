INSERT INTO
    problems (
        title,
        difficulty,
        statement,
        input_format,
        output_format,
        examples,
        constraints,
        sample_testcases,
        hidden_testcases,
        topics,
        hints,
        starter_code,
        daily_problem_id,
        contest_id
    )
VALUES (
        'Sum of Two Numbers',
        'Easy',
        'Given two integers A and B, return their sum.',
        'The input consists of two integers A and B.',
        'Print a single integer representing A + B.',
        '[
        {
            "input": "2 3",
            "output": "5",
            "explanation": "2 + 3 = 5"
        },
        {
            "input": "-4 10",
            "output": "6",
            "explanation": "-4 + 10 = 6"
        }
    ]'::jsonb,
        '{
        "A": "-1000000 <= A <= 1000000",
        "B": "-1000000 <= B <= 1000000"
    }'::jsonb,
        '[
        {
            "input": "1 2",
            "output": "3"
        },
        {
            "input": "100 200",
            "output": "300"
        },
        {
            "input": "-5 -7",
            "output": "-12"
        }
    ]'::jsonb,
        '[
        {
            "input": "999999 1",
            "output": "1000000"
        },
        {
            "input": "-1000000 1000000",
            "output": "0"
        },
        {
            "input": "0 0",
            "output": "0"
        }
    ]'::jsonb,
        ARRAY['Math', 'Implementation'],
        '[
        "Read two integers from input.",
        "Use the + operator.",
        "Print the result."
    ]'::jsonb,
        '{
        "cpp": "#include <iostream>\nusing namespace std;\n\nint main() {\n    // Write your code here\n    return 0;\n}",
        "python": "def solve():\n    # Write your code here\n    pass\n\nif __name__ == \"__main__\":\n    solve()",
        "java": "import java.util.*;\n\npublic class Main {\n    public static void main(String[] args) {\n        // Write your code here\n    }\n}"
    }'::jsonb,
        NULL,
        NULL
    );