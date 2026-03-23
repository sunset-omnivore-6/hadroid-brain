import plotly.graph_objects as go
from datetime import date, timedelta
from collections import defaultdict
from components.theme import BG_PRIMARY, BG_SECONDARY, TEXT_PRIMARY, TILE_COLOURS


CHART_LAYOUT = dict(
    paper_bgcolor=BG_PRIMARY,
    plot_bgcolor=BG_SECONDARY,
    font=dict(family="Lexend, sans-serif", color=TEXT_PRIMARY, size=13),
    margin=dict(l=40, r=20, t=40, b=40),
    xaxis=dict(gridcolor="#2a2a4e", zerolinecolor="#2a2a4e"),
    yaxis=dict(gridcolor="#2a2a4e", zerolinecolor="#2a2a4e"),
)


def plot_weight_over_time(logs, exercise_name):
    filtered = []
    for log in logs:
        for ex in log.get("exercises", []):
            if ex.get("name") == exercise_name:
                filtered.append({
                    "date": log.get("date"),
                    "weight": ex.get("weight_kg", 0),
                })
    if not filtered:
        return None

    filtered.sort(key=lambda x: x["date"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[f["date"] for f in filtered],
        y=[f["weight"] for f in filtered],
        mode="lines+markers",
        line=dict(color=TILE_COLOURS["exercise"], width=3),
        marker=dict(size=8),
        name="Weight (kg)",
    ))
    fig.update_layout(
        title=f"{exercise_name} — Weight Over Time",
        xaxis_title="Date",
        yaxis_title="Weight (kg)",
        **CHART_LAYOUT,
    )
    return fig


def plot_volume_per_session(logs):
    sessions = []
    for log in logs:
        total_volume = 0
        for ex in log.get("exercises", []):
            reps = ex.get("reps", [])
            sets = len(reps)
            avg_reps = sum(reps) / len(reps) if reps else 0
            weight = ex.get("weight_kg", 0)
            total_volume += sets * avg_reps * weight
        sessions.append({"date": log.get("date"), "volume": round(total_volume)})

    if not sessions:
        return None

    sessions.sort(key=lambda x: x["date"])
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[s["date"] for s in sessions],
        y=[s["volume"] for s in sessions],
        marker_color=TILE_COLOURS["exercise"],
        name="Volume (kg)",
    ))
    fig.update_layout(
        title="Volume Per Session",
        xaxis_title="Date",
        yaxis_title="Total Volume (sets x reps x weight)",
        **CHART_LAYOUT,
    )
    return fig


def plot_workout_frequency(logs):
    week_counts = defaultdict(int)
    for log in logs:
        d = date.fromisoformat(log.get("date", "2000-01-01"))
        monday = d - timedelta(days=d.weekday())
        week_counts[monday.isoformat()] += 1

    if not week_counts:
        return None

    sorted_weeks = sorted(week_counts.items())
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[w[0] for w in sorted_weeks],
        y=[w[1] for w in sorted_weeks],
        marker_color=TILE_COLOURS["exercise"],
        name="Sessions",
    ))
    fig.update_layout(
        title="Workout Frequency Per Week",
        xaxis_title="Week Starting",
        yaxis_title="Sessions",
        **CHART_LAYOUT,
    )
    return fig


def plot_chartership_radar(competencies):
    if not competencies:
        return None

    names = [c.get("name", "") for c in competencies]
    values = [c.get("progress_pct", 0) for c in competencies]
    # Close the radar
    names.append(names[0])
    values.append(values[0])

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=names,
        fill="toself",
        fillcolor="rgba(0, 168, 107, 0.3)",
        line=dict(color=TILE_COLOURS["work"], width=2),
    ))
    fig.update_layout(
        polar=dict(
            bgcolor=BG_SECONDARY,
            radialaxis=dict(
                visible=True, range=[0, 100],
                gridcolor="#2a2a4e",
                tickfont=dict(color=TEXT_PRIMARY),
            ),
            angularaxis=dict(gridcolor="#2a2a4e", tickfont=dict(color=TEXT_PRIMARY, size=11)),
        ),
        title="Chartership Progress",
        **{k: v for k, v in CHART_LAYOUT.items() if k not in ("xaxis", "yaxis")},
    )
    return fig
