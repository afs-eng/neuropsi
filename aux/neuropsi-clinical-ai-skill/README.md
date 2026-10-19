# GoPsi Clinical AI Quality Skill

Skill para agentes de programação que trabalham no GoPsi.

## Instalação sugerida
Copie `SKILL.md` para `.agents/skills/gopsi-clinical-ai-quality/SKILL.md` na raiz do repositório, caso seu agente reconheça esse padrão. Ajuste o diretório conforme a documentação do agente utilizado.

## Comando inicial para o agente
> Use a skill `gopsi-clinical-ai-quality`. Execute somente a Fase 0 no repositório atual. Identifique arquivos, contratos, testes e riscos reais; entregue o diagnóstico e o plano de implementação sem alterar código.

A skill é uma especificação para execução por agente, não uma alteração já aplicada ao GoPsi.

## Escopo e adoção

- Instalar a skill e executar suas fases são ações separadas. Revisar este documento não instala nem modifica o sistema.
- A Fase 0 entrega diagnóstico, testes seguros de referência e plano com riscos/rollback; o agente deve parar para aprovação antes de alterar código do sistema.
- Reutilizar fila, contratos, evidências e revisão existentes. O isolamento atual é por proprietário da conta, sem presumir clínicas/equipes.
- Priorizar consolidação do BPA-2, regras clínicas contextualizadas e avaliação profissional com casos sintéticos. Métricas/heartbeat, outros instrumentos e integração ao laudo são entregas posteriores com escopo próprio.
- Não aumentar limites, baixar/trocar modelos, ativar provedores pagos, tracing, serviços ou inferências reais sem autorização específica. Testes de referência devem usar dados sintéticos e transporte mockado/offline.

## Critérios essenciais

- Validade técnica não significa homologação clínica nem aprovação para um paciente.
- Erros críticos impedem homologação independentemente da nota ponderada. Os 20–30 casos iniciais não constituem validação científica geral.
- Trechos clínicos pertencem ao ambiente clínico autenticado, quando sua retenção estiver autorizada, nunca a logs operacionais ou telemetria.
- Recuperar um job abandonado não autoriza repetir a inferência; tentativas novas precisam de política e auditoria explícitas.
- No futuro caminho de integração, somente a versão com aprovação profissional atual pode ser incorporada ao laudo/DOCX, sem sobrescrever edição humana silenciosamente.
