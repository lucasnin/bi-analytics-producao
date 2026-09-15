import re

BLOCKED = re.compile(r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke|replace|call)\b", re.I)


def validate_readonly_sql(sql: str, allowed_views: set[str]) -> None:
    normalized = sql.strip().rstrip(";")
    if not normalized.lower().startswith("select") or BLOCKED.search(normalized) or ";" in normalized:
        raise ValueError("Somente uma consulta SELECT é permitida")
    names = set(re.findall(r"\b(?:from|join)\s+([a-zA-Z0-9_\.]+)", normalized, re.I))
    if not names or not names.issubset(allowed_views):
        raise ValueError("A consulta referencia uma fonte não autorizada")

