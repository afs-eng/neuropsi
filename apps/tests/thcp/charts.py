from io import BytesIO

from matplotlib.figure import Figure


def build_percentile_chart(data: dict) -> bytes:
    rows = [row for row in data.get("results", []) if row.get("percentile") is not None]
    if not rows:
        return b""
    fig = Figure(figsize=(8, 3.5), layout="constrained")
    ax = fig.subplots()
    bars = ax.barh([row["label"] for row in rows], [row["percentile"] for row in rows], color="#0e7490")
    ax.bar_label(bars, labels=[str(row["percentile"]) for row in rows], padding=3, fontsize=9)
    ax.set_xlim(0, 110)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("Percentil estimado pela distribuição normal")
    ax.invert_yaxis()
    ax.spines[["top", "right"]].set_visible(False)
    output = BytesIO()
    fig.savefig(output, format="png", dpi=150)
    return output.getvalue()
