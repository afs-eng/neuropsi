# Modelos privados e planejamento de especialistas — primeira etapa

## API (Bearer obrigatório)

- `GET /api/report-templates/`: lista somente modelos do usuário autenticado.
- `POST /api/report-templates/`: JSON `{"name": "Infantil", "instrument_code": "wisc4"}`.
- `POST /api/report-templates/{id}/versions`: multipart, campo `file` com DOCX.
- `GET /api/report-templates/{id}/versions/{version_id}/download`: download privado original.
- `GET /api/reports/{id}/specialist-plan`: plano por aplicação validada do snapshot
  salvo, disponível somente ao autor do laudo. Não modifica o snapshot nem chama IA.

O proprietário nunca é aceito do cliente. A permissão de administrador não dá
acesso automático aos modelos privados de outros usuários nestas rotas.
Leitores não podem criar modelos ou enviar versões.

## Versões e arquivos

Cada envio acrescenta uma versão com checksum SHA-256. Não há endpoint de
sobrescrita. Os bytes ficam no banco, fora de `MEDIA_URL`; portanto integram os
backups do PostgreSQL. Para catálogos grandes, migrar para object storage privado
com as mesmas verificações de autorização, não para mídia pública.

Limites: 10 MB por envio, 50 MB descompactados, 2.000 entradas ZIP. DTDs, macros,
ActiveX e relacionamentos externos são recusados. Esta verificação estrutural
não é antivírus nem prova de fidelidade visual. Arquivos com links externos
(inclusive hyperlinks) precisam ter esses vínculos removidos antes do envio.

**Todos os envios permanecem rascunhos, sem exportação habilitada.** Ainda é
necessário mapear campos, respondentes, tabelas e gráficos, homologar o layout e
vincular uma versão homologada ao laudo. Não houve troca automática dos modelos
de exportação existentes. Cabeçalhos/rodapés e suas imagens continuam os atuais;
a identidade profissional no texto e assinatura usa o responsável da avaliação,
com fallback para o autor do laudo, sem inventar CRP ou especializações.

## Especialistas

O registro é declarativo, não uma certificação clínica. Gera uma entrada por
aplicação validada, não apenas por instrumento; instrumentos desconhecidos ficam
explicitamente sem suporte. A chave dos dados muda com paciente, avaliação,
aplicação ou resultados. Textos salvos e potencialmente antigos não são usados
como fonte dessa chave. Ainda não há cache nem invalidação automática em produção.

Antes da execução clínica: referências autorizadas, prompts específicos,
contratos de resposta com evidências, validação por instrumento, persistência de
execuções, fila/worker, integração clínica e aprovação humana por snapshot.
Nenhum provedor/modelo novo foi contratado ou ativado nesta etapa.

## Verificação e publicação

```bash
.venv/bin/python manage.py test apps.reports.test_private_templates apps.reports.tests apps.reports.test_wais3_docx_model
.venv/bin/python manage.py migrate
```

A migração `0005` cria apenas as tabelas novas. Não altera laudos anteriores.
Não há interface frontend nesta entrega. O isolamento destas rotas não substitui
uma revisão de autorização das demais APIs legadas de pacientes e laudos.
