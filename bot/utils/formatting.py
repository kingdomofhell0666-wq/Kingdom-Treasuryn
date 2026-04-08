def format_dc(amount: int) -> str:
    return f"{amount:,} DC"


def format_rank_name(rank: str) -> str:
    return rank


def format_tax_rate(rate: float) -> str:
    return f"{int(rate * 100)}%"


def format_cost(cost: int) -> str:
    if cost >= 1_000_000:
        return f"{cost / 1_000_000:.1f}M DC"
    if cost >= 1_000:
        return f"{cost / 1_000:.0f}K DC"
    return f"{cost:,} DC"
