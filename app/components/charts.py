from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def score_comparison_chart(df: pd.DataFrame) -> go.Figure:
    display = df.copy()
    display = display.sort_values("hybrid_score", ascending=False).head(12)

    figure = go.Figure()
    for column, label in [
        ("engine_score_side_to_move", "Engine score"),
        ("human_score_side_to_move", "Human score"),
        ("hybrid_score", "Hybrid score"),
    ]:
        if column in display:
            figure.add_trace(
                go.Bar(
                    x=display["move_san"],
                    y=display[column],
                    name=label,
                    text=[f"{value:.2f}" if pd.notna(value) else "" for value in display[column]],
                    textposition="auto",
                )
            )

    figure.update_layout(
        barmode="group",
        yaxis=dict(range=[0, 1], title="Score from side-to-move perspective"),
        xaxis=dict(title="Candidate move"),
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    )
    return figure

