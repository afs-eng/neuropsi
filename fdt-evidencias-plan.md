# FDT — referências de evidência inválidas no Ollama

Relato: execução #21 falhou com `evidence_not_found`. Não repetir nem alterar esse
registro. A resposta rejeitada não é persistida, portanto não sabemos qual ID foi
usado nessa execução; reproduzir o mecanismo com referências sintéticas inválidas.

- [x] Reproduzir: FDT não enumera IDs no schema nem permite corrigir evidências dentro da execução.
- [x] Adicionar guia dos caminhos reais, schema restrito e uma correção dentro das duas chamadas existentes.
- [x] Versionar somente FDT para nova solicitação explícita, preservando resultados e revisões anteriores.
- [x] Validar falha terminal segura, schema ignorado, regressões e nenhum acesso à produção/inferência real.

Não afrouxar `validate_evidence`, converter IDs, descartar citações, inventar fatos,
aumentar orçamento ou garantir sucesso clínico com base em testes simulados.

## Evidências

- Dois testes de reprodução falhavam antes da correção; log sintético em
  `/tmp/opencode/fdt-grounding-before.log`.
- O motor real com entradas sintéticas também revelou um falso negativo numérico:
  tempo `30.0` rejeitado quando a prosa usava `30`. Equivalência decimal corrigida
  somente no FDT, com testes que continuam rejeitando sinais/valores diferentes.
- 13 testes novos e 354 testes de laudos aprovados; SQLite em memória, sockets
  bloqueados, **zero tentativas de rede**. Log: `/tmp/opencode/fdt-all-reports.log`.
- Ruff e Bandit aprovados; MyPy do módulo novo com imports externos ignorados.
- `git diff --check` aprovado; `graphify update .` bloqueado por CLI indisponível,
  sem substituir o grafo existente.
- Publicação de backend/worker e avaliação autorizada com modelo real continuam
  pendentes. Não acessar/reativar #21 nem prometer sucesso real por testes simulados.
