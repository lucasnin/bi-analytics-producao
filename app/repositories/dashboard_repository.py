from abc import ABC, abstractmethod
from datetime import date, timedelta
from decimal import Decimal

from app.schemas.dashboard import DashboardFilters


class DashboardRepository(ABC):
    @abstractmethod
    def snapshot(self, filters: DashboardFilters) -> dict: ...


class DemoDashboardRepository(DashboardRepository):
    """Deterministic sample data; replace through MYSQL_MAPPING.md once the schema is known."""

    def snapshot(self, filters: DashboardFilters) -> dict:
        end = filters.end_date or date.today()
        start = filters.start_date or end.replace(day=1)
        days = max(1, (end - start).days + 1)
        daily = []
        for offset in range(days):
            current = start + timedelta(days=offset)
            if current.weekday() < 5:
                value = Decimal(118000 + ((offset * 37141) % 104000))
                daily.append({"label": current.strftime("%d/%m"), "value": value})
        total = sum((item["value"] for item in daily), Decimal(0))
        integrated = total * Decimal("0.82")
        contracts = Decimal(max(1, int(total / Decimal(6800))))
        goal = Decimal("4200000")
        teams = self._rank(["Aurora", "Nexus", "Impulso", "Vértice", "Atlas"], total)
        operators = self._rank(["Ana Lima", "Carlos Reis", "Marina Costa", "João Silva", "Bia Alves", "Rafael Luz"], total)
        managements = self._rank(["Sudeste", "Sul", "Centro"], total)
        return {
            "total": total,
            "integrated": integrated,
            "contracts": contracts,
            "goal": goal,
            "previous": total * Decimal("0.91"),
            "daily": daily,
            "daily_by_status": {
                "Integrado": [item["value"] * Decimal("0.82") for item in daily],
                "Em análise": [item["value"] * Decimal("0.11") for item in daily],
                "Pendente": [item["value"] * Decimal("0.07") for item in daily],
            },
            "teams": teams,
            "operators": operators,
            "managements": managements,
            "statuses": [
                {"label": "Integrado", "value": integrated},
                {"label": "Em análise", "value": total * Decimal("0.11")},
                {"label": "Pendente", "value": total * Decimal("0.07")},
            ],
        }

    @staticmethod
    def _rank(names: list[str], total: Decimal) -> list[dict]:
        weights = [Decimal(".29"), Decimal(".24"), Decimal(".19"), Decimal(".16"), Decimal(".08"), Decimal(".04")]
        return [{"label": name, "value": total * weights[index]} for index, name in enumerate(names)]


class MySQLDashboardRepository(DashboardRepository):
    def snapshot(self, filters: DashboardFilters) -> dict:
        raise RuntimeError(
            "O mapeamento MySQL ainda não foi configurado. Preencha MYSQL_MAPPING.md e implemente as views autorizadas."
        )
