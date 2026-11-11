"""Stable subdomain slots; unavailable scores break the line, never become zero."""

from .config import DOMAINS, SUBDOMAINS
from .norms import domain_members

HEADER_LINES = {
    "COM": ["COMUNICAÇÃO"], "AVD": ["ATIVIDADES DE VIDA", "DIÁRIA"],
    "SOC": ["SOCIALIZAÇÃO"], "HMOT": ["HABILIDADES", "MOTORAS"],
}

def subdomain_profile(result):
    members = domain_members(result["form"])
    scores = {row["scale"]: row for row in result.get("subdomains", [])}
    columns, groups, segments, segment = [], [], [], []
    index = 0
    for domain, codes in members.items():
        start = index
        for code in codes:
            row = scores.get(code, {})
            score = row.get("v_scale")
            x = 70 + index * 44
            y = 364 - (score - 1) * 12 if score is not None else None
            columns.append({"code": code, "label": SUBDOMAINS[code], "display_code": "CMD" if code == "com" else code.upper(),
                            "x": x, "y": y, "score": score})
            if score is None:
                if segment:
                    segments.append(segment)
                segment = []
            else:
                segment.append((x, y))
            index += 1
        groups.append({"code": domain, "label": DOMAINS[domain], "header_lines": HEADER_LINES[domain], "x": 48 + start * 44,
                       "width": len(codes) * 44, "center": 48 + start * 44 + len(codes) * 22})
    if segment:
        segments.append(segment)
    return {"columns": columns, "groups": groups, "right": 48 + index * 44,
            "ticks": [{"value": value, "y": 364 - (value - 1) * 12, "reference": value in (6, 9, 12, 15)} for value in range(1, 25)],
            "segments": [" ".join(f"{x},{y}" for x, y in points) for points in segments]}
