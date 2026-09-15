import re
import unicodedata
from dataclasses import dataclass
from datetime import date


def normalize_text(value: str) -> str:
    value = re.sub(r"\s+", " ", value.casefold()).strip()
    return "".join(character for character in unicodedata.normalize("NFD", value) if unicodedata.category(character) != "Mn")


INTENTS = {
    "ranking_teams": ("equipe", "equipes", "time", "times", "ranking"),
    "ranking_operators": ("operador", "operadores", "vendedor", "vendedores", "consultor", "consultores"),
    "projection": ("projecao", "fechamento", "tendencia", "bater a meta", "quanto falta"),
    "comparison": ("compare", "comparacao", "mes anterior", "periodo anterior", "variacao", "queda", "crescimento"),
    "integrated": ("integrado", "integrados", "integracao", "pago", "pagos", "pagou", "pagamento"),
    "summary": ("vendeu", "vendemos", "producao", "faturamento", "valor", "total", "quanto", "quantos", "quantas", "proposta", "contrato"),
}


def parse_intent(question: str) -> str:
    normalized = normalize_text(question)
    for intent, terms in INTENTS.items():
        if any(term in normalized for term in terms):
            return intent
    return "unsupported"


DIMENSIONS = {
    "team": ("equipe", "equipes", "time", "times"),
    "operator": ("operador", "operadores", "vendedor", "vendedores", "consultor", "consultores", "atendente"),
    "manual_management": ("gerencia manual", "gerente manual", "andar"),
    "management": ("gerencia", "gerencias", "gerente", "gerentes"),
    "status": ("status", "situacao", "situacoes"),
    "product": ("produto", "produtos"),
    "modality": ("modalidade", "modalidades"),
    "agreement": ("convenio", "convenios"),
    "stage": ("esteira", "esteiras", "etapa", "etapas", "funcao"),
}

STATUS_TERMS = (
    (("cancelad", "cancelamento"), "Cancelado"),
    (("reprovad", "reprovacao"), "Reprovado"),
    (("andamento", "em analise"), "Andamento"),
    (("pendente", "pendencia"), "Pendente"),
    (("integrado", "integracao", "pago", "pagos", "pagou", "pagamento"), "Integrado"),
    (("liberado", "liberacao"), "Liberado"),
)

MONTHS = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}

WEEKDAYS = {
    "segunda": 0, "terca": 1, "quarta": 2, "quinta": 3, "sexta": 4, "sabado": 5, "domingo": 6,
}


@dataclass(frozen=True)
class ParsedQuestion:
    metric: str
    dimension: str | None
    operation: str
    limit: int
    status: str | None
    year: int | None
    month: int | None
    day: int | None
    exact_date: date | None = None
    range_start: date | None = None
    range_end: date | None = None
    relative_period: str | None = None
    relative_days: int | None = None
    weekday: int | None = None


def _parsed_numeric_dates(normalized: str) -> list[date]:
    values: list[date] = []
    patterns = (
        (r"\b(\d{1,2})[/-](\d{1,2})[/-](20\d{2})\b", lambda groups: (int(groups[2]), int(groups[1]), int(groups[0]))),
        (r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", lambda groups: (int(groups[0]), int(groups[1]), int(groups[2]))),
    )
    for pattern, reorder in patterns:
        for match in re.finditer(pattern, normalized):
            try:
                values.append(date(*reorder(match.groups())))
            except ValueError:
                continue
    return values


def parse_question(question: str) -> ParsedQuestion:
    normalized = normalize_text(question)
    count_terms = ("quantos", "quantas", "quantidade", "numero de", "qtd")
    metric = "count" if any(term in normalized for term in count_terms) else "contract"
    paid_terms = ("integrado", "integracao", "pago", "pagos", "pagou", "pagamento", "liberado", "liberacao")
    if metric != "count" and any(term in normalized for term in paid_terms):
        metric = "released"
    dimension = next((key for key, terms in DIMENSIONS.items() if any(term in normalized for term in terms)), None)
    operation = "ranking" if dimension or any(term in normalized for term in ("top", "maior", "melhor", "menor", "ranking", "lidera")) else "summary"
    match = re.search(r"\btop\s*(\d{1,2})\b", normalized)
    limit = min(20, max(1, int(match.group(1)))) if match else 10
    status = next((value for terms, value in STATUS_TERMS if any(term in normalized for term in terms)), None)

    numeric_dates = _parsed_numeric_dates(normalized)
    exact_date = numeric_dates[0] if len(numeric_dates) == 1 else None
    range_start = min(numeric_dates[0], numeric_dates[1]) if len(numeric_dates) >= 2 else None
    range_end = max(numeric_dates[0], numeric_dates[1]) if len(numeric_dates) >= 2 else None

    month = next((value for name, value in MONTHS.items() if name in normalized), None)
    year_match = re.search(r"\b(20\d{2})\b", normalized)
    day_match = re.search(r"\bdia\s+(\d{1,2})(?![/-])", normalized)

    relative_period = None
    relative_days = None
    if "anteontem" in normalized:
        relative_period = "day_before_yesterday"
    elif "ontem" in normalized:
        relative_period = "yesterday"
    elif "hoje" in normalized:
        relative_period = "today"
    elif "semana passada" in normalized or "ultima semana" in normalized:
        relative_period = "previous_week"
    elif "esta semana" in normalized or "semana atual" in normalized:
        relative_period = "current_week"
    elif "mes passado" in normalized or "ultimo mes" in normalized:
        relative_period = "previous_month"
    elif "este mes" in normalized or "mes atual" in normalized:
        relative_period = "current_month"
    elif "ano passado" in normalized or "ultimo ano" in normalized:
        relative_period = "previous_year"
    elif "este ano" in normalized or "ano atual" in normalized:
        relative_period = "current_year"
    else:
        days_match = re.search(r"(?:ultimos|ultimas)\s+(\d{1,3})\s+dias", normalized)
        if days_match:
            relative_period = "last_days"
            relative_days = min(366, max(1, int(days_match.group(1))))

    weekday = None
    if not relative_period and not numeric_dates:
        weekday = next((value for name, value in WEEKDAYS.items() if re.search(rf"\b{name}(?:-feira)?\b", normalized)), None)

    return ParsedQuestion(
        metric=metric,
        dimension=dimension,
        operation=operation,
        limit=limit,
        status=status,
        year=int(year_match.group(1)) if year_match else None,
        month=month,
        day=int(day_match.group(1)) if day_match else None,
        exact_date=exact_date,
        range_start=range_start,
        range_end=range_end,
        relative_period=relative_period,
        relative_days=relative_days,
        weekday=weekday,
    )
