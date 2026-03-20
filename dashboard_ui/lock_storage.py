import hashlib


LOCK_HEADERS = ["uid", "source", "option", "time", "game", "bet_type", "bet", "edge", "confidence", "market_line"]


def make_lock_uid(lock):
    base = "|".join([
        str(lock.get("source", "manual")),
        str(lock.get("option", "")),
        str(lock.get("time", "")),
        str(lock.get("game", "")),
        str(lock.get("bet_type", "")),
        str(lock.get("bet", "")),
        str(lock.get("edge", "")),
        str(lock.get("confidence", "")),
        str(lock.get("market_line", "")),
    ])
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:12]


def normalize_lock_record(lock):
    normalized = {
        "uid": lock.get("uid", "") or make_lock_uid(lock),
        "source": lock.get("source", "manual"),
        "option": lock.get("option", ""),
        "time": lock.get("time", ""),
        "game": lock.get("game", ""),
        "bet_type": lock.get("bet_type", ""),
        "bet": lock.get("bet", ""),
        "edge": lock.get("edge", ""),
        "confidence": lock.get("confidence", ""),
        "market_line": lock.get("market_line", ""),
    }
    return normalized


def parse_locks_values(values):

    if len(values) < 2:
        return []

    headers = [str(h).strip().lower() for h in values[0]]

    if headers == ["lock"]:
        return [
            _legacy_lock_record(value[0])
            for value in values[1:]
            if value and value[0]
        ]

    records = []

    for row in values[1:]:
        padded = row + [""] * max(0, len(headers) - len(row))
        record = dict(zip(headers, padded))

        if not any(record.values()):
            continue

        records.append(normalize_lock_record(record))

    return records


def _legacy_lock_record(option):
    option = str(option)
    game = option
    bet = option

    if " — " in option:
        game, bet = option.split(" — ", 1)
    elif " - " in option:
        game, bet = option.split(" - ", 1)

    return normalize_lock_record({
        "source": "auto",
        "option": option,
        "game": game,
        "bet": bet,
    })


def build_locks_rows(locks):

    normalized = [normalize_lock_record(lock) for lock in locks]

    deduped = []
    seen = set()
    for lock in normalized:
        key = tuple(lock.items())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(lock)

    rows = [
        LOCK_HEADERS
    ]
    for lock in deduped:
        rows.append([
            lock["uid"],
            lock["source"],
            lock["option"],
            lock["time"],
            lock["game"],
            lock["bet_type"],
            lock["bet"],
            lock["edge"],
            lock["confidence"],
            lock["market_line"],
        ])

    return rows
