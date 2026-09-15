import calendar
from datetime import date, timedelta

from app.ai.intent_parser import parse_intent, parse_question
from app.ai.provider import AIProvider
from app.schemas.ai import AskRequest
from app.services.dashboard_service import DashboardService


class AnalyticsService:
    def __init__(self, dashboard: DashboardService, provider: AIProvider | None = None):
        self.dashboard = dashboard
        self.provider = provider

    async def ask(self, request: AskRequest) -> dict:
        intent = parse_intent(request.question)
        parsed = parse_question(request.question)
        # What the user writes in the question takes precedence over a conflicting screen filter.
        if parsed.status:
            request.filters.status = parsed.status
        repository = self.dashboard.repository
        if hasattr(repository, "semantic_query"):
            latest = repository.filter_options()["latest_date"]
            period = self._resolve_period(parsed, latest)
            if period:
                request.filters.start_date, request.filters.end_date = period
            if intent == "unsupported" and not parsed.dimension and not parsed.status and not period:
                return {
                    "answer": "Não consegui identificar a análise nessa pergunta. Tente informar a métrica e o período, por exemplo: ‘quanto foi integrado ontem?’ ou ‘top 5 operadores de setembro’.",
                    "intent": "unsupported", "visualization": None, "value_format": "currency", "data": [],
                    "suggestions": ["Quanto foi integrado ontem?", "Top 5 operadores deste mês"], "used_ai": False,
                }
            query = repository.semantic_query(request.filters, parsed.metric, parsed.dimension, parsed.limit)
            result = self._semantic_answer(query)
            intent = f"{parsed.operation}_{parsed.dimension or parsed.metric}"
        else:
            snapshot = self.dashboard.dashboard(request.filters)
            result = self._deterministic(intent, snapshot)
        used_ai = False
        if self.provider and intent != "unsupported":
            try:
                prompt = "Explique em português, em no máximo duas frases, sem inventar números: " + result["answer"]
                result["answer"] = await self.provider.explain(prompt)
                used_ai = True
            except Exception:
                pass
        return {**result, "intent": intent, "used_ai": used_ai,
                "suggestions": ["Quanto foi integrado ontem?", "Mostre o TOP 10 operadores deste mês"]}

    @staticmethod
    def _resolve_period(parsed, reference: date) -> tuple[date, date] | None:
        """Resolve dates mentioned in the question using the latest available business date as 'today'."""
        if parsed.range_start and parsed.range_end:
            return parsed.range_start, parsed.range_end
        if parsed.exact_date:
            return parsed.exact_date, parsed.exact_date
        if parsed.relative_period:
            if parsed.relative_period == "today":
                return reference, reference
            if parsed.relative_period == "yesterday":
                target = reference - timedelta(days=1)
                return target, target
            if parsed.relative_period == "day_before_yesterday":
                target = reference - timedelta(days=2)
                return target, target
            if parsed.relative_period == "last_days":
                return reference - timedelta(days=(parsed.relative_days or 1) - 1), reference
            if parsed.relative_period in {"current_week", "previous_week"}:
                start = reference - timedelta(days=reference.weekday())
                if parsed.relative_period == "previous_week":
                    start -= timedelta(days=7)
                    return start, start + timedelta(days=6)
                return start, reference
            if parsed.relative_period in {"current_month", "previous_month"}:
                start = reference.replace(day=1)
                if parsed.relative_period == "previous_month":
                    end = start - timedelta(days=1)
                    return end.replace(day=1), end
                return start, reference
            if parsed.relative_period in {"current_year", "previous_year"}:
                target_year = reference.year - int(parsed.relative_period == "previous_year")
                end = date(target_year, 12, 31) if target_year != reference.year else reference
                return date(target_year, 1, 1), end
        if parsed.weekday is not None:
            target = reference - timedelta(days=(reference.weekday() - parsed.weekday) % 7)
            return target, target
        if parsed.month or parsed.year or parsed.day:
            year, month = parsed.year or reference.year, parsed.month or reference.month
            try:
                if parsed.day:
                    target = date(year, month, parsed.day)
                    return target, target
                if parsed.month:
                    return date(year, month, 1), date(year, month, calendar.monthrange(year, month)[1])
                return date(year, 1, 1), date(year, 12, 31)
            except ValueError:
                return None
        return None

    @staticmethod
    def _semantic_answer(query: dict) -> dict:
        count_label = "quantidade de contratos integrados" if (query.get("status") or "").casefold() == "integrado" else "quantidade de contratos"
        labels = {"contract": "produção", "released": "valor integrado", "count": count_label}
        dimensions = {"team": ("A", "equipe"), "operator": ("O", "operador"), "management": ("A", "gerência"),
                      "manual_management": ("A", "gerência manual"), "status": ("O", "status"), "product": ("O", "produto"),
                      "modality": ("A", "modalidade"), "agreement": ("O", "convênio"), "stage": ("A", "esteira")}
        metric = query["metric"]
        display = (lambda value: f"{int(value):,}".replace(",", ".")) if metric == "count" else (
            lambda value: f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        period = f"de {query['start_date'].strftime('%d/%m/%Y')} a {query['end_date'].strftime('%d/%m/%Y')}"
        if query["ranking"]:
            leader = query["ranking"][0]
            article, dimension_label = dimensions[query["dimension"]]
            answer = f"{article} principal {dimension_label} no período é {leader['label']}, com {display(leader['value'])} em {labels[metric]}."
            return {"answer": answer, "visualization": "ranking", "value_format": "number" if metric == "count" else "currency", "data": query["ranking"]}
        if query["dimension"]:
            return {"answer": f"Não encontrei dados por {dimensions[query['dimension']][1]} {period} com os filtros informados.",
                    "visualization": "ranking", "value_format": "number" if metric == "count" else "currency", "data": []}
        article = "O" if metric == "released" else "A"
        return {"answer": f"{article} {labels[metric]} {period} é {display(query['total'])}.", "visualization": "kpi",
                "value_format": "number" if metric == "count" else "currency", "data": []}

    @staticmethod
    def _deterministic(intent: str, data: dict) -> dict:
        money = lambda value: f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        if intent == "ranking_teams":
            top = data["teams"]
            return {"answer": f"A equipe {top[0]['label']} lidera com {money(top[0]['value'])}.", "visualization": "ranking", "data": top}
        if intent == "ranking_operators":
            top = data["operators"]
            return {"answer": f"{top[0]['label']} lidera a produção com {money(top[0]['value'])}.", "visualization": "ranking", "data": top}
        if intent == "projection":
            p = data["projection"]
            return {"answer": f"A projeção é {money(p['projection'])}; faltam {money(p['remaining'])} para a meta.", "visualization": "kpi", "data": []}
        if intent == "comparison":
            change = data["kpis"][-1]["value"]
            return {"answer": f"A variação frente ao período anterior é {float(change):.1f}%.", "visualization": "kpi", "data": []}
        if intent == "integrated":
            return {"answer": f"O valor integrado no período é {money(data['integrated'])}.", "visualization": "kpi", "data": []}
        if intent == "summary":
            return {"answer": f"A produção acumulada no período é {money(data['total'])}.", "visualization": "kpi", "data": []}
        return {"answer": "Ainda não reconheço essa análise. Pergunte sobre produção, integração, projeção, equipes ou operadores.", "visualization": None, "data": []}
