-- problem-service schema (database: problems)
-- Applied automatically on service startup; every statement is idempotent.
-- user ids come from auth-service (UUID). There is no FK to users: that table lives in another database.

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE IF NOT EXISTS problems (
    problem_id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    difficulty VARCHAR(20) NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
    statement TEXT NOT NULL,
    input_format TEXT,
    output_format TEXT,
    examples JSONB NOT NULL DEFAULT '[]',          -- [{input, output, explanation}]
    constraints JSONB NOT NULL DEFAULT '[]',       -- ["1 <= n <= 10^5", ...]
    sample_testcases JSONB NOT NULL DEFAULT '[]',  -- [{input, output}] shown to users
    hidden_testcases JSONB NOT NULL DEFAULT '[]',  -- [{input, output}] never returned by public APIs
    topics TEXT [] NOT NULL DEFAULT '{}',          -- lower-case tags, e.g. {'arrays','math'}
    hints JSONB NOT NULL DEFAULT '[]',
    starter_code JSONB NOT NULL DEFAULT '{}',      -- {"python": "...", "cpp": "..."}
    created_by UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_problems_topics ON problems USING GIN (topics);

CREATE TABLE IF NOT EXISTS submissions (
    submission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    problem_id BIGINT NOT NULL REFERENCES problems (problem_id) ON DELETE CASCADE,
    language VARCHAR(20) NOT NULL,
    source_code TEXT NOT NULL,

    -- queued -> running -> completed | failed
    status VARCHAR(20) NOT NULL DEFAULT 'queued',
    -- Accepted, Wrong Answer, Time Limit Exceeded, Runtime Error, Compilation Error, Internal Error
    verdict VARCHAR(30),
    passed_count INT,
    total_count INT,
    runtime_ms INT,      -- max time over all test cases
    memory_kb INT,       -- max memory over all test cases
    error_output TEXT,   -- compiler/runtime error of the first failing test case

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_submissions_user_id ON submissions (user_id);
CREATE INDEX IF NOT EXISTS idx_submissions_problem_id ON submissions (problem_id);

-- One problem per (date, difficulty), filled by ai-service's daily job
CREATE TABLE IF NOT EXISTS daily_problems (
    challenge_date DATE NOT NULL,
    difficulty VARCHAR(20) NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
    problem_id BIGINT NOT NULL REFERENCES problems (problem_id) ON DELETE CASCADE,
    topic TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (challenge_date, difficulty)
);

-- Topic-based practice contests, created instantly by users (POST /api/v1/contests/generate)
CREATE TABLE IF NOT EXISTS contests (
    contest_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    topic TEXT NOT NULL,
    difficulty VARCHAR(20) NOT NULL CHECK (difficulty IN ('easy', 'medium', 'hard')),
    created_by UUID NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS contest_problems (
    contest_id UUID NOT NULL REFERENCES contests (contest_id) ON DELETE CASCADE,
    problem_id BIGINT NOT NULL REFERENCES problems (problem_id) ON DELETE CASCADE,
    position INT NOT NULL,
    PRIMARY KEY (contest_id, problem_id)
);

-- Submissions made inside a contest count towards that contest's score
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS contest_id UUID REFERENCES contests (contest_id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_submissions_contest_id ON submissions (contest_id);
