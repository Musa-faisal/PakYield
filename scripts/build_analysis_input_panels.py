"""Build deterministic analysis-ready panels while preserving analytical grains."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

from pakyield.config import PROJECT_ROOT

INPUTS = {
    "policy_daily": {
        "path": PROJECT_ROOT / "data" / "interim" / "policy_rate_daily_state.csv",
        "rows": 1731,
        "sha": ("7655ddc7fd5cfd051ce628f006d8c4851b54ee47d4cbd90760e86cf9ebfd368a"),
    },
    "yield_changes": {
        "path": PROJECT_ROOT / "data" / "interim" / "yield_changes_long.csv",
        "rows": 24815,
        "sha": ("96dcc5c05b09221c18d030929a1be5f7a879cae57a0390448fed4a9f19160090"),
    },
    "cross_curve": {
        "path": PROJECT_ROOT / "data" / "interim" / "pkrv_pkisrv_same_date_panel.csv",
        "rows": 2035,
        "sha": ("9d17eda88a23c6106b3bab51bd56b2f64626488c533af0436e133b334dc32641"),
    },
    "monthly_cpi": {
        "path": PROJECT_ROOT / "data" / "interim" / "monthly_cpi_yield_panel.csv",
        "rows": 1234,
        "sha": ("978734c701969e049b4bd78c3a7c3d15b6534f530c19971c1b6df8efd6f370c7"),
    },
    "mpc_windows": {
        "path": PROJECT_ROOT / "data" / "interim" / "mpc_event_window_panel.csv",
        "rows": 936,
        "sha": ("b99224391fd254d3404ca7e0ce27073b2fdceee12cc0703a54af9b32e125472f"),
    },
    "term_spreads": {
        "path": PROJECT_ROOT / "data" / "interim" / "term_spread_panel.csv",
        "rows": 4596,
        "sha": ("5123ff3d4abe4a667d0854f3e9a8a8f9bf208368b8227bd3d31da2f011adb0ed"),
    },
    "regimes": {
        "path": PROJECT_ROOT / "data" / "interim" / "monetary_policy_regime_panel.csv",
        "rows": 1552,
        "sha": ("d53f6301048f2261551d467e322fe820970a0db7eea145fe0221a45142d9ff4b"),
    },
}

YIELD_OUTPUT = PROJECT_ROOT / "data" / "interim" / "yield_regime_analysis_panel.csv"

TERM_OUTPUT = (
    PROJECT_ROOT / "data" / "interim" / "term_spread_regime_analysis_panel.csv"
)

CROSS_OUTPUT = (
    PROJECT_ROOT / "data" / "interim" / "cross_curve_regime_analysis_panel.csv"
)

MANIFEST_OUTPUT = PROJECT_ROOT / "data" / "interim" / "analysis_input_manifest.csv"

REGIME_APPEND_FIELDS = [
    "regime_label",
    "regime_analysis_status",
    "regime_ineligibility_reason",
    "is_mpc_event_date",
    "same_day_mpc_event_type",
    "latest_prior_mpc_event_date",
    "latest_prior_mpc_event_type",
    "regime_origin_event_date",
    "regime_origin_event_type",
    "days_since_latest_prior_mpc_event",
    "days_since_regime_origin_event",
    "regime_classification_method",
]

POLICY_APPEND_FIELDS = [
    "policy_rate_pct",
    "policy_source_effective_date",
    "policy_is_source_effective_date",
    "policy_source_organization",
    "policy_source_file",
]

YIELD_SOURCE_FIELDS = [
    "observation_date",
    "curve_type",
    "tenor",
    "tenor_years",
    "yield_pct",
    "previous_observation_date",
    "previous_yield_pct",
    "observation_gap_days",
    "yield_change_bps",
    "change_method",
    "source_organization",
    "source_file",
    "ingestion_run_id",
]

YIELD_OUTPUT_FIELDS = (
    YIELD_SOURCE_FIELDS
    + REGIME_APPEND_FIELDS
    + POLICY_APPEND_FIELDS
    + [
        "yield_level_regime_analysis_status",
        "yield_level_regime_ineligibility_reason",
        "yield_change_regime_analysis_status",
        "yield_change_regime_ineligibility_reason",
    ]
)

TERM_SOURCE_FIELDS = [
    "observation_date",
    "curve_type",
    "spread_name",
    "long_tenor",
    "short_tenor",
    "long_tenor_years",
    "short_tenor_years",
    "long_yield_pct",
    "short_yield_pct",
    "term_spread_bps",
    "eligibility_status",
    "ineligibility_reason",
    "construction_method",
    "long_source_organization",
    "long_source_file",
    "long_ingestion_run_id",
    "short_source_organization",
    "short_source_file",
    "short_ingestion_run_id",
]

TERM_OUTPUT_FIELDS = (
    TERM_SOURCE_FIELDS
    + REGIME_APPEND_FIELDS
    + POLICY_APPEND_FIELDS
    + [
        "joint_analysis_status",
        "joint_ineligibility_reason",
    ]
)

CROSS_SOURCE_FIELDS = [
    "observation_date",
    "tenor",
    "tenor_years",
    "match_status",
    "pkrv_yield_pct",
    "pkisrv_yield_pct",
    "pkisrv_minus_pkrv_bps",
    "pkrv_source_organization",
    "pkrv_source_file",
    "pkrv_ingestion_run_id",
    "pkisrv_source_organization",
    "pkisrv_source_file",
    "pkisrv_ingestion_run_id",
]

CROSS_OUTPUT_FIELDS = (
    CROSS_SOURCE_FIELDS
    + REGIME_APPEND_FIELDS
    + POLICY_APPEND_FIELDS
    + [
        "paired_comparison_status",
        "paired_comparison_ineligibility_reason",
    ]
)

MANIFEST_FIELDS = [
    "analysis_family",
    "artifact_path",
    "grain",
    "row_count",
    "sha256",
    "regime_join_rule",
    "policy_join_rule",
    "eligibility_rule",
]


def sha256_file(
    path: Path,
) -> str:
    """Return SHA-256 for one file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest()


def display_path(
    path: Path,
) -> Path:
    """Return repository-relative path when possible."""

    if path.is_relative_to(PROJECT_ROOT):
        return path.relative_to(PROJECT_ROOT)

    return path


def read_csv(
    path: Path,
) -> tuple[
    list[str],
    list[dict[str, str]],
]:
    """Read one CSV."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        reader = csv.DictReader(file)

        return (
            list(reader.fieldnames or []),
            list(reader),
        )


def write_csv(
    path: Path,
    fields: list[str],
    rows: list[dict[str, str]],
) -> None:
    """Atomically write one deterministic CSV."""

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(path.suffix + ".part")

    with temporary.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fields,
        )

        writer.writeheader()
        writer.writerows(rows)

    temporary.replace(path)


def load_frozen_inputs() -> dict[
    str,
    dict[str, object],
]:
    """Load and verify every frozen upstream artifact."""

    loaded = {}

    for name, spec in INPUTS.items():
        path = spec["path"]

        if not path.is_file():
            raise RuntimeError(f"Missing frozen input: {path}")

        actual_sha = sha256_file(path)

        if actual_sha != spec["sha"]:
            raise RuntimeError(f"Frozen input SHA changed: {path}")

        headers, rows = read_csv(path)

        if len(rows) != spec["rows"]:
            raise RuntimeError(f"Frozen input row count changed: {path}")

        loaded[name] = {
            "headers": headers,
            "rows": rows,
        }

    return loaded


def validate_source_grains(
    loaded: dict[
        str,
        dict[str, object],
    ],
) -> None:
    """Validate the D095 source grains."""

    key_specs = {
        "yield_changes": (
            "observation_date",
            "curve_type",
            "tenor",
        ),
        "cross_curve": (
            "observation_date",
            "tenor",
        ),
        "monthly_cpi": (
            "period",
            "curve_type",
            "tenor",
        ),
        "mpc_windows": (
            "event_date",
            "curve_type",
            "tenor",
            "half_window",
        ),
        "term_spreads": (
            "observation_date",
            "curve_type",
            "spread_name",
        ),
        "regimes": (
            "observation_date",
            "curve_type",
        ),
        "policy_daily": ("date",),
    }

    for name, fields in key_specs.items():
        rows = loaded[name]["rows"]

        keys = [tuple(row[field] for field in fields) for row in rows]

        if len(keys) != len(set(keys)):
            raise RuntimeError(f"Duplicate analytical key in {name}: {fields}")


def build_regime_maps(
    regime_rows: list[dict[str, str]],
) -> tuple[
    dict[
        tuple[str, str],
        dict[str, str],
    ],
    dict[
        str,
        dict[str, str],
    ],
]:
    """Build exact curve-date and date-only regime maps."""

    by_curve_date = {}

    metadata_fields = [
        "regime_label",
        "regime_analysis_status",
        "ineligibility_reason",
        "is_mpc_event_date",
        "same_day_mpc_event_type",
        "latest_prior_mpc_event_date",
        "latest_prior_mpc_event_type",
        "regime_origin_event_date",
        "regime_origin_event_type",
        "days_since_latest_prior_mpc_event",
        "days_since_regime_origin_event",
        "classification_method",
    ]

    date_metadata = defaultdict(list)

    for row in regime_rows:
        key = (
            row["observation_date"],
            row["curve_type"],
        )

        if key in by_curve_date:
            raise RuntimeError(f"Duplicate regime key: {key}")

        by_curve_date[key] = row

        date_metadata[row["observation_date"]].append(row)

    by_date = {}

    for observation_date, rows in date_metadata.items():
        signatures = {tuple(row[field] for field in metadata_fields) for row in rows}

        if len(signatures) != 1:
            raise RuntimeError(
                f"Regime metadata differs by curve on {observation_date}"
            )

        by_date[observation_date] = rows[0]

    return (
        by_curve_date,
        by_date,
    )


def build_policy_map(
    policy_rows: list[dict[str, str]],
) -> dict[
    str,
    dict[str, str],
]:
    """Build exact-date policy-state map."""

    by_date = {}

    for row in policy_rows:
        observation_date = row["date"]

        if observation_date in by_date:
            raise RuntimeError(f"Duplicate policy daily date: {observation_date}")

        by_date[observation_date] = row

    return by_date


def regime_fields(
    regime: dict[str, str],
) -> dict[str, str]:
    """Return prefixed regime metadata."""

    return {
        "regime_label": (regime["regime_label"]),
        "regime_analysis_status": (regime["regime_analysis_status"]),
        "regime_ineligibility_reason": (regime["ineligibility_reason"]),
        "is_mpc_event_date": (regime["is_mpc_event_date"]),
        "same_day_mpc_event_type": (regime["same_day_mpc_event_type"]),
        "latest_prior_mpc_event_date": (regime["latest_prior_mpc_event_date"]),
        "latest_prior_mpc_event_type": (regime["latest_prior_mpc_event_type"]),
        "regime_origin_event_date": (regime["regime_origin_event_date"]),
        "regime_origin_event_type": (regime["regime_origin_event_type"]),
        "days_since_latest_prior_mpc_event": (
            regime["days_since_latest_prior_mpc_event"]
        ),
        "days_since_regime_origin_event": (regime["days_since_regime_origin_event"]),
        "regime_classification_method": (regime["classification_method"]),
    }


def policy_fields(
    policy: dict[str, str],
) -> dict[str, str]:
    """Return prefixed exact-date policy metadata."""

    return {
        "policy_rate_pct": (policy["policy_rate_pct"]),
        "policy_source_effective_date": (policy["source_effective_date"]),
        "policy_is_source_effective_date": (policy["is_source_effective_date"]),
        "policy_source_organization": (policy["source_organization"]),
        "policy_source_file": (policy["source_file"]),
    }


def get_exact_context(
    observation_date: str,
    curve_type: str,
    regime_by_curve_date: dict[
        tuple[str, str],
        dict[str, str],
    ],
    policy_by_date: dict[
        str,
        dict[str, str],
    ],
) -> tuple[
    dict[str, str],
    dict[str, str],
]:
    """Return exact regime and policy records."""

    regime = regime_by_curve_date.get(
        (
            observation_date,
            curve_type,
        )
    )

    if regime is None:
        raise RuntimeError(
            f"Missing exact regime match: {observation_date} {curve_type}"
        )

    policy = policy_by_date.get(observation_date)

    if policy is None:
        raise RuntimeError(f"Missing exact policy-state match: {observation_date}")

    return (
        regime,
        policy,
    )


def build_yield_panel(
    source_rows: list[dict[str, str]],
    regime_by_curve_date: dict[
        tuple[str, str],
        dict[str, str],
    ],
    policy_by_date: dict[
        str,
        dict[str, str],
    ],
) -> list[dict[str, str]]:
    """Build yield-level/change regime analysis input."""

    output = []

    for source in source_rows:
        regime, policy = get_exact_context(
            source["observation_date"],
            source["curve_type"],
            regime_by_curve_date,
            policy_by_date,
        )

        regime_eligible = regime["regime_analysis_status"] == "ELIGIBLE"

        change_available = bool(source["yield_change_bps"])

        if regime_eligible:
            level_status = "ELIGIBLE"
            level_reason = ""
        else:
            level_status = "INELIGIBLE"
            level_reason = regime["ineligibility_reason"]

        if regime_eligible and change_available:
            change_status = "ELIGIBLE"
            change_reason = ""

        elif not regime_eligible and not change_available:
            change_status = "INELIGIBLE"
            change_reason = "NO_PREVIOUS_YIELD_OBSERVATION_AND_REGIME_INELIGIBLE"

        elif not regime_eligible:
            change_status = "INELIGIBLE"
            change_reason = "REGIME_INELIGIBLE"

        else:
            change_status = "INELIGIBLE"
            change_reason = "NO_PREVIOUS_YIELD_OBSERVATION"

        row = {field: source[field] for field in YIELD_SOURCE_FIELDS}

        row.update(regime_fields(regime))

        row.update(policy_fields(policy))

        row["yield_level_regime_analysis_status"] = level_status

        row["yield_level_regime_ineligibility_reason"] = level_reason

        row["yield_change_regime_analysis_status"] = change_status

        row["yield_change_regime_ineligibility_reason"] = change_reason

        output.append(row)

    return output


def build_term_panel(
    source_rows: list[dict[str, str]],
    regime_by_curve_date: dict[
        tuple[str, str],
        dict[str, str],
    ],
    policy_by_date: dict[
        str,
        dict[str, str],
    ],
) -> list[dict[str, str]]:
    """Build term-spread regime analysis input."""

    output = []

    for source in source_rows:
        regime, policy = get_exact_context(
            source["observation_date"],
            source["curve_type"],
            regime_by_curve_date,
            policy_by_date,
        )

        spread_eligible = source["eligibility_status"] == "ELIGIBLE"

        regime_eligible = regime["regime_analysis_status"] == "ELIGIBLE"

        if spread_eligible and regime_eligible:
            status = "ELIGIBLE"
            reason = ""

        elif not spread_eligible and not regime_eligible:
            status = "INELIGIBLE"
            reason = "TERM_SPREAD_AND_REGIME_INELIGIBLE"

        elif not spread_eligible:
            status = "INELIGIBLE"
            reason = "TERM_SPREAD_INELIGIBLE"

        else:
            status = "INELIGIBLE"
            reason = "REGIME_INELIGIBLE"

        row = {field: source[field] for field in TERM_SOURCE_FIELDS}

        row.update(regime_fields(regime))

        row.update(policy_fields(policy))

        row["joint_analysis_status"] = status

        row["joint_ineligibility_reason"] = reason

        output.append(row)

    return output


def build_cross_panel(
    source_rows: list[dict[str, str]],
    regime_by_date: dict[
        str,
        dict[str, str],
    ],
    policy_by_date: dict[
        str,
        dict[str, str],
    ],
) -> list[dict[str, str]]:
    """Build exact-date cross-curve regime analysis input."""

    output = []

    for source in source_rows:
        observation_date = source["observation_date"]

        regime = regime_by_date.get(observation_date)

        if regime is None:
            raise RuntimeError(f"Missing date-level regime match: {observation_date}")

        policy = policy_by_date.get(observation_date)

        if policy is None:
            raise RuntimeError(f"Missing exact policy-state match: {observation_date}")

        pair_complete = all(
            (
                source["pkrv_yield_pct"],
                source["pkisrv_yield_pct"],
                source["pkisrv_minus_pkrv_bps"],
            )
        )

        regime_eligible = regime["regime_analysis_status"] == "ELIGIBLE"

        if pair_complete and regime_eligible:
            status = "ELIGIBLE"
            reason = ""

        elif not pair_complete and not regime_eligible:
            status = "INELIGIBLE"
            reason = "PAIR_AND_REGIME_INELIGIBLE"

        elif not pair_complete:
            status = "INELIGIBLE"
            reason = "CROSS_CURVE_PAIR_INELIGIBLE"

        else:
            status = "INELIGIBLE"
            reason = "REGIME_INELIGIBLE"

        row = {field: source[field] for field in CROSS_SOURCE_FIELDS}

        row.update(regime_fields(regime))

        row.update(policy_fields(policy))

        row["paired_comparison_status"] = status

        row["paired_comparison_ineligibility_reason"] = reason

        output.append(row)

    return output


def validate_derived_panels(
    yield_rows: list[dict[str, str]],
    term_rows: list[dict[str, str]],
    cross_rows: list[dict[str, str]],
) -> None:
    """Validate deterministic derived analytical inputs."""

    if len(yield_rows) != 24815:
        raise RuntimeError("Unexpected yield analysis row count")

    if len(term_rows) != 4596:
        raise RuntimeError("Unexpected term analysis row count")

    if len(cross_rows) != 2035:
        raise RuntimeError("Unexpected cross analysis row count")

    yield_keys = {
        (
            row["observation_date"],
            row["curve_type"],
            row["tenor"],
        )
        for row in yield_rows
    }

    if len(yield_keys) != 24815:
        raise RuntimeError("Duplicate yield analysis key")

    term_keys = {
        (
            row["observation_date"],
            row["curve_type"],
            row["spread_name"],
        )
        for row in term_rows
    }

    if len(term_keys) != 4596:
        raise RuntimeError("Duplicate term analysis key")

    cross_keys = {
        (
            row["observation_date"],
            row["tenor"],
        )
        for row in cross_rows
    }

    if len(cross_keys) != 2035:
        raise RuntimeError("Duplicate cross analysis key")

    term_joint = Counter(row["joint_analysis_status"] for row in term_rows)

    if term_joint != {
        "ELIGIBLE": 4164,
        "INELIGIBLE": 432,
    }:
        raise RuntimeError(f"Unexpected term joint eligibility: {dict(term_joint)}")

    term_reasons = Counter(
        row["joint_ineligibility_reason"]
        for row in term_rows
        if row["joint_analysis_status"] == "INELIGIBLE"
    )

    if term_reasons != {
        "REGIME_INELIGIBLE": 402,
        "TERM_SPREAD_INELIGIBLE": 28,
        "TERM_SPREAD_AND_REGIME_INELIGIBLE": 2,
    }:
        raise RuntimeError(f"Unexpected term joint reasons: {dict(term_reasons)}")

    for row in yield_rows + term_rows + cross_rows:
        if not row["policy_rate_pct"]:
            raise RuntimeError("Missing exact-date policy rate")

        if not row["regime_label"]:
            raise RuntimeError("Missing regime metadata")


def build_manifest(
    output_specs: list[
        tuple[
            str,
            Path,
            str,
            int,
            str,
            str,
            str,
        ]
    ],
) -> list[dict[str, str]]:
    """Build analysis-family manifest."""

    rows = []

    for (
        family,
        path,
        grain,
        row_count,
        regime_rule,
        policy_rule,
        eligibility_rule,
    ) in output_specs:
        rows.append(
            {
                "analysis_family": family,
                "artifact_path": str(display_path(path)),
                "grain": grain,
                "row_count": str(row_count),
                "sha256": sha256_file(path),
                "regime_join_rule": (regime_rule),
                "policy_join_rule": (policy_rule),
                "eligibility_rule": (eligibility_rule),
            }
        )

    return rows


def main() -> None:
    """Build all D095 analysis inputs."""

    loaded = load_frozen_inputs()

    validate_source_grains(loaded)

    regime_rows = loaded["regimes"]["rows"]

    policy_rows = loaded["policy_daily"]["rows"]

    (
        regime_by_curve_date,
        regime_by_date,
    ) = build_regime_maps(regime_rows)

    policy_by_date = build_policy_map(policy_rows)

    yield_rows = build_yield_panel(
        loaded["yield_changes"]["rows"],
        regime_by_curve_date,
        policy_by_date,
    )

    term_rows = build_term_panel(
        loaded["term_spreads"]["rows"],
        regime_by_curve_date,
        policy_by_date,
    )

    cross_rows = build_cross_panel(
        loaded["cross_curve"]["rows"],
        regime_by_date,
        policy_by_date,
    )

    validate_derived_panels(
        yield_rows,
        term_rows,
        cross_rows,
    )

    write_csv(
        YIELD_OUTPUT,
        YIELD_OUTPUT_FIELDS,
        yield_rows,
    )

    write_csv(
        TERM_OUTPUT,
        TERM_OUTPUT_FIELDS,
        term_rows,
    )

    write_csv(
        CROSS_OUTPUT,
        CROSS_OUTPUT_FIELDS,
        cross_rows,
    )

    manifest_rows = build_manifest(
        [
            (
                "yield_level_change_regime",
                YIELD_OUTPUT,
                ("curve_type × observation_date × tenor"),
                len(yield_rows),
                ("exact curve_type + observation_date"),
                "exact observation_date",
                (
                    "level requires eligible regime; "
                    "change additionally requires "
                    "non-missing yield_change_bps"
                ),
            ),
            (
                "term_spread_regime",
                TERM_OUTPUT,
                ("PKRV × observation_date × spread_name"),
                len(term_rows),
                ("exact curve_type + observation_date"),
                "exact observation_date",
                ("term spread and regime must both be ELIGIBLE"),
            ),
            (
                "cross_curve_regime",
                CROSS_OUTPUT,
                ("observation_date × comparable tenor"),
                len(cross_rows),
                ("date-level regime metadata only after cross-curve consistency check"),
                "exact observation_date",
                ("both curve legs + numerical spread and eligible regime required"),
            ),
            (
                "mpc_event_study",
                INPUTS["mpc_windows"]["path"],
                ("event_date × curve_type × tenor × half_window"),
                INPUTS["mpc_windows"]["rows"],
                "NOT_JOINED",
                "NOT_JOINED",
                ("uses event panel eligibility_status"),
            ),
            (
                "monthly_cpi_yield",
                INPUTS["monthly_cpi"]["path"],
                ("period × curve_type × tenor"),
                INPUTS["monthly_cpi"]["rows"],
                ("NOT_JOINED_PENDING_MONTHLY_ANCHOR_CONTRACT"),
                "NOT_JOINED",
                ("variable-specific non-missingness; no imputation"),
            ),
        ]
    )

    write_csv(
        MANIFEST_OUTPUT,
        MANIFEST_FIELDS,
        manifest_rows,
    )

    yield_level_status = Counter(
        row["yield_level_regime_analysis_status"] for row in yield_rows
    )

    yield_change_status = Counter(
        row["yield_change_regime_analysis_status"] for row in yield_rows
    )

    yield_change_reasons = Counter(
        row["yield_change_regime_ineligibility_reason"]
        for row in yield_rows
        if row["yield_change_regime_analysis_status"] == "INELIGIBLE"
    )

    term_status = Counter(row["joint_analysis_status"] for row in term_rows)

    term_reasons = Counter(
        row["joint_ineligibility_reason"]
        for row in term_rows
        if row["joint_analysis_status"] == "INELIGIBLE"
    )

    cross_status = Counter(row["paired_comparison_status"] for row in cross_rows)

    cross_reasons = Counter(
        row["paired_comparison_ineligibility_reason"]
        for row in cross_rows
        if row["paired_comparison_status"] == "INELIGIBLE"
    )

    print("===== D095 ANALYSIS INPUT PANELS =====")

    for path in (
        YIELD_OUTPUT,
        TERM_OUTPUT,
        CROSS_OUTPUT,
        MANIFEST_OUTPUT,
    ):
        print("")
        print(display_path(path))
        print(
            "SHA256:",
            sha256_file(path),
        )

    print("")
    print(
        "yield_level_status:",
        dict(yield_level_status),
    )

    print(
        "yield_change_status:",
        dict(yield_change_status),
    )

    print(
        "yield_change_reasons:",
        dict(yield_change_reasons),
    )

    print(
        "term_joint_status:",
        dict(term_status),
    )

    print(
        "term_joint_reasons:",
        dict(term_reasons),
    )

    print(
        "cross_pair_status:",
        dict(cross_status),
    )

    print(
        "cross_pair_reasons:",
        dict(cross_reasons),
    )

    print("")
    print("PASS: deterministic D095 analysis inputs constructed")


if __name__ == "__main__":
    main()
