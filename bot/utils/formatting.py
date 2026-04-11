_DC = "<:devilcoinStack:1492184333392412692>"


def format_dc(amount: int) -> str:
    return f"{amount:,} {_DC}"


def format_rank_name(rank: str) -> str:
    return rank


def format_tax_rate(rate: float) -> str:
    return f"{int(rate * 100)}%"


def format_cost(cost: int) -> str:
    if cost >= 1_000_000:
        return f"{cost / 1_000_000:.1f}M {_DC}"
    if cost >= 1_000:
        return f"{cost / 1_000:.0f}K {_DC}"
    return f"{cost:,} {_DC}"
