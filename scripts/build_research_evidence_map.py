"""Build the deterministic Phase 6D research-evidence map."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from pakyield.config import PROJECT_ROOT

DESCRIPTIVE_MANIFEST = (
    PROJECT_ROOT / "data" / "interim" / "descriptive_analysis_manifest.csv"
)

INFERENTIAL_MANIFEST = (
    PROJECT_ROOT / "data" / "interim" / "inferential_analysis_manifest.csv"
)

DIAGNOSTIC_MANIFEST = (
    PROJECT_ROOT / "data" / "interim" / "inferential_diagnostics_manifest.csv"
)

OUTPUT_PATH = PROJECT_ROOT / "data" / "interim" / "research_evidence_map.csv"

EXPECTED_DIAGNOSTIC_SHA = (
    "e059f18c249746136c02b20c593504408df4e873eca2b888209add7465473420"
)

FIELDS = [
    "target_id",
    "target_type",
    "research_theme",
    "evidence_class",
    "source_family",
    "source_artifact",
    "evidence_role",
    "priority",
    "diagnostic_requirement",
    "diagnostic_status",
    "interpretation_boundary",
]


def sha256_file(
    path: Path,
) -> str:
    """Return SHA-256 for one file."""

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def read_csv(
    path: Path,
) -> list[dict[str, str]]:
    """Read one CSV."""

    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def write_csv(
    path: Path,
    rows: list[dict[str, str]],
) -> None:
    """Atomically write deterministic output."""

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
            fieldnames=FIELDS,
        )

        writer.writeheader()
        writer.writerows(rows)

    temporary.replace(path)


def descriptive_lookup() -> dict[
    str,
    dict[str, str],
]:
    """Index descriptive families by manifest family."""

    rows = read_csv(DESCRIPTIVE_MANIFEST)

    output = {}

    for row in rows:
        family = row.get("descriptive_family") or row.get("family")

        if not family:
            raise RuntimeError("Descriptive manifest family field missing")

        output[family] = row

    return output


def inferential_lookup() -> dict[
    str,
    dict[str, str],
]:
    """Index inferential manifest families."""

    rows = read_csv(INFERENTIAL_MANIFEST)

    output = {}

    for row in rows:
        family = row["family"]

        if family in output:
            raise RuntimeError(f"Duplicate inferential family: {family}")

        output[family] = row

    return output


def diagnostic_lookup() -> dict[
    str,
    dict[str, str],
]:
    """Index and validate diagnostics."""

    actual_sha = sha256_file(DIAGNOSTIC_MANIFEST)

    if actual_sha != EXPECTED_DIAGNOSTIC_SHA:
        raise RuntimeError("Frozen Phase 6C diagnostic manifest changed")

    rows = read_csv(DIAGNOSTIC_MANIFEST)

    output = {}

    for row in rows:
        family = row["family"]

        if row["diagnostic_status"] != "PASS":
            raise RuntimeError(f"Inferential diagnostic family failed: {family}")

        output[family] = row

    return output


def make_row(
    *,
    target_id: str,
    target_type: str,
    research_theme: str,
    evidence_class: str,
    source_family: str,
    source_artifact: str,
    evidence_role: str,
    priority: str,
    diagnostic_requirement: str,
    diagnostic_status: str,
    interpretation_boundary: str,
) -> dict[str, str]:
    """Create one evidence-map row."""

    return {
        "target_id": target_id,
        "target_type": target_type,
        "research_theme": research_theme,
        "evidence_class": evidence_class,
        "source_family": source_family,
        "source_artifact": source_artifact,
        "evidence_role": evidence_role,
        "priority": priority,
        "diagnostic_requirement": diagnostic_requirement,
        "diagnostic_status": diagnostic_status,
        "interpretation_boundary": interpretation_boundary,
    }


def main() -> None:
    """Build Phase 6D evidence map."""

    descriptive = descriptive_lookup()
    inferential = inferential_lookup()
    diagnostics = diagnostic_lookup()

    required_descriptive = {
        "yield_levels",
        "yield_changes",
        "term_spreads",
        "cross_curve_differences",
        "mpc_event_windows",
        "monthly_sample_census",
    }

    if set(descriptive) != required_descriptive:
        raise RuntimeError(
            f"Unexpected descriptive family universe: {sorted(descriptive)}"
        )

    required_inferential = {
        "yield_level_regime",
        "yield_change_regime",
        "term_spread_regime",
        "cross_curve_zero",
        "cross_curve_regime",
        "mpc_event_window",
        "monthly_cpi_yield",
    }

    if set(inferential) != required_inferential:
        raise RuntimeError(
            f"Unexpected inferential family universe: {sorted(inferential)}"
        )

    if set(diagnostics) != required_inferential:
        raise RuntimeError("Unexpected diagnostic family universe")

    rows: list[dict[str, str]] = []

    def add_descriptive(
        target_id: str,
        target_type: str,
        theme: str,
        family: str,
        role: str,
        priority: str,
        boundary: str,
    ) -> None:
        manifest = descriptive[family]

        rows.append(
            make_row(
                target_id=target_id,
                target_type=target_type,
                research_theme=theme,
                evidence_class="DESCRIPTIVE",
                source_family=family,
                source_artifact=manifest["artifact_path"],
                evidence_role=role,
                priority=priority,
                diagnostic_requirement=("NOT_APPLICABLE"),
                diagnostic_status=("NOT_APPLICABLE"),
                interpretation_boundary=boundary,
            )
        )

    def add_inferential(
        target_id: str,
        target_type: str,
        theme: str,
        family: str,
        role: str,
        priority: str,
        boundary: str,
    ) -> None:
        manifest = inferential[family]

        diagnostic = diagnostics[family]

        rows.append(
            make_row(
                target_id=target_id,
                target_type=target_type,
                research_theme=theme,
                evidence_class="INFERENTIAL",
                source_family=family,
                source_artifact=manifest["artifact_path"],
                evidence_role=role,
                priority=priority,
                diagnostic_requirement=("PASS_REQUIRED"),
                diagnostic_status=diagnostic["diagnostic_status"],
                interpretation_boundary=boundary,
            )
        )

    def add_limitation(
        target_id: str,
        target_type: str,
        theme: str,
        family: str,
        artifact: str,
        role: str,
        priority: str,
        boundary: str,
    ) -> None:
        rows.append(
            make_row(
                target_id=target_id,
                target_type=target_type,
                research_theme=theme,
                evidence_class="DATA_LIMITATION",
                source_family=family,
                source_artifact=artifact,
                evidence_role=role,
                priority=priority,
                diagnostic_requirement=("NOT_APPLICABLE"),
                diagnostic_status=("NOT_APPLICABLE"),
                interpretation_boundary=boundary,
            )
        )

    # RQ1 — conventional yield-curve evolution.
    add_descriptive(
        "RQ1",
        "RESEARCH_QUESTION",
        "CONVENTIONAL_YIELD_CURVE",
        "yield_levels",
        "describes PKRV yield levels by regime and tenor",
        "PRIMARY",
        "descriptive regime comparison; not causal",
    )

    add_descriptive(
        "RQ1",
        "RESEARCH_QUESTION",
        "CONVENTIONAL_YIELD_CURVE",
        "yield_changes",
        "describes PKRV yield changes by regime and tenor",
        "PRIMARY",
        "descriptive regime comparison; not causal",
    )

    add_descriptive(
        "RQ1",
        "RESEARCH_QUESTION",
        "CONVENTIONAL_YIELD_CURVE",
        "term_spreads",
        "describes PKRV curve-shape spreads by regime",
        "PRIMARY",
        "spread sign or magnitude has no automatic causal interpretation",
    )

    add_inferential(
        "RQ1",
        "RESEARCH_QUESTION",
        "CONVENTIONAL_YIELD_CURVE",
        "yield_level_regime",
        "tests directional-regime differences in yield levels",
        "PRIMARY",
        "observational regime difference; not causal transmission",
    )

    add_inferential(
        "RQ1",
        "RESEARCH_QUESTION",
        "CONVENTIONAL_YIELD_CURVE",
        "yield_change_regime",
        "tests directional-regime differences in yield changes",
        "PRIMARY",
        "observational regime difference; not causal transmission",
    )

    add_inferential(
        "RQ1",
        "RESEARCH_QUESTION",
        "CONVENTIONAL_YIELD_CURVE",
        "term_spread_regime",
        "tests directional-regime differences in selected PKRV term spreads",
        "PRIMARY",
        "observational regime difference; not causal transmission",
    )

    # RQ2 — MPC announcement windows.
    add_descriptive(
        "RQ2",
        "RESEARCH_QUESTION",
        "MPC_ANNOUNCEMENT_WINDOWS",
        "mpc_event_windows",
        "describes yield movements around MPC observation windows",
        "PRIMARY",
        "announcement-window movement is not a policy-surprise estimate",
    )

    add_inferential(
        "RQ2",
        "RESEARCH_QUESTION",
        "MPC_ANNOUNCEMENT_WINDOWS",
        "mpc_event_window",
        "tests eligible event-window group means against zero",
        "PRIMARY",
        "not causal; groups with insufficient n remain descriptive-only",
    )

    add_limitation(
        "RQ2",
        "RESEARCH_QUESTION",
        "MPC_ANNOUNCEMENT_WINDOWS",
        "market_expectations",
        "",
        "no market-expectations series exists for policy-surprise identification",
        "CRITICAL",
        "policy-rate change must not be called policy surprise",
    )

    # RQ3 — conventional versus Shariah-compliant benchmarks.
    add_descriptive(
        "RQ3",
        "RESEARCH_QUESTION",
        "CROSS_CURVE_COMPARISON",
        "cross_curve_differences",
        "describes exact-date PKISRV minus PKRV benchmark differences",
        "PRIMARY",
        "numerical difference is not a structural premium or discount",
    )

    add_inferential(
        "RQ3",
        "RESEARCH_QUESTION",
        "CROSS_CURVE_COMPARISON",
        "cross_curve_zero",
        "tests whether numerical benchmark differences have zero mean",
        "PRIMARY",
        "does not identify why a benchmark difference exists",
    )

    add_inferential(
        "RQ3",
        "RESEARCH_QUESTION",
        "CROSS_CURVE_COMPARISON",
        "cross_curve_regime",
        "tests directional-regime differences in numerical benchmark differences",
        "PRIMARY",
        "does not identify structural Islamic-finance pricing mechanisms",
    )

    # RQ4 — macro relationships.
    add_descriptive(
        "RQ4",
        "RESEARCH_QUESTION",
        "MACRO_RELATIONSHIPS",
        "monthly_sample_census",
        "documents monthly CPI/yield sample availability",
        "CONTEXTUAL",
        "sample census is not a macroeconomic regression",
    )

    add_limitation(
        "RQ4",
        "RESEARCH_QUESTION",
        "MACRO_RELATIONSHIPS",
        "monthly_cpi_yield",
        inferential["monthly_cpi_yield"]["artifact_path"],
        "monthly CPI/yield family remains descriptive-only in Phase 6B",
        "CRITICAL",
        "no macroeconomic inferential relationship has been estimated",
    )

    # H1 — relative maturity sensitivity around MPC announcements.
    add_descriptive(
        "H1",
        "HYPOTHESIS",
        "MATURITY_SENSITIVITY",
        "mpc_event_windows",
        "provides maturity-specific announcement-window movement distributions",
        "PRIMARY",
        "support requires relative short-versus-long maturity evidence",
    )

    add_inferential(
        "H1",
        "HYPOTHESIS",
        "MATURITY_SENSITIVITY",
        "mpc_event_window",
        "provides maturity-specific non-zero event-window tests",
        "CONTEXTUAL",
        "individual significance does not directly test short-versus-long differences",
    )

    add_limitation(
        "H1",
        "HYPOTHESIS",
        "MATURITY_SENSITIVITY",
        "direct_maturity_contrast",
        "",
        "no dedicated short-minus-long event-response contrast is frozen",
        "CRITICAL",
        "H1 cannot be declared supported solely from individual maturity tests",
    )

    # H2 — co-movement.
    add_descriptive(
        "H2",
        "HYPOTHESIS",
        "CROSS_CURVE_COMOVEMENT",
        "cross_curve_differences",
        (
            "provides paired exact-date conventional/Shariah-compliant "
            "benchmark observations"
        ),
        "CONTEXTUAL",
        "difference distributions are not a direct co-movement statistic",
    )

    add_limitation(
        "H2",
        "HYPOTHESIS",
        "CROSS_CURVE_COMOVEMENT",
        "direct_comovement_test",
        "",
        "no dedicated correlation or co-movement inferential family is frozen",
        "CRITICAL",
        "H2 direct inferential status remains unresolved without a co-movement test",
    )

    # H3 — spread variation.
    add_descriptive(
        "H3",
        "HYPOTHESIS",
        "CROSS_CURVE_SPREAD_VARIATION",
        "cross_curve_differences",
        "describes numerical benchmark-difference variation across maturity and regime",
        "PRIMARY",
        "numerical difference is not a structural premium or discount",
    )

    add_inferential(
        "H3",
        "HYPOTHESIS",
        "CROSS_CURVE_SPREAD_VARIATION",
        "cross_curve_regime",
        "tests whether numerical benchmark differences vary by directional regime",
        "PRIMARY",
        "regime variation does not identify the economic cause of the difference",
    )

    add_inferential(
        "H3",
        "HYPOTHESIS",
        "CROSS_CURVE_SPREAD_VARIATION",
        "cross_curve_zero",
        "tests whether maturity-specific mean numerical differences equal zero",
        "CONTEXTUAL",
        "non-zero mean is not proof of time variation or a structural premium",
    )

    # H4 — term-spread regime distributions.
    add_descriptive(
        "H4",
        "HYPOTHESIS",
        "TERM_SPREAD_REGIME_VARIATION",
        "term_spreads",
        "describes selected PKRV term spreads across directional regimes",
        "PRIMARY",
        "regime association is observational",
    )

    add_inferential(
        "H4",
        "HYPOTHESIS",
        "TERM_SPREAD_REGIME_VARIATION",
        "term_spread_regime",
        "tests directional-regime differences in selected PKRV term spreads",
        "PRIMARY",
        "does not establish causal monetary-policy effects",
    )

    target_counts = {}

    for row in rows:
        target_counts[row["target_id"]] = (
            target_counts.get(
                row["target_id"],
                0,
            )
            + 1
        )

    expected_targets = {
        "RQ1",
        "RQ2",
        "RQ3",
        "RQ4",
        "H1",
        "H2",
        "H3",
        "H4",
    }

    if set(target_counts) != expected_targets:
        raise RuntimeError("Evidence-map target universe changed")

    for row in rows:
        if (
            row["evidence_class"] == "INFERENTIAL"
            and row["diagnostic_status"] != "PASS"
        ):
            raise RuntimeError("Inferential evidence without PASS diagnostics")

    write_csv(
        OUTPUT_PATH,
        rows,
    )

    print("===== PHASE 6D RESEARCH EVIDENCE MAP =====")

    print(
        "rows:",
        len(rows),
    )

    print(
        "targets:",
        target_counts,
    )

    class_counts = {}

    for row in rows:
        key = row["evidence_class"]

        class_counts[key] = (
            class_counts.get(
                key,
                0,
            )
            + 1
        )

    print(
        "evidence_classes:",
        class_counts,
    )

    print(
        "SHA256:",
        sha256_file(OUTPUT_PATH),
    )

    print("")
    print("PASS: Phase 6D research-evidence map constructed")


if __name__ == "__main__":
    main()
