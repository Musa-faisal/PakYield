PRAGMA foreign_keys = ON;

-- ============================================================
-- PakYield Lab
-- Core SQLite Research Schema
-- Schema Version: 1
-- ============================================================


-- ------------------------------------------------------------
-- Schema version
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    description TEXT NOT NULL,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO schema_version (
    version,
    description
)
VALUES (
    1,
    'Initial PakYield research schema'
);


-- ------------------------------------------------------------
-- Ingestion provenance
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ingestion_runs (
    ingestion_run_id INTEGER PRIMARY KEY AUTOINCREMENT,

    dataset TEXT NOT NULL
        CHECK (
            dataset IN (
                'PKRV',
                'PKISRV',
                'SBP_POLICY_RATE',
                'SBP_MPC_EVENTS',
                'PBS_CPI'
            )
        ),

    source_organization TEXT NOT NULL,
    source_url TEXT,
    source_file TEXT,

    retrieved_at TEXT NOT NULL,

    status TEXT NOT NULL
        CHECK (
            status IN (
                'STARTED',
                'SUCCESS',
                'FAILED'
            )
        ),

    records_read INTEGER NOT NULL DEFAULT 0
        CHECK (records_read >= 0),

    records_written INTEGER NOT NULL DEFAULT 0
        CHECK (records_written >= 0),

    sha256 TEXT,
    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ------------------------------------------------------------
-- Sovereign benchmark yield observations
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS yield_observations (
    yield_observation_id INTEGER PRIMARY KEY AUTOINCREMENT,

    observation_date TEXT NOT NULL,

    curve_type TEXT NOT NULL
        CHECK (
            curve_type IN (
                'PKRV',
                'PKISRV'
            )
        ),

    tenor TEXT NOT NULL,

    tenor_years REAL NOT NULL
        CHECK (tenor_years > 0),

    yield_pct REAL NOT NULL
        CHECK (
            yield_pct > -100
            AND yield_pct < 100
        ),

    source_organization TEXT NOT NULL,
    source_file TEXT,

    ingestion_run_id INTEGER,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ingestion_run_id)
        REFERENCES ingestion_runs (ingestion_run_id),

    UNIQUE (
        observation_date,
        curve_type,
        tenor
    )
);


CREATE INDEX IF NOT EXISTS idx_yields_date
ON yield_observations (observation_date);


CREATE INDEX IF NOT EXISTS idx_yields_curve_date
ON yield_observations (
    curve_type,
    observation_date
);


CREATE INDEX IF NOT EXISTS idx_yields_tenor_date
ON yield_observations (
    tenor,
    observation_date
);


-- ------------------------------------------------------------
-- SBP Policy (Target) Rate
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS policy_rate_observations (
    policy_rate_id INTEGER PRIMARY KEY AUTOINCREMENT,

    effective_date TEXT NOT NULL UNIQUE,

    rate_pct REAL NOT NULL
        CHECK (
            rate_pct > -100
            AND rate_pct < 100
        ),

    series_key TEXT,

    observation_status TEXT,
    observation_status_comment TEXT,

    source_organization TEXT NOT NULL
        DEFAULT 'State Bank of Pakistan',

    source_file TEXT,

    ingestion_run_id INTEGER,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ingestion_run_id)
        REFERENCES ingestion_runs (ingestion_run_id)
);


CREATE INDEX IF NOT EXISTS idx_policy_rate_date
ON policy_rate_observations (effective_date);


-- ------------------------------------------------------------
-- SBP Monetary Policy Committee events
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS mpc_events (
    mpc_event_id INTEGER PRIMARY KEY AUTOINCREMENT,

    event_date TEXT NOT NULL UNIQUE,

    decision_type TEXT NOT NULL
        CHECK (
            decision_type IN (
                'HIKE',
                'CUT',
                'HOLD'
            )
        ),

    previous_rate_pct REAL,

    announced_rate_pct REAL,

    change_bps INTEGER,

    effective_date TEXT,

    statement_title TEXT,
    statement_url TEXT,

    source_organization TEXT NOT NULL
        DEFAULT 'State Bank of Pakistan',

    ingestion_run_id INTEGER,

    notes TEXT,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ingestion_run_id)
        REFERENCES ingestion_runs (ingestion_run_id),

    CHECK (
        change_bps IS NULL
        OR (
            decision_type = 'HIKE'
            AND change_bps > 0
        )
        OR (
            decision_type = 'CUT'
            AND change_bps < 0
        )
        OR (
            decision_type = 'HOLD'
            AND change_bps = 0
        )
    )
);


CREATE INDEX IF NOT EXISTS idx_mpc_event_date
ON mpc_events (event_date);


-- ------------------------------------------------------------
-- Pakistan Bureau of Statistics CPI
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS cpi_observations (
    cpi_observation_id INTEGER PRIMARY KEY AUTOINCREMENT,

    period TEXT NOT NULL UNIQUE,

    national_cpi_index REAL NOT NULL
        CHECK (national_cpi_index > 0),

    cpi_inflation_yoy_pct REAL NOT NULL
        CHECK (
            cpi_inflation_yoy_pct > -100
            AND cpi_inflation_yoy_pct < 100
        ),

    base_year TEXT NOT NULL
        DEFAULT '2015-16',

    source_organization TEXT NOT NULL
        DEFAULT 'Pakistan Bureau of Statistics',

    source_file TEXT,

    ingestion_run_id INTEGER,

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ingestion_run_id)
        REFERENCES ingestion_runs (ingestion_run_id)
);


CREATE INDEX IF NOT EXISTS idx_cpi_period
ON cpi_observations (period);