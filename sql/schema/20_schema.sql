-- SCHEMA CREATION FOR open-cp DATABASE
-- Run this *after* the database + roles are created.

-- ============================================
-- USERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    fname       TEXT NOT NULL,
    lname       TEXT NOT NULL,
    username    TEXT NOT NULL UNIQUE,
    rating      INTEGER DEFAULT 0
);

-- ============================================
-- PROBLEMS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS problems (
    id              SERIAL PRIMARY KEY,
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    author          TEXT NOT NULL,
    tags            TEXT[],
    rating          INTEGER DEFAULT 0,
    time_limit      INTEGER NOT NULL,     -- ms
    mem_limit       INTEGER NOT NULL,     -- MB
    sample_in       TEXT,
    sample_out      TEXT,
    in_test_ref     TEXT,
    out_test_ref    TEXT
);

-- ============================================
-- SUBMISSIONS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS submissions (
    id          SERIAL PRIMARY KEY,
    problem_id  INTEGER NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date        TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    verdict     TEXT NOT NULL,
    time_usage  INTEGER,   -- ms
    mem_usage   INTEGER,   -- kB
    code        TEXT NOT NULL
);

-- Useful indices
CREATE INDEX IF NOT EXISTS idx_submissions_problem_id ON submissions(problem_id);
CREATE INDEX IF NOT EXISTS idx_submissions_user_id ON submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_problems_rating ON problems(rating);
CREATE INDEX IF NOT EXISTS idx_users_rating ON users(rating);
