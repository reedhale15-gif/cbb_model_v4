TOURNAMENT_MODE = True

# Spread/totals bet filters
REGULAR_SPREAD_EDGE_MIN = 6.0
TOURNAMENT_SPREAD_EDGE_MIN = 6.0
REGULAR_FAVORITE_SPREAD_EDGE_MAX = 12.0
REGULAR_DOG_SPREAD_EDGE_MAX = 8.5
TOURNAMENT_FAVORITE_SPREAD_EDGE_MAX = 10.0
TOURNAMENT_DOG_SPREAD_EDGE_MAX = 8.5

TOTAL_EDGE_MIN = 6.0
TOTAL_EDGE_MAX = 12.0

# Projection tuning
REGULAR_HOME_COURT = 3.0
TOURNAMENT_HOME_COURT = 0.0

REGULAR_RECENCY_MULTIPLIER = 1.0
TOURNAMENT_RECENCY_MULTIPLIER = 0.5


def spread_edge_band():
    if TOURNAMENT_MODE:
        return TOURNAMENT_SPREAD_EDGE_MIN, TOURNAMENT_FAVORITE_SPREAD_EDGE_MAX
    return REGULAR_SPREAD_EDGE_MIN, REGULAR_FAVORITE_SPREAD_EDGE_MAX


def spread_edge_caps():
    if TOURNAMENT_MODE:
        return TOURNAMENT_FAVORITE_SPREAD_EDGE_MAX, TOURNAMENT_DOG_SPREAD_EDGE_MAX
    return REGULAR_FAVORITE_SPREAD_EDGE_MAX, REGULAR_DOG_SPREAD_EDGE_MAX


def spread_bet_side(market_spread, model_spread):
    return "home" if model_spread < market_spread else "away"


def spread_bet_is_favorite(market_spread, model_spread):
    side = spread_bet_side(market_spread, model_spread)
    if side == "home":
        return market_spread < 0
    return market_spread > 0


def spread_bet_qualifies(market_spread, model_spread, spread_edge):
    min_edge, favorite_cap = spread_edge_band()
    _, dog_cap = spread_edge_caps()
    max_edge = favorite_cap if spread_bet_is_favorite(market_spread, model_spread) else dog_cap
    return min_edge <= abs(spread_edge) <= max_edge


def active_home_court():
    if TOURNAMENT_MODE:
        return TOURNAMENT_HOME_COURT
    return REGULAR_HOME_COURT


def active_recency_multiplier():
    if TOURNAMENT_MODE:
        return TOURNAMENT_RECENCY_MULTIPLIER
    return REGULAR_RECENCY_MULTIPLIER


def active_mode_label():
    return "TOURNAMENT" if TOURNAMENT_MODE else "REGULAR"
