"""Legacy patrol statistics and simulation."""


def segment_length_cm(p1, p2):
    """Return Manhattan segment length in centimeters; one cell is one meter."""
    return (
        abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
    ) * 100


def total_route_meters(points):
    """Return the total route length in meters."""
    distance_cm = 0
    for i in range(len(points) - 1):
        distance_cm += segment_length_cm(points[i], points[i + 1])
    return distance_cm / 100


def parse_event(line):
    """Parse an event into a dictionary; return None for dirty input."""
    if not isinstance(line, str):
        return None

    parts = line.strip().split(",")
    if len(parts) != 2 or parts[0] not in ("MOVE", "SCAN", "IDLE"):
        return None

    if not parts[1].isdigit():
        return None

    try:
        count = int(parts[1])
    except ValueError:
        return None

    return {"type": parts[0], "count": count}


def first_positive(samples):
    """Return the first positive sample, or None if none exists."""
    for sample in samples:
        if sample > 0:
            return sample
    return None


def calibrate(samples):
    """Return cumulative drift, or zero when no positive baseline exists."""
    baseline = first_positive(samples)
    if baseline is None:
        return 0

    return sum(sample - baseline for sample in samples)


def summarize_events(events, max_id):
    """Count events whose IDs are at most max_id and sum their steps."""
    used = 0
    steps = 0

    for event in events:
        if event["id"] <= max_id:
            used += 1
            steps += event["move"] + calibrate(event["samples"])

    return {"events": used, "steps": steps}


def log(message, history=None):
    """Append a message; omitted history starts a new list on every call."""
    if history is None:
        history = []

    history.append(message)
    return history


def run_legacy_sim(rounds, stamina_start=100):
    stamina = stamina_start
    trace = []

    for round_ in range(rounds):
        stamina -= 8
        if round_ >= 3:
            stamina -= 5

        trace.append((round_, stamina))

        if stamina <= 20:
            break

    return {
        "rounds": len(trace),
        "stamina": stamina,
        "trace": trace,
    }
