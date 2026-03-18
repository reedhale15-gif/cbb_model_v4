import importlib.util
from pathlib import Path


_ROOT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "model_config.py"
_SPEC = importlib.util.spec_from_file_location("root_model_config", _ROOT_CONFIG_PATH)

if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Unable to load model_config from {_ROOT_CONFIG_PATH}")

_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

TOURNAMENT_MODE = _MODULE.TOURNAMENT_MODE

REGULAR_SPREAD_EDGE_MIN = _MODULE.REGULAR_SPREAD_EDGE_MIN
TOURNAMENT_SPREAD_EDGE_MIN = _MODULE.TOURNAMENT_SPREAD_EDGE_MIN
REGULAR_FAVORITE_SPREAD_EDGE_MAX = _MODULE.REGULAR_FAVORITE_SPREAD_EDGE_MAX
REGULAR_DOG_SPREAD_EDGE_MAX = _MODULE.REGULAR_DOG_SPREAD_EDGE_MAX
TOURNAMENT_FAVORITE_SPREAD_EDGE_MAX = _MODULE.TOURNAMENT_FAVORITE_SPREAD_EDGE_MAX
TOURNAMENT_DOG_SPREAD_EDGE_MAX = _MODULE.TOURNAMENT_DOG_SPREAD_EDGE_MAX

TOTAL_EDGE_MIN = _MODULE.TOTAL_EDGE_MIN
TOTAL_EDGE_MAX = _MODULE.TOTAL_EDGE_MAX

REGULAR_HOME_COURT = _MODULE.REGULAR_HOME_COURT
TOURNAMENT_HOME_COURT = _MODULE.TOURNAMENT_HOME_COURT

REGULAR_RECENCY_MULTIPLIER = _MODULE.REGULAR_RECENCY_MULTIPLIER
TOURNAMENT_RECENCY_MULTIPLIER = _MODULE.TOURNAMENT_RECENCY_MULTIPLIER


def spread_edge_band():
    return _MODULE.spread_edge_band()


def spread_edge_caps():
    return _MODULE.spread_edge_caps()


def spread_bet_side(market_spread, model_spread):
    return _MODULE.spread_bet_side(market_spread, model_spread)


def spread_bet_is_favorite(market_spread, model_spread):
    return _MODULE.spread_bet_is_favorite(market_spread, model_spread)


def spread_bet_qualifies(market_spread, model_spread, spread_edge):
    return _MODULE.spread_bet_qualifies(market_spread, model_spread, spread_edge)


def active_home_court():
    return _MODULE.active_home_court()


def active_recency_multiplier():
    return _MODULE.active_recency_multiplier()


def active_mode_label():
    return _MODULE.active_mode_label()
