import calendar
from collections import defaultdict
from datetime import date
from decimal import Decimal

from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import DashboardFilters
from app.services.insight_service import InsightService
from app.services.projection_service import ProjectionService


class DashboardService:
    def __init__(self, repository: DashboardRepository):
        self.repository = repository
        self.projections = ProjectionService()
        self.insights = InsightService()

    def dashboard(self, filters: DashboardFilters) -> dict:
        data = self.repository.snapshot(filters)
        reference = filters.end_date or date.today()
        projection = self.projections.calculate(data["total"], data["goal"], reference)
        accumulated, running = [], Decimal(0)
        for point in data["daily"]:
            running += point["value"]
            accumulated.append({"label": point["label"], "value": running})
        change = float(((data["total"] / data["previous"]) - 1) * 100) if data["previous"] else 0
        status_values = {item["label"].casefold(): item["value"] for item in data["statuses"]}
        kpis = [
            {"key": "production", "label": "Produção total", "value": data["total"], "change": change},
            {"key": "integrated", "label": "Valor integrado", "value": data["integrated"]},
            {"key": "contracts", "label": "Contratos", "value": data["contracts"], "format": "number"},
            {"key": "cancelled", "label": "Valor cancelado", "value": status_values.get("cancelado", Decimal(0))},
            {"key": "progress", "label": "Em andamento", "value": status_values.get("andamento", Decimal(0))},
            {"key": "pending", "label": "Valor pendente", "value": status_values.get("pendente", Decimal(0))},
            {"key": "ticket", "label": "Ticket médio", "value": data["total"] / data["contracts"]},
            {"key": "change", "label": "Variação mensal", "value": Decimal(str(change)), "format": "percent", "change": change},
        ]
        monthly = self._monthly_analysis(filters)
        story = self._story(data, monthly, filters)
        analytics = self.repository.advanced_analytics(filters) if hasattr(self.repository, "advanced_analytics") else {}
        return {**data, "kpis": kpis, "accumulated": accumulated, "projection": projection,
                "monthly": monthly, "story": story, "analytics": analytics, "insights": self.insights.generate(data, projection)}

    def _monthly_analysis(self, filters: DashboardFilters) -> list[dict]:
        if not hasattr(self.repository, "semantic_query"):
            return []
        latest = self.repository.filter_options()["latest_date"]
        month_starts = []
        for offset in range(8, -1, -1):
            index = latest.year * 12 + latest.month - 1 - offset
            year, month = divmod(index, 12)
            month += 1
            month_starts.append(date(year, month, 1))
        totals = self.repository.monthly_integrated(filters, month_starts, latest.day)
        points = []
        for start in month_starts:
            integrated = totals[start]["actual"]
            cutoff = min(latest.day, calendar.monthrange(start.year, start.month)[1])
            elapsed = max(1, self.projections.business_days(start.year, start.month, cutoff))
            total_days = self.projections.business_days(start.year, start.month)
            projected = totals[start]["cutoff"] / elapsed * total_days
            variance = float((integrated / points[-1]["integrated"] - 1) * 100) if points and points[-1]["integrated"] else 0
            points.append({"label": start.strftime("%m/%Y"), "integrated": integrated, "projection": projected, "variance": variance})
        return points

    @staticmethod
    def _story(data: dict, monthly: list[dict], filters: DashboardFilters) -> list[str]:
        if not data["contracts"]:
            return ["Não há produção para a combinação de filtros selecionada."]
        top_team = data["teams"][0] if data["teams"] else None
        integrated_rate = float(data["integrated"] / data["total"] * 100) if data["total"] else 0
        story = [f"O período reúne {int(data['contracts']):,} contratos e R$ {data['total']:,.2f} em valor contratado."]
        story.append(f"O valor integrado representa {integrated_rate:.1f}% da produção filtrada.")
        if top_team:
            share = float(top_team["value"] / data["total"] * 100) if data["total"] else 0
            story.append(f"{top_team['label']} lidera entre as equipes, concentrando {share:.1f}% do valor contratado.")
        if monthly and monthly[-1]["projection"] > monthly[-1]["integrated"]:
            story.append(f"No ritmo atual, o integrado do mês pode alcançar R$ {monthly[-1]['projection']:,.2f}.")
        return story
