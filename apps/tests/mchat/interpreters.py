def build_mchat_interpretation(computed_payload: dict, classification: dict) -> str:
    total_failures = computed_payload["total_failures"]
    critical_failures = computed_payload["critical_failures"]
    failed_items = computed_payload["failed_items"]
    failed_critical_items = computed_payload["failed_critical_items"]
    screen_result = classification["screen_result"]

    parts = [
        f"No M-CHAT, observou-se {total_failures} falha(s) no total, sendo {critical_failures} em item(ns) crítico(s).",
        f"O resultado indica {screen_result}.",
    ]

    if failed_items:
        parts.append(
            f"Os itens com falha foram: {', '.join(str(i) for i in failed_items)}."
        )

    if failed_critical_items:
        parts.append(
            f"Entre os itens críticos, houve falha em: {', '.join(str(i) for i in failed_critical_items)}."
        )

    if classification["screen_code"] == "positive":
        parts.append(
            "Trata-se de instrumento de rastreamento, de modo que um resultado positivo sugere necessidade de investigação clínica mais aprofundada."
        )
    else:
        parts.append(
            "Apesar do rastreio negativo, a interpretação deve considerar o contexto clínico e o desenvolvimento global da criança."
        )

    return " ".join(parts)
