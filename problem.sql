CREATE TABLE problems (
    problem_id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    statement TEXT NOT NULL,
    input_format TEXT,
    output_format TEXT,
    examples JSONB,
    constraints JSONB,
    sample_testcases JSONB,
    hidden_testcases JSONB,
    topics TEXT [],
    hints JSONB,
    starter_code JSONB,
    daily_problem_id UUID,
    contest_id UUID,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE problems
ADD CONSTRAINT fk_daily_problem FOREIGN KEY (daily_problem_id) REFERENCES daily_problems (daily_problem_id);

ALTER TABLE problems
ADD CONSTRAINT fk_contest FOREIGN KEY (contest_id) REFERENCES contests (contest_id);

CREATE TABLE daily_problems (
    daily_problem_id UUID PRIMARY KEY,
    prompt TEXT NOT NULL,
    generated_date DATE NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE contests (
    contest_id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    is_user_created BOOLEAN NOT NULL DEFAULT FALSE,
    user_id BIGINT,
    user_requirements JSONB,
    prompt JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);