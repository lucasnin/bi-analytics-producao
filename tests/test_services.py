from datetime import date
from decimal import Decimal

import pytest

from app.ai.analytics_service import AnalyticsService
from app.ai.intent_parser import parse_intent, parse_question
from app.ai.query_validator import validate_readonly_sql
from app.repositories.dashboard_repository import DemoDashboardRepository
from app.repositories.csv_production_repository import CsvProductionRepository, REQUIRED_COLUMNS
from app.schemas.dashboard import DashboardFilters
from app.services.dashboard_service import DashboardService
from app.services.projection_service import ProjectionService


def test_projection_uses_business_days():
    result = ProjectionService().calculate(Decimal("1000"), Decimal("3000"), date(2026, 9, 10))
    assert result["projection"] > result["daily_average"]
    assert result["remaining"] == Decimal("2000")


def test_dashboard_contract():
    result = DashboardService(DemoDashboardRepository()).dashboard(DashboardFilters(start_date=date(2026, 9, 1), end_date=date(2026, 9, 10)))
    assert len(result["kpis"]) == 8
    assert result["teams"][0]["value"] > result["teams"][1]["value"]


def test_intent_is_deterministic():
    assert parse_intent("Qual equipe vendeu mais?") == "ranking_teams"


def test_chat_understands_relative_and_explicit_dates():
    reference = date(2026, 9, 15)
    assert AnalyticsService._resolve_period(parse_question("quanto foi integrado ontem?"), reference) == (
        date(2026, 9, 14), date(2026, 9, 14)
    )
    assert AnalyticsService._resolve_period(parse_question("integrado entre 01/09/2026 e 14/09/2026"), reference) == (
        date(2026, 9, 1), date(2026, 9, 14)
    )
    assert AnalyticsService._resolve_period(parse_question("produção nos últimos 7 dias"), reference) == (
        date(2026, 9, 9), date(2026, 9, 15)
    )


def test_chat_distinguishes_integrated_value_from_count():
    assert parse_question("quanto foi integrado ontem?").metric == "released"
    parsed = parse_question("quantos contratos foram pagos ontem?")
    assert parsed.metric == "count"
    assert parsed.status == "Integrado"


def test_sql_validator_blocks_mutation_and_unknown_views():
    with pytest.raises(ValueError): validate_readonly_sql("DELETE FROM bi_sales", {"bi_sales"})
    with pytest.raises(ValueError): validate_readonly_sql("SELECT id FROM secret", {"bi_sales"})
    validate_readonly_sql("SELECT total FROM bi_sales", {"bi_sales"})


def test_csv_uses_integration_date_only_for_integrated_status(tmp_path):
    import csv

    path = tmp_path / "production.csv"
    base = {column: "X" for column in REQUIRED_COLUMNS}
    rows = [
        base | {"id_front": "1", "Status_Funcao": "Integrado", "valor_contrato": "100,00", "valor_liberacao": "90,00",
                "data_cadastro": "2026-01-10", "data_integracao": "2026-02-03", "data_atualizacao": "2026-02-03 10:00:00"},
        base | {"id_front": "2", "Status_Funcao": "Cancelado", "valor_contrato": "50,00", "valor_liberacao": "0,00",
                "data_cadastro": "2026-01-12", "data_integracao": "2026-03-04", "data_atualizacao": "2026-03-04 10:00:00"},
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)
    repository = CsvProductionRepository(str(path))
    january = repository.snapshot(DashboardFilters(start_date=date(2026, 1, 1), end_date=date(2026, 1, 31)))
    february = repository.snapshot(DashboardFilters(start_date=date(2026, 2, 1), end_date=date(2026, 2, 28)))
    assert january["total"] == Decimal("50.00")
    assert january["integrated"] == Decimal(0)
    assert february["total"] == Decimal("100.00")
    assert february["integrated"] == Decimal("100.00")
