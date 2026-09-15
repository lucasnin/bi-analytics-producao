import csv
import hashlib
import os
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from threading import Lock

from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import DashboardFilters

REQUIRED_COLUMNS = {
    "id_front", "convenio", "Esteira_Funcao", "Status_Funcao", "produto", "modalidade",
    "valor_contrato", "valor_liberacao", "Equipe_Padronizada", "operador", "gerente",
    "Gerente_Manual", "data_atualizacao", "data_cadastro", "data_integracao",
}


def parse_decimal(value: str) -> Decimal:
    normalized = (value or "").strip()
    if not normalized or normalized.upper() == "NULL":
        return Decimal(0)
    try:
        return Decimal(normalized.replace(".", "").replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError(f"Valor monetário inválido: {value}") from exc


def parse_date(value: str) -> date | None:
    normalized = (value or "").strip()
    if not normalized or normalized.upper() == "NULL":
        return None
    return datetime.fromisoformat(normalized).date()


class CsvProductionRepository(DashboardRepository):
    """Loads the current import once and reuses parsed rows until the file changes."""

    def __init__(self, path: str):
        self.path = Path(path)
        self._mtime = 0.0
        self._rows: list[dict] = []
        self._lock = Lock()

    def _load(self) -> list[dict]:
        if not self.path.exists():
            raise RuntimeError("Nenhum arquivo de produção foi importado")
        mtime = self.path.stat().st_mtime
        with self._lock:
            if self._rows and self._mtime == mtime:
                return self._rows
            with self.path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
                if missing:
                    raise ValueError("Colunas obrigatórias ausentes: " + ", ".join(sorted(missing)))
                rows = []
                for raw in reader:
                    rows.append({
                        "id": raw["id_front"].strip(), "agreement": raw["convenio"].strip(),
                        "stage": raw["Esteira_Funcao"].strip(), "status": raw["Status_Funcao"].strip(),
                        "product": raw["produto"].strip(), "modality": raw["modalidade"].strip(),
                        "contract": parse_decimal(raw["valor_contrato"]), "released": parse_decimal(raw["valor_liberacao"]),
                        "team": raw["Equipe_Padronizada"].strip(), "operator": raw["operador"].strip(),
                        "management": raw["gerente"].strip() if raw["gerente"].upper() != "NULL" else "Sem gerência",
                        "manual_management": raw.get("Gerente_Manual", "").strip() or "Sem gerência manual",
                        "created_at": parse_date(raw["data_cadastro"]), "integrated_at": parse_date(raw["data_integracao"]),
                        "updated_at": datetime.fromisoformat(raw["data_atualizacao"].strip()) if raw.get("data_atualizacao") else None,
                    })
            self._rows, self._mtime = rows, mtime
            return self._rows

    def snapshot(self, filters: DashboardFilters) -> dict:
        all_rows = self._load()
        dates = [self._business_date(row) for row in all_rows if self._business_date(row)]
        latest = max(dates)
        end = filters.end_date or latest
        start = filters.start_date or end.replace(day=1)
        rows = [row for row in all_rows if self._in_period(row, start, end) and self._matches(row, filters)]
        previous_end = start.fromordinal(start.toordinal() - 1)
        previous_start = previous_end.replace(day=1)
        previous = sum((row["contract"] for row in all_rows if self._in_period(row, previous_start, previous_end) and self._matches(row, filters)), Decimal(0))
        daily, teams, operators, managements, statuses = (defaultdict(Decimal) for _ in range(5))
        daily_status: dict[date, dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
        for row in rows:
            business_date = self._business_date(row)
            daily[business_date] += row["contract"]
            daily_status[business_date][row["status"]] += row["contract"]
            teams[row["team"]] += row["contract"]
            operators[row["operator"]] += row["contract"]
            managements[row["manual_management"]] += row["contract"]
            statuses[row["status"]] += row["contract"]
        total = sum((row["contract"] for row in rows), Decimal(0))
        integrated = sum((row["contract"] for row in rows if row["status"].casefold() == "integrado"), Decimal(0))
        daily_dates = sorted(daily)
        status_names = sorted({status for values in daily_status.values() for status in values})
        return {
            "total": total, "integrated": integrated, "contracts": Decimal(len({row["id"] for row in rows})),
            "goal": Decimal(0), "previous": previous,
            "daily": [{"label": key.strftime("%d/%m"), "value": value} for key, value in sorted(daily.items())],
            "daily_by_status": {status: [daily_status[current][status] for current in daily_dates] for status in status_names},
            "teams": self._rank(teams), "operators": self._rank(operators, 10),
            "managements": self._rank(managements), "statuses": self._rank(statuses, 10),
        }

    @staticmethod
    def _matches(row: dict, filters: DashboardFilters) -> bool:
        pairs = (("management", filters.management), ("manual_management", filters.manual_management), ("team", filters.team), ("operator", filters.operator),
                 ("product", filters.product), ("modality", filters.modality), ("agreement", filters.agreement),
                 ("status", filters.status))
        return all(not value or row[key].casefold() == value.casefold() for key, value in pairs)

    @staticmethod
    def _business_date(row: dict) -> date | None:
        """Power BI rule: Integrado uses data_integracao; every other status uses data_cadastro."""
        return row["integrated_at"] if row["status"].casefold() == "integrado" else row["created_at"]

    @classmethod
    def _in_period(cls, row: dict, start: date, end: date) -> bool:
        business_date = cls._business_date(row)
        return bool(business_date and start <= business_date <= end)

    @staticmethod
    def _rank(values: dict[str, Decimal], limit: int = 10) -> list[dict]:
        return [{"label": key, "value": value} for key, value in sorted(values.items(), key=lambda item: item[1], reverse=True)[:limit]]

    def metadata(self) -> dict:
        rows = self._load()
        dates = [self._business_date(row) for row in rows if self._business_date(row)]
        updates = [row["updated_at"] for row in rows if row["updated_at"]]
        return {"filename": self.path.name, "rows": len(rows), "start_date": min(dates), "end_date": max(dates),
                "latest_update": max(updates) if updates else None,
                "sha256": hashlib.sha256(self.path.read_bytes()).hexdigest(), "size_bytes": os.path.getsize(self.path)}

    def filter_options(self) -> dict:
        rows = self._load()
        values = lambda key: sorted({row[key] for row in rows if row[key]}, key=str.casefold)
        dates = [self._business_date(row) for row in rows if self._business_date(row)]
        return {"managements": values("management"), "manual_managements": values("manual_management"), "teams": values("team"), "operators": values("operator"),
                "products": values("product"), "modalities": values("modality"), "agreements": values("agreement"),
                "statuses": values("status"), "years": sorted({value.year for value in dates}, reverse=True),
                "latest_date": max(dates), "latest_update": max((row["updated_at"] for row in rows if row["updated_at"]), default=None)}

    def semantic_query(self, filters: DashboardFilters, metric: str, dimension: str | None, limit: int = 10) -> dict:
        rows = self._load()
        dates = [self._business_date(row) for row in rows if self._business_date(row)]
        end = filters.end_date or max(dates)
        start = filters.start_date or end.replace(day=1)
        selected = [row for row in rows if self._in_period(row, start, end) and self._matches(row, filters)]

        def measure(row: dict) -> Decimal:
            if metric == "count":
                return Decimal(1)
            if metric == "released":
                return row["contract"]
            return row["contract"]

        total = Decimal(len({row["id"] for row in selected})) if metric == "count" else sum((measure(row) for row in selected), Decimal(0))
        ranking = []
        if dimension:
            allowed = {"team", "operator", "management", "manual_management", "status", "product", "modality", "agreement", "stage"}
            if dimension not in allowed:
                raise ValueError("Dimensão não autorizada")
            grouped: dict[str, Decimal] = defaultdict(Decimal)
            if metric == "count":
                grouped_ids: dict[str, set[str]] = defaultdict(set)
                for row in selected:
                    grouped_ids[row[dimension]].add(row["id"])
                grouped = {key: Decimal(len(ids)) for key, ids in grouped_ids.items()}
            else:
                for row in selected:
                    grouped[row[dimension]] += measure(row)
            ranking = self._rank(grouped, limit)
        return {"total": total, "ranking": ranking, "start_date": start, "end_date": end, "metric": metric,
                "dimension": dimension, "status": filters.status}

    def monthly_integrated(self, filters: DashboardFilters, month_starts: list[date], cutoff_day: int) -> dict[date, dict[str, Decimal]]:
        wanted = {(value.year, value.month): value for value in month_starts}
        totals = {value: {"actual": Decimal(0), "cutoff": Decimal(0)} for value in month_starts}
        dimension_filters = filters.model_copy(update={"start_date": None, "end_date": None})
        for row in self._load():
            current = row["integrated_at"]
            if current and row["status"].casefold() == "integrado" and (current.year, current.month) in wanted and self._matches(row, dimension_filters):
                bucket = totals[wanted[(current.year, current.month)]]
                bucket["actual"] += row["contract"]
                if current.day <= cutoff_day:
                    bucket["cutoff"] += row["contract"]
        return totals

    def advanced_analytics(self, filters: DashboardFilters) -> dict:
        rows = self._load()
        latest = max(self._business_date(row) for row in rows if self._business_date(row))
        start, end = filters.start_date or latest.replace(day=1), filters.end_date or latest
        dimensions = {name: defaultdict(lambda: {"inserted": Decimal(0), "integrated": Decimal(0), "contracts": set(), "paid": set()}) for name in ("operator", "manual_management", "team", "agreement", "modality")}
        status = defaultdict(lambda: {"value": Decimal(0), "count": set()})
        for row in rows:
            if not self._matches(row, filters):
                continue
            created = row["created_at"] and start <= row["created_at"] <= end
            paid = row["status"].casefold() == "integrado" and row["integrated_at"] and start <= row["integrated_at"] <= end
            business = self._in_period(row, start, end)
            if business:
                status[row["status"]]["value"] += row["contract"]
                status[row["status"]]["count"].add(row["id"])
            for dimension, groups in dimensions.items():
                bucket = groups[row[dimension]]
                if created:
                    bucket["inserted"] += row["contract"]
                    bucket["contracts"].add(row["id"])
                if paid:
                    bucket["integrated"] += row["contract"]
                    bucket["paid"].add(row["id"])
        def output(groups):
            result=[]
            for label,value in groups.items():
                conversion=float(value["integrated"] / value["inserted"] * 100) if value["inserted"] else 0
                result.append({"label":label,"inserted":value["inserted"],"integrated":value["integrated"],"contracts":len(value["contracts"]),"paid":len(value["paid"]),"conversion":conversion})
            return sorted(result,key=lambda item:item["inserted"],reverse=True)
        return {"statuses":[{"label":key,"value":value["value"],"count":len(value["count"])} for key,value in sorted(status.items(),key=lambda item:item[1]["value"],reverse=True)], **{key:output(value) for key,value in dimensions.items()}}
