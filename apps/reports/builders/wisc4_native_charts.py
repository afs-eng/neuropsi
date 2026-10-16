"""Dados atuais para os gráficos nativos SCARED e EPQ-J do modelo WISC-IV."""


def native_scale_data(service, key, context):
    if key.startswith("epq_j:"):
        test = service._find_test(context, "epq_j")
        if not test:
            raise ValueError("Gráfico EPQ-J sem resultados validados.")
        factors = (test.get("classified_payload") or {}).get("fatores") or {}
        column = "escore" if key == "epq_j:raw" else "percentil"
        labels = [code for code in ("P", "E", "N", "S") if code in factors]
        if any(factors[code].get(column) is None for code in labels):
            raise ValueError("Resultados incompletos para o gráfico EPQ-J.")
        values = [service._to_float(factors[code][column]) for code in labels]
        return labels, [values], ["RESULTADO BRUTO" if column == "escore" else "PERCENTIL"]

    from apps.tests.scared.config import PAIS_MAXIMOS
    from apps.tests.scared.norms import PAIS_CORTES

    index = int(key.split(":", 1)[1])
    tests = service._find_tests(context, "scared")
    if index < 0 or index >= len(tests):
        raise ValueError("Gráfico SCARED sem resultados validados.")
    payload = tests[index].get("classified_payload") or {}
    results = payload.get("analise_geral") or []
    labels = {
        "panico_sintomas_somaticos": "Pa/SS", "panico_somatico": "Pa/SS",
        "ansiedade_generalizada": "AG", "ansiedade_separacao": "AS",
        "fobia_social": "FS", "evitacao_escolar": "EE", "total": "TOTAL",
    }
    categories = [labels.get(item.get("fator"), str(item.get("fator") or "")) for item in results]
    if payload.get("form_type") != "parent":
        values = [item.get("percentil") if item.get("percentil") is not None else item.get("percentual") for item in results]
        if any(value is None for value in values):
            raise ValueError("Percentis ausentes para o gráfico SCARED Autorrelato.")
        return categories, [[service._to_float(value) for value in values]], ["Auto aplicação"]
    observed, cutoffs = [], []
    for item in results:
        factor = item.get("fator")
        factor = "panico_sintomas_somaticos" if factor == "panico_somatico" else factor
        maximum = PAIS_MAXIMOS.get(factor)
        if not maximum or item.get("escore_bruto") is None:
            raise ValueError("Resultados incompletos para o gráfico SCARED Mãe.")
        cutoff = item.get("nota_corte")
        if cutoff is None:
            cutoff = PAIS_CORTES[factor]
        observed.append(service._to_float(item["escore_bruto"]) * 100 / maximum)
        cutoffs.append(service._to_float(cutoff) * 100 / maximum)
    # Mesmas curvas de referência do modelo, recalculadas pelas normas atuais.
    return categories, [
        [value * 2 / 3 for value in cutoffs], cutoffs,
        [value * 4 / 3 for value in cutoffs], observed,
    ], ["-1/3", "nota de corte", "+1/3", "Paciente"]
