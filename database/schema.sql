-- AI Workplace Intelligence Platform -- PostgreSQL Schema
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TYPE role_enum AS ENUM ('employee', 'manager');
CREATE TYPE action_item_status AS ENUM ('open', 'in_progress', 'done', 'cancelled');

CREATE TABLE teams (
    team_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(120) NOT NULL,
    department  VARCHAR(120),
    manager_id  UUID,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE employees (
    employee_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(200) NOT NULL,
    email           VARCHAR(320) UNIQUE NOT NULL,
    hashed_password VARCHAR(512) NOT NULL,
    role            role_enum NOT NULL DEFAULT 'employee',
    team_id         UUID REFERENCES teams(team_id) ON DELETE SET NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE teams ADD CONSTRAINT fk_teams_manager
    FOREIGN KEY (manager_id) REFERENCES employees(employee_id) ON DELETE SET NULL;

CREATE TABLE refresh_tokens (
    token_id    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    token_hash  VARCHAR(512) UNIQUE NOT NULL,
    family_id   UUID NOT NULL,
    revoked     BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at  TIMESTAMPTZ NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_refresh_tokens_hash   ON refresh_tokens(token_hash);
CREATE INDEX idx_refresh_tokens_family ON refresh_tokens(family_id);

CREATE TABLE meetings (
    meeting_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title             VARCHAR(300) NOT NULL,
    date              TIMESTAMPTZ NOT NULL,
    duration_mins     INTEGER,
    audio_s3_key      VARCHAR(512),
    transcript_s3_key VARCHAR(512),
    created_by        UUID NOT NULL REFERENCES employees(employee_id),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE meeting_analysis (
    analysis_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id       UUID UNIQUE NOT NULL REFERENCES meetings(meeting_id) ON DELETE CASCADE,
    summary          TEXT,
    decisions        JSONB,
    action_items     JSONB,
    confidence_score FLOAT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE meeting_analysis
    ADD COLUMN summary_tsv TSVECTOR
    GENERATED ALWAYS AS (to_tsvector('english', COALESCE(summary, ''))) STORED;
CREATE INDEX idx_meeting_summary_fts ON meeting_analysis USING GIN(summary_tsv);

CREATE TABLE productivity_metrics (
    metric_id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id               UUID NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    week_start                TIMESTAMPTZ NOT NULL,
    meeting_hours             FLOAT,
    focus_blocks              INTEGER,
    tasks_completed           INTEGER,
    overdue_tasks             FLOAT,
    after_hours_activity      INTEGER,
    response_time_avg         FLOAT,
    calendar_fragmentation    FLOAT,
    consecutive_meeting_ratio FLOAT,
    productivity_score        FLOAT,
    burnout_risk              FLOAT,
    cluster_label             VARCHAR(60),
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (employee_id, week_start)
);
CREATE INDEX idx_productivity_employee_week ON productivity_metrics(employee_id, week_start DESC);

CREATE TABLE action_items (
    item_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    meeting_id  UUID NOT NULL REFERENCES meetings(meeting_id) ON DELETE CASCADE,
    assignee_id UUID REFERENCES employees(employee_id) ON DELETE SET NULL,
    task_text   TEXT NOT NULL,
    due_date    TIMESTAMPTZ,
    status      action_item_status NOT NULL DEFAULT 'open',
    confidence  FLOAT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_action_items_assignee ON action_items(assignee_id, status);
