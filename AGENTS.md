## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)

## Session: Correção de Exportação DOCX — Gráficos, Tabelas e Consistência de Dados

### Problema
Laudo de Leticia Bolonha Lucati apresentava inconsistência: gráfico WASI mostrava QIV=115, QIE=123, mas texto da interpretação usava QIV=118, QIE=120. Isso acontecia porque:
1. **`clinical_interpretation`** e **`summary`** do teste WASI eram gerados por IA com dados de uma avaliação anterior (stale)
2. O gráfico era populado corretamente via `computed_payload` → `_wasi_chart_payload`
3. A interpretação textual vinha da `_resolve_interpretation_text` que usava o texto salvo (stale)

### Correções Aplicadas em `apps/reports/services/report_export_service.py`

**1. `_wasi_payload` (linha 4385):** Removeu busca pela chave intermediária `"composites"` como source separado, que causava sobreposição de dados. Agora usa apenas `structured_results` e `computed_payload`.

**2. `_wasi_candidate_has_stale_qi` (novo, linha 5117):** Detecta se um texto de interpretação contém valores de QI diferentes dos computados no `computed_payload`. Usa regex `/\b(\d{2,3})\b/` para encontrar números entre 60-160, compara com os valores reais dos composites.

**3. `_resolve_interpretation_text` candidates (linha 5157):** Reordenou candidatos para:
   - `clinical_interpretation` (primeiro, pode ser stale)
   - `_fallback_test_interpretation` (sempre consistente, usa computed_payload)
   - `summary`
   - `primary_section` / `fallback_section`

**4. `_fallback_test_interpretation` (linha 5238):** Adicionou handler específico para `instrument_code == "wasi"` que usa `build_wasi_interpretation` com dados de `computed_payload`.

**5. `_remove_empty_paragraphs` (linha 2432):** Adicionou `if cls._paragraph_contains_chart(paragraph): continue` — parágrafos que contêm charts embedding (vazios em texto mas com `<w:drawing>`) não eram mais removidos. Antes o `_remove_empty_paragraphs` destruía todos os charts.

**6. `@classmethod` duplicado (linhas 4246 e 4361):** Removida duplicação de `@classmethod` nos métodos `_populate_wasi_tables` e `_fmt_fdt_num`.

### Fluxo de Dados WASI

```
TestApplication.computed_payload
  └── composites{ qi_verbal{qi:115}, qi_execucao{qi:123}, qit_4{qi:122} }
  └── subtests{ vc, sm, cb, rm }
  └── age

TestApplication.classified_payload
  └── summary{ qi_verbal, qi_execucao, qit_4 }  ← só QI + classificação

build_validated_tests_snapshot
  └── structured_results = classified_payload (summary)
  └── classified_payload = classified_payload
  └── computed_payload = computed_payload

_report_export_service
  └── _wasi_payload() → merge structured_results + computed_payload → composites{subtests, etc}
  └── _wasi_chart_payload() → usa _wasi_payload().composites → gráfico correto
  └── _wasi_intro_text() → usa _wasi_payload() → QIT correto
  └── _wasi_global_bullet_parts() → usa _wasi_payload() → bullets corretos
  └── _resolve_interpretation_text() → pula candidatos stale → usa _fallback → consistente

_template WASI (Modelo-WASI.docx)
  └── 7 charts nativos (wasi, bpa2, ravlt, fdt_auto, fdt_control, etdah_ad, srs2)
  └── 7 tabelas (WASI verbal, WASI execução, BPA-2, RAVLT, FDT, E-TDAH-AD, SRS-2)
  └── Body text com placeholders
```

### Validação: `_validate_patient_identity` (linha 2526)
Após `_sanitize_generated_document`, roda `_validate_patient_identity` que verifica se há nomes de pacientes divergentes no texto. Se encontrar, lança `ValueError` e bloqueia a exportação.

## Session: Redesign Página 1 WAIS3 PDF

### O que foi feito
Substituiu toda a primeira página do relatório WAIS3 PDF por um novo layout moderno:
- **Hero** com gradiente azul-teal, brand Neuroavalia, título, badge WAIS-III e descrição
- **Card do paciente** com nome em destaque e grid de informações (sexo, idade, escolaridade, profissional, tabela normativa, código, aplicação)
- **Card de finalidade** com borda lateral teal
- **Footer** com marca N e nome Neuroavalia

### Arquivo
- `apps/tests/wais3/templates/layout_relatorio_wais_3.html` — replace do HTML da página 1 + remoção de CSS morto (`.patient-card-v3`, `.cover-hero`, etc.)

### Placeholders mantidos (compatíveis com `pdf_service.py:_render_html`)
- `Nome do Avaliado`, `Masculino`, `32 anos e 4 meses`, `Ensino superior completo`
- `Andre Alekhine`, `WAIS-III / Brasil / Faixa etária correspondente`, `AVL-102`, `13/05/2026`

## Session: Correção WAIS3 PDF — Zona de Média Removida do Gráfico QI

### Problema
No PDF do WAIS3, no gráfico "Perfil dos Quocientes Intelectuais e Índices Fatoriais", cada coluna parecia ter múltiplos itens marcados. Isso acontecia porque:

1. O SVG tinha um `<rect fill="#DDF6FA">` que criava uma zona destacada (escore 90–110) se estendendo por **todas as colunas**
2. Os rótulos numéricos dos marcadores estavam ocultos por CSS (`display: none`) conforme ajuste anterior
3. Sem rótulos, a zona de média + o marcador de escore criavam aparência de múltiplos itens por coluna

### Correção em `apps/tests/wais3/templates/layout_relatorio_wais_3.html`
- Removeu `<rect fill="#DDF6FA" height="65.4545..." width="372" x="44" y="183.27"/>`
- Após remoção, cada coluna tem apenas UM marcador (sombra + barra ciano)

### Key Files
- `apps/reports/services/report_export_service.py` — correções DOCX
- `apps/tests/wasi/interpreters.py` — `build_wasi_interpretation()` usa `merged_data.composites`
- `apps/tests/wasi/loaders.py` — lê tabela Excel (CORRECAO.xlsm) para normas
- `apps/tests/wasi/calculators.py` — `compute_wasi_payload()` populates `computed_payload`
- `apps/reports/builders/tests_builder.py` — `build_validated_tests_snapshot()` monta contexto
- `apps/tests/wais3/pdf_service.py` — serviço de geração de PDF WAIS3
- `apps/tests/wais3/templates/layout_relatorio_wais_3.html` — template HTML/PDF WAIS3 (redesign página 1 + correção zona de média)

## Session: Fix WISC4 Table Generation — `_rebuild_qualitative_section` Não Executava

### Root Cause
`_rebuild_qualitative_section` (`report_export_service.py:2752`) verificava `_find_paragraph(document, "Conclusão")`, mas `_replace_simple_sections` (executado antes, linha 420) renomeava o heading "Conclusão" → "14. CONCLUSÃO" (linha 2336). Isso fazia `_rebuild_qualitative_section` retornar early sem remover as tabelas nativas do template nem criar as tabelas WISC4 reconstruídas.

### Correção
**`_rebuild_qualitative_section` (linha 2756-2760):** Agora busca por `"Conclusão"` OU `"14. CONCLUSÃO"` como marcador de fim:
```python
conclusao = cls._find_paragraph(document, "Conclusão") or cls._find_paragraph(document, "14. CONCLUSÃO")
```

### Fixes Adicionais em Testes
- **`test_rebuild_qualitative_section_uses_wais3_skill_labels_for_late_chapters`**: Corrigidas asserções para usar acentos reais das descrições (é, presença, à investigação)
- **`test_replace_simple_sections_rebuilds_identification_chapter_with_fixed_labels`**: Corrigido para usar valores hardcoded de `FIXED_INTERESTED_PARTY` ("Familiares") e `FIXED_PURPOSE`

### Resultado
50/50 testes passando. Geração WISC4 DOCX verifica:
- Tabelas nativas do template (FDT, E-TDAH, SCARED, EPQ-J, SRS-2) corretamente removidas (4 tabelas no total)
- Larguras das tabelas WISC4 batem com `TABLE_LAYOUT_SPECS`:
  - `wisc` (Função Executiva): `[2028, 1525, 1366, 1492, 1400, 1523]`
  - `wisc_linguagem` (Linguagem): `[1736, 1632, 1464, 1594, 1499, 1409]`
  - `wisc_gnosias` (Gnosias): `[1980, 1579, 1415, 1546, 1451, 1363]`
  - `wisc` (Memória): `[2028, 1525, 1366, 1492, 1400, 1523]`