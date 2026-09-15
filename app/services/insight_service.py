from decimal import Decimal


class InsightService:
    def generate(self, snapshot: dict, projection: dict) -> list[dict]:
        insights = []
        change = ((snapshot["total"] / snapshot["previous"]) - 1) * 100 if snapshot["previous"] else Decimal(0)
        insights.append({
            "type": "highlight" if change >= 0 else "alert",
            "title": "Evolução no período",
            "text": f"A produção está {abs(float(change)):.1f}% {'acima' if change >= 0 else 'abaixo'} do período anterior.",
        })
        if projection["trend"] == "at_risk":
            insights.append({
                "type": "alert",
                "title": "Risco para a meta",
                "text": f"A média necessária é R$ {projection['daily_needed']:,.0f} por dia útil restante.",
            })
        elif projection["trend"] == "on_track":
            insights.append({"type": "highlight", "title": "Meta no radar", "text": "A projeção atual supera a meta mensal."})
        return insights
