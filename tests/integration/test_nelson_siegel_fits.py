"""Integration tests for production Nelson-Siegel artifacts."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
from collections import Counter, defaultdict
from math import sqrt
from pathlib import Path
from types import ModuleType

import pytest

from pakyield.config import (
    DATABASE_PATH,
)
from pakyield.database.connection import (
    get_connection,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

BUILDER_PATH = PROJECT_ROOT / "scripts" / "build_nelson_siegel_fits.py"


def load_builder() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "build_nelson_siegel_fits",
        BUILDER_PATH,
    )

    assert spec is not None
    assert spec.loader is not None

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


BUILDER = load_builder()


def read_csv(
    path: Path,
) -> list[dict[str, str]]:
    with path.open(
        newline="",
        encoding="utf-8",
    ) as file:
        return list(csv.DictReader(file))


def run_builder(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[
    Path,
    Path,
]:
    date_path = tmp_path / "date_fits.csv"

    point_path = tmp_path / "fitted_yields.csv"

    monkeypatch.setattr(
        BUILDER,
        "DATE_OUTPUT",
        date_path,
    )

    monkeypatch.setattr(
        BUILDER,
        "POINT_OUTPUT",
        point_path,
    )

    BUILDER.main()

    assert date_path.is_file()
    assert point_path.is_file()

    return (
        date_path,
        point_path,
    )


def test_production_shape_status_and_eligibility(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    date_path, point_path = run_builder(
        tmp_path,
        monkeypatch,
    )

    date_rows = read_csv(date_path)

    point_rows = read_csv(point_path)

    assert len(date_rows) == 1552
    assert len(point_rows) == 24815

    assert Counter(
        (
            row["curve_type"],
            row["fit_status"],
        )
        for row in date_rows
    ) == {
        (
            "PKRV",
            "FIT",
        ): 1149,
        (
            "PKISRV",
            "INELIGIBLE",
        ): 403,
    }

    assert Counter(
        (
            row["curve_type"],
            row["fit_status"],
        )
        for row in point_rows
    ) == {
        (
            "PKRV",
            "FIT",
        ): 22800,
        (
            "PKISRV",
            "INELIGIBLE",
        ): 2015,
    }


def test_pkrv_point_fits_and_date_rmse_reconcile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    date_path, point_path = run_builder(
        tmp_path,
        monkeypatch,
    )

    date_rows = read_csv(date_path)

    point_rows = read_csv(point_path)

    points_by_date: dict[
        str,
        list[dict[str, str]],
    ] = defaultdict(list)

    for row in point_rows:
        if row["curve_type"] == "PKRV":
            points_by_date[row["observation_date"]].append(row)

    date_lookup = {
        row["observation_date"]: row for row in date_rows if row["curve_type"] == "PKRV"
    }

    assert len(points_by_date) == 1149

    for (
        observation_date,
        rows,
    ) in points_by_date.items():
        residuals = []

        for row in rows:
            observed = float(row["observed_yield_pct"])

            fitted = float(row["fitted_yield_pct"])

            residual = float(row["residual_pct_points"])

            assert residual == (
                pytest.approx(
                    observed - fitted,
                    abs=2e-11,
                )
            )

            residuals.append(residual)

        reconstructed_rmse = sqrt(sum(value**2 for value in residuals) / len(residuals))

        stored_rmse = float(date_lookup[observation_date]["rmse_pct_points"])

        assert stored_rmse == (
            pytest.approx(
                reconstructed_rmse,
                abs=2e-10,
            )
        )


def test_pkisrv_structural_exclusion_is_explicit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    date_path, point_path = run_builder(
        tmp_path,
        monkeypatch,
    )

    date_rows = [row for row in read_csv(date_path) if row["curve_type"] == "PKISRV"]

    point_rows = [row for row in read_csv(point_path) if row["curve_type"] == "PKISRV"]

    expected_reason = "POINTS_LT_10;NO_BELLY;NO_LONG;SPAN_LT_15Y"

    assert len(date_rows) == 403
    assert len(point_rows) == 2015

    assert all(row["fit_status"] == "INELIGIBLE" for row in date_rows)

    assert all(row["ineligibility_reason"] == expected_reason for row in date_rows)

    assert all(
        row["beta0"] == ""
        and row["beta1"] == ""
        and row["beta2"] == ""
        and row["rmse_pct_points"] == ""
        for row in date_rows
    )

    assert all(
        row["fitted_yield_pct"] == "" and row["residual_pct_points"] == ""
        for row in point_rows
    )


def test_point_output_preserves_every_production_yield_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, point_path = run_builder(
        tmp_path,
        monkeypatch,
    )

    derived = read_csv(point_path)

    connection = get_connection(DATABASE_PATH)

    try:
        production = connection.execute(
            """
                SELECT
                    yield_observation_id,
                    observation_date,
                    curve_type,
                    tenor,
                    tenor_years,
                    yield_pct
                FROM yield_observations
                ORDER BY
                    curve_type,
                    observation_date,
                    tenor_years,
                    tenor
                """
        ).fetchall()

    finally:
        connection.close()

    production_by_id = {str(row["yield_observation_id"]): row for row in production}

    assert len(production_by_id) == 24815

    assert len(derived) == 24815

    for row in derived:
        source = production_by_id[row["yield_observation_id"]]

        assert row["observation_date"] == source["observation_date"]

        assert row["curve_type"] == source["curve_type"]

        assert row["tenor"] == source["tenor"]

        assert float(row["tenor_years"]) == pytest.approx(float(source["tenor_years"]))

        assert float(row["observed_yield_pct"]) == pytest.approx(
            float(source["yield_pct"])
        )


def test_production_builder_is_byte_deterministic(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_date, first_point = run_builder(
        tmp_path,
        monkeypatch,
    )

    first_date_bytes = first_date.read_bytes()

    first_point_bytes = first_point.read_bytes()

    first_date_sha = hashlib.sha256(first_date_bytes).hexdigest()

    first_point_sha = hashlib.sha256(first_point_bytes).hexdigest()

    second_date, second_point = run_builder(
        tmp_path,
        monkeypatch,
    )

    assert second_date.read_bytes() == first_date_bytes

    assert second_point.read_bytes() == first_point_bytes

    assert hashlib.sha256(second_date.read_bytes()).hexdigest() == first_date_sha

    assert hashlib.sha256(second_point.read_bytes()).hexdigest() == first_point_sha
