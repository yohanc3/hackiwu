-- HackTitan Database Schema
-- PostgreSQL DB hosted @ Supabase 

CREATE TABLE IF NOT EXISTS staff_users (
    id            SERIAL       PRIMARY KEY,
    email         TEXT         UNIQUE NOT NULL,
    password_hash TEXT         NOT NULL,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS applications (
    id               SERIAL       PRIMARY KEY,
    first_name       TEXT         NOT NULL,
    last_name        TEXT         NOT NULL,
    email            TEXT         UNIQUE NOT NULL,
    phone            TEXT,
    age_confirm      BOOLEAN      NOT NULL,
    accuracy_confirm BOOLEAN      NOT NULL,
    media_release    BOOLEAN      NOT NULL DEFAULT FALSE,
    school           TEXT         NOT NULL,
    school_other     TEXT,
    year             TEXT         NOT NULL,
    major            TEXT         NOT NULL,
    grad_year        TEXT         NOT NULL,
    experience       TEXT         NOT NULL,
    team_status      TEXT         NOT NULL,
    track_preference TEXT,
    dietary          TEXT[],
    dietary_other    TEXT,
    linkedin         TEXT,
    referral         TEXT         NOT NULL,
    submitted_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
