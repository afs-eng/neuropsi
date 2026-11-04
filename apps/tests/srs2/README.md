# Normas SRS-2

Os dez CSVs em `tabelas/` são exportados da aba oculta `SRS2-Normas`
de `aux/CORRECAO.xlsm`: pré-escolar, escolar masculino/feminino e adulto
autorrelato/heterorrelato. Cada modalidade possui subescalas e escalas DSM-5/total.

Para reproduzir a exportação, sem executar macros:

```bash
python3 apps/tests/srs2/import_norms.py aux/CORRECAO.xlsm
```

Os valores extremos percentílicos `0.9` e `99.1` da planilha são exportados
como `<1` e `>99`. Os sinais de limite existentes nos escores T são mantidos
nos CSVs; o carregador usa o valor numérico do limite, como já fazia para
percentis. O sistema consulta apenas pontos brutos presentes na tabela:
não interpola nem extrapola lacunas ou pontuações fora dos limites.

A aplicação usa os CSVs versionados; não depende do XLSM em produção.
Resultados já persistidos precisam ser recalculados após a implantação
para atualizar classificação, interpretação e relatórios derivados.
