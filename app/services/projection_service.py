import calendar
from datetime import date
from decimal import Decimal


class ProjectionService:
    @staticmethod
    def business_days(year: int, month: int, through: int | None = None) -> int:
        last = through or calendar.monthrange(year, month)[1]
        return sum(date(year, month, day).weekday() < 5 for day in range(1, last + 1))

    def calculate(self, production: Decimal, goal: Decimal, reference: date) -> dict:
        elapsed = max(1, self.business_days(reference.year, reference.month, reference.day))
        total_days = self.business_days(reference.year, reference.month)
        average = production / elapsed
        projection = average * total_days
        remaining = max(Decimal(0), goal - production)
        remaining_days = max(1, total_days - elapsed)
        return {
            "projection": projection,
            "daily_average": average,
            "remaining": remaining,
            "achieved_pct": float((production / goal * 100) if goal else 0),
            "daily_needed": remaining / remaining_days if goal > 0 else Decimal(0),
            "trend": "no_goal" if goal <= 0 else ("on_track" if projection >= goal else "at_risk"),
        }
