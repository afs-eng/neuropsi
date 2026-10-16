# Fidelidade do DOCX WISC-IV

- [x] Comparar o modelo e o laudo fornecido: cabeçalhos, imagens, margens, tabelas e gráficos.
- [x] Preencher o documento original sem reconstruir tabelas nem aplicar estilos genéricos.
- [x] Manter SCARED e EPQ-J como gráficos nativos, vinculados a resultados reais.
- [x] Preservar os arquivos de cabeçalho/rodapé e remover dados de exemplo não utilizados.
- [x] Validar propriedades visuais OOXML, dados e regressões; executar graphify update.

Sem Word/LibreOffice neste ambiente: a validação visual renderizada deve ser
distinguida da comparação estrutural OOXML.

103 testes passaram (exportação geral e modelo WAIS-III). Novos testes comparam
tblPr/tblGrid/trPr/tcPr/pPr com o modelo, cabeçalhos/rodapés/imagens byte a byte,
estilos, geometria dos desenhos, cores/linhas/marcadores dos gráficos e dados
atuais nos gráficos e tabelas. SCARED somente Mãe não conserva dados do Autorrelato.
Ruff sem novos alertas. Nenhum deploy foi realizado.
