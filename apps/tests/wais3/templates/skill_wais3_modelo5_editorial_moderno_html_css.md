# Skill: WAIS-III Modelo 5 - Editorial Moderno em HTML/CSS para PDF

## 1. Objetivo da skill

Gerar um relatório técnico do **WAIS-III** em **HTML/CSS com saída em PDF A4**, mantendo o design do **Modelo 5 - Editorial Moderno** ajustado nas últimas versões. O modelo deve ser moderno, limpo, técnico e visualmente consistente, com foco em clareza psicométrica, legibilidade em PDF e padronização para uso em sistema.

A IA deve preservar os **tipos de dados do WAIS-III** e pode alterar apenas apresentação visual, espaçamentos, grids, cards e organização visual, sem remover campos técnicos obrigatórios do teste.

## 2. Configuração obrigatória de página

O relatório deve ser construído em páginas fixas A4, com controle de margem no próprio HTML.

### Medidas obrigatórias

- Tamanho da página: **A4 vertical**, 210 mm x 297 mm.
- Margem superior: **3 cm**.
- Margem esquerda: **2 cm**.
- Margem direita: **2 cm**.
- Margem inferior: **2 cm**.
- Rodapé deve respeitar margem inferior de **2 cm**.
- As páginas no modo visualização HTML não podem ficar grudadas. Devem ter separação visual entre uma página e outra.

### CSS base obrigatório

```css
@page {
  size: A4;
  margin: 0;
}

* {
  box-sizing: border-box;
}

html,
body {
  margin: 0;
  padding: 0;
  background: #eef4f7;
  font-family: Arial, Helvetica, sans-serif;
  color: #0f2538;
}

.page {
  width: 210mm;
  height: 297mm;
  position: relative;
  margin: 0 auto;
  background: #FFFFFF;
  padding: 30mm 20mm 34mm 20mm;
  overflow: hidden;
  break-after: page;
}

.page:last-child {
  break-after: auto;
}

@media screen {
  body {
    padding: 12mm 0;
  }

  .page {
    margin: 0 auto 14mm auto;
    box-shadow: 0 14px 42px rgba(18, 58, 90, 0.12);
  }

  .page:last-child {
    margin-bottom: 0;
  }
}

@media print {
  html,
  body {
    background: #FFFFFF;
  }

  .page {
    margin: 0 auto;
    box-shadow: none;
    break-after: page;
  }

  .page:last-child {
    break-after: auto;
  }
}
```

## 3. Paleta cromática obrigatória

Usar exclusivamente a paleta abaixo como base visual principal:

```css
:root {
  --azul-profundo: #123A5A;
  --petroleo: #1B7F8C;
  --ciano: #27BBD0;
  --cinza-azulado: #CBD6DE;
  --branco: #FFFFFF;

  --texto-principal: #0f2538;
  --texto-secundario: #587080;
  --fundo-suave: #F4F8FA;
  --fundo-card: #F7FAFC;
  --linha-suave: #C9D8E0;
  --linha-media: #9DB5C2;
  --linha-forte: #6F8FA0;
}
```

### Regras de cor

- Títulos principais: `#123A5A`.
- Destaques e linhas laterais dos cards: `#27BBD0`.
- Áreas escuras: gradiente entre `#123A5A` e `#1B7F8C`.
- Tabelas: cabeçalho em `#EAF4F7` ou `#123A5A`, conforme hierarquia.
- Grids técnicos devem ser mais visíveis que no modelo inicial, usando tons entre `#9DB5C2` e `#6F8FA0`.
- Evitar cinza muito claro em grades técnicas, pois fica apagado no PDF.

## 4. Logomarca

A logo deve ser incorporada como **SVG inline** no HTML, preferencialmente sem depender de arquivo externo.

### Regras de posicionamento

- Página 1: não usar logo no cabeçalho superior. A capa já pode conter a marca dentro do card principal.
- Páginas 2 a 5: usar a logo no cabeçalho, em tamanho maior.
- Rodapé: usar a logo no lado esquerdo, substituindo o texto “Neuroavalia”.
- Remover do rodapé qualquer texto “Modelo 5 - Editorial Moderno”.
- Manter apenas a numeração de página no canto inferior direito.

### CSS do cabeçalho e rodapé

```css
.page-header {
  position: absolute;
  top: 9mm;
  left: 20mm;
  right: 20mm;
  height: 21mm;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  border-bottom: 1.2px solid #CBD6DE;
  padding-bottom: 4mm;
}

.logo-small {
  display: none !important;
}

.logo-small svg {
  width: 64mm;
  height: auto;
  display: block;
}

.page:not(:first-child) .page-header .logo-small {
  display: block !important;
}

.page:first-child .page-header .logo-small {
  display: none !important;
}

.page-footer {
  position: absolute;
  left: 20mm;
  right: 20mm;
  bottom: 20mm;
  height: 8mm;
  display: flex;
  align-items: center;
  border-top: 1px solid #DDE7EC;
  padding-top: 2mm;
}

.footer-logo {
  display: flex;
  align-items: center;
  height: 8mm;
  min-width: 32mm;
}

.page-footer .footer-logo svg {
  width: 32mm;
  height: auto;
  display: block;
}

.footer-page-number {
  margin-left: auto;
  color: #6f8190;
  font-size: 8pt;
  font-weight: 600;
}
```

## 5. Estrutura geral do HTML

Cada página deve estar dentro de uma `section.page`. A estrutura mínima é:

```html
<body>
  <section class="page page-1">
    <header class="page-header"></header>
    <main class="page-content">...</main>
    <footer class="page-footer">...</footer>
  </section>

  <section class="page page-2">
    <header class="page-header">
      <div class="logo-small">SVG DA LOGO</div>
    </header>
    <main class="page-content">...</main>
    <footer class="page-footer">...</footer>
  </section>
</body>
```

## 6. Página 1: capa e dados do avaliado

### Elementos obrigatórios da página 1

1. Card principal “Avaliação Neuropsicológica”.
2. Título do instrumento: **Escala Wechsler de Inteligência para Adultos**.
3. O título do instrumento deve ficar em **uma única linha**. Reduzir fonte quando necessário.
4. Badge central ou pill com **WAIS-III** dentro do card principal.
5. Bloco **Dados do avaliado**.
6. Bloco **Finalidade do relatório técnico**.

### Elementos que não devem aparecer

- Não usar “Identificação e dados técnicos” no bloco de dados do avaliado.
- Não usar badge “WAIS-III” dentro do bloco de dados do avaliado.
- Não usar logo pequena no cabeçalho da página 1.

### Card principal da capa

O card principal deve ter a mesma largura dos blocos de dados e finalidade. Ele deve respeitar a largura útil da página, isto é, 170 mm, considerando margem esquerda e direita de 20 mm.

```css
.cover-hero {
  width: 100%;
  min-height: 86mm;
  border-radius: 7mm;
  padding: 12mm 10mm;
  background: linear-gradient(135deg, #123A5A 0%, #1B7F8C 72%, #27BBD0 130%);
  color: #FFFFFF;
  position: relative;
  overflow: hidden;
}

.cover-hero .eyebrow {
  font-size: 9pt;
  font-weight: 800;
  letter-spacing: 3.2px;
  text-transform: uppercase;
  margin-bottom: 6mm;
}

.cover-hero h1 {
  margin: 0;
  font-size: 25pt;
  line-height: 1.06;
  font-weight: 800;
  white-space: nowrap;
  letter-spacing: -0.8px;
}

.test-badge {
  width: 100%;
  height: 12mm;
  border-radius: 99px;
  margin: 7mm 0 6mm 0;
  background: #FFFFFF;
  color: #123A5A;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18pt;
  font-weight: 900;
  letter-spacing: 1px;
}

.cover-hero .lead {
  max-width: 142mm;
  font-size: 10.5pt;
  line-height: 1.45;
  color: rgba(255, 255, 255, 0.86);
  margin: 0;
}
```

### Dados do avaliado

O bloco deve ficar com a mesma largura do card principal e do card de finalidade. Usar card lateral escuro para identificação principal e cards claros à direita.

Campos obrigatórios:

- Nome.
- Sexo.
- Idade.
- Escolaridade.
- Profissional.
- Tabela normativa.
- Código do avaliado.
- Data da aplicação.

```css
.patient-panel {
  width: 100%;
  margin-top: 8mm;
  border: 1px solid #CBD6DE;
  border-radius: 6mm;
  overflow: hidden;
  display: grid;
  grid-template-columns: 58mm 1fr;
  background: linear-gradient(90deg, #F6FAFC 0%, #FFFFFF 100%);
}

.patient-card {
  background: linear-gradient(150deg, #123A5A 0%, #1B7F8C 100%);
  color: #FFFFFF;
  padding: 7mm;
  position: relative;
  overflow: hidden;
}

.patient-card::after {
  content: "";
  position: absolute;
  right: -18mm;
  bottom: -20mm;
  width: 44mm;
  height: 44mm;
  border-radius: 50%;
  background: rgba(39, 187, 208, 0.18);
}

.patient-card .label {
  font-size: 7pt;
  font-weight: 900;
  letter-spacing: 2px;
  text-transform: uppercase;
  margin-bottom: 4mm;
}

.patient-card .name {
  font-size: 14pt;
  line-height: 1.12;
  font-weight: 900;
  margin-bottom: 5mm;
}

.patient-meta-card {
  border: 1px solid rgba(255,255,255,.35);
  border-radius: 3mm;
  padding: 3mm;
  margin-top: 3mm;
  background: rgba(255,255,255,.12);
}

.patient-details {
  padding: 7mm 7mm 6mm 7mm;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 3mm;
  align-content: center;
}

.patient-details .field {
  border: 1px solid #CBD6DE;
  border-radius: 3mm;
  padding: 3.2mm 3.4mm;
  background: #F7FAFC;
  min-height: 14mm;
  box-shadow: 0 6px 14px rgba(18,58,90,.05);
}

.field .field-label {
  font-size: 6.5pt;
  letter-spacing: 2px;
  text-transform: uppercase;
  font-weight: 900;
  color: #1B7F8C;
  margin-bottom: 1.4mm;
}

.field .field-value {
  font-size: 9.2pt;
  line-height: 1.2;
  font-weight: 800;
  color: #123A5A;
}
```

### Finalidade do relatório técnico

```css
.purpose-card {
  width: 100%;
  margin-top: 6mm;
  border: 1px solid #CBD6DE;
  border-left: 1.2mm solid #27BBD0;
  border-radius: 0 4mm 4mm 0;
  background: #FFFFFF;
  overflow: hidden;
}

.purpose-card h2 {
  margin: 0;
  padding: 3mm 4mm;
  font-size: 12pt;
  color: #123A5A;
  border-bottom: 1px solid #DCE7ED;
}

.purpose-card p {
  margin: 0;
  padding: 4mm;
  font-size: 10pt;
  line-height: 1.48;
  text-align: justify;
}
```

## 7. Página 2: resultados, tabelas e gráficos

### Elementos obrigatórios da página 2

1. Título: **Resultados**.
2. Tabela **QI / Índices Fatoriais**.
3. Gráfico **Perfil dos Pontos Ponderados dos Subtestes**.
4. Gráfico **Perfil dos Quocientes Intelectuais e Índices Fatoriais**.
5. Tabela **Resumo Técnico dos Índices**.

### Elementos que não devem aparecer

- Não usar cards superiores com QIV, QIE, QIT, ICV, IOP, IMO, IVP.
- Não usar etiquetas pequenas como “TABELA TÉCNICA”.
- Não usar texto “faixa média 90-110”.
- Não usar seta/linha externa indicando faixa média.
- Não usar números acima dos marcadores dos gráficos.
- Não usar traços ou hífens em PS e AO quando não houver valor. Deixar célula vazia.

## 8. Cards técnicos da página 2

```css
.panel {
  border: 1px solid #CBD6DE;
  border-radius: 4mm;
  background: #FFFFFF;
  overflow: hidden;
  box-shadow: 0 8px 22px rgba(18,58,90,.06);
}

.panel-title {
  padding: 3mm 4mm;
  background: #123A5A;
  color: #FFFFFF;
  font-size: 10pt;
  font-weight: 900;
  line-height: 1.12;
}

.panel-body {
  padding: 4mm;
}
```

## 9. Tabela QI / Índices Fatoriais

A tabela deve ser compacta, técnica e com linhas nítidas.

```css
.data-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 7.5pt;
  color: #123A5A;
}

.data-table th {
  background: #E6F3F7;
  color: #123A5A;
  font-weight: 900;
  border: 1.1px solid #8FA9B8;
  padding: 2mm 1.5mm;
  text-align: center;
}

.data-table td {
  border: 1px solid #9DB5C2;
  padding: 1.8mm 1.4mm;
  text-align: center;
  vertical-align: middle;
}

.data-table td:first-child,
.data-table th:first-child {
  text-align: left;
  font-weight: 900;
}
```

## 10. Gráfico Perfil dos Pontos Ponderados dos Subtestes

Este gráfico deve seguir o modelo de grade do WAIS, com melhoria visual.

### Regras obrigatórias

- Escala Verbal e Escala de Execução lado a lado.
- Cabeçalho superior em azul/ciano.
- Subgrupos no topo:
  - Escala Verbal: CV e MO.
  - Escala de Execução: OP e VP.
- Subtestes visíveis:
  - Verbal: V, S, I, C, A, D, SNL.
  - Execução: AF, CF, CB, RM, CD, PS, AO.
- Valores de 1 a 19 devem aparecer apenas na lateral esquerda do conjunto, não no meio entre as duas escalas.
- Cada quadrado da grade deve ter largura e altura iguais.
- Os marcadores devem ficar centralizados no quadrado correspondente.
- O marcador deve ser **círculo**, um pouco menor, sem borda, sem brilho, sem número, com cor única.
- Cor do círculo: `#27BBD0`.
- Não colocar traço horizontal como marcador.
- Não colocar número acima do marcador.
- Não colocar hífens para valores ausentes.
- A grade não pode ficar apagada. Usar linhas reforçadas.

### CSS recomendado

```css
.wais-subtests-sheet {
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5mm;
}

.wais-scale {
  position: relative;
  border: 1.3px solid #6F8FA0;
  background: #FFFFFF;
}

.wais-scale-title {
  height: 7mm;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #27BBD0;
  color: #FFFFFF;
  font-size: 10pt;
  font-weight: 900;
  border-bottom: 1.3px solid #6F8FA0;
}

.wais-group-row {
  display: grid;
  height: 7mm;
  border-bottom: 1.2px solid #6F8FA0;
}

.wais-group-label {
  display: flex;
  align-items: center;
  justify-content: center;
  border-right: 1.2px solid #6F8FA0;
  font-size: 8.5pt;
  font-weight: 900;
  color: #526775;
}

.wais-subtest-row {
  display: grid;
  height: 6.5mm;
  border-bottom: 1.2px solid #6F8FA0;
}

.wais-sub-label {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 7.5pt;
  font-weight: 900;
  color: #123A5A;
  border-right: 1px solid #9DB5C2;
}

.wais-grid-wrap {
  position: relative;
  display: grid;
  grid-template-columns: 7mm 1fr;
}

.wais-y-axis {
  display: grid;
  grid-template-rows: repeat(19, 5.5mm);
  border-right: 1.3px solid #6F8FA0;
}

.wais-y-label {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 7pt;
  font-weight: 800;
  color: #425866;
  border-bottom: 1px solid #9DB5C2;
}

.wais-plot {
  position: relative;
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  grid-template-rows: repeat(19, 5.5mm);
  background-image:
    linear-gradient(to right, #9DB5C2 1px, transparent 1px),
    linear-gradient(to bottom, #9DB5C2 1px, transparent 1px);
  background-size: calc(100% / 7) 5.5mm;
  border-right: 1.3px solid #6F8FA0;
  border-bottom: 1.3px solid #6F8FA0;
}

.wais-plot::before {
  content: "";
  position: absolute;
  left: 0;
  right: 0;
  top: calc(5.5mm * 7);
  height: calc(5.5mm * 5);
  background: rgba(39, 187, 208, 0.12);
  pointer-events: none;
}

.wais-dot {
  position: absolute;
  width: 3.2mm;
  height: 3.2mm;
  border-radius: 50%;
  background: #27BBD0;
  border: none;
  box-shadow: none;
  transform: translate(-50%, -50%);
  z-index: 3;
}
```

### Fórmula de posicionamento dos círculos

Para cada subteste, calcular:

- `colIndex`: índice da coluna começando em 0.
- `score`: ponto ponderado entre 1 e 19.
- `x = ((colIndex + 0.5) / totalColunas) * 100`.
- `y = ((19 - score + 0.5) / 19) * 100`.

Exemplo:

```html
<span class="wais-dot" style="left: 7.14%; top: 18.42%;"></span>
```

## 11. Gráfico Perfil dos Quocientes Intelectuais e Índices Fatoriais

### Regras obrigatórias

- Categorias: QIV, QIE, QIT, ICV, IOP, IMO, IVP.
- Eixo vertical: 45 a 155.
- Grade com linhas horizontais e verticais reforçadas.
- Não usar número acima do marcador.
- Não usar texto “faixa média 90-110”.
- Não usar seta externa de faixa média.
- Pode manter uma faixa visual discreta entre 90 e 110, sem texto.
- Marcador deve ser discreto e limpo.

```css
.qi-sheet {
  position: relative;
  height: 92mm;
  border: 1.3px solid #6F8FA0;
  background: #FFFFFF;
  padding: 8mm 6mm 5mm 10mm;
}

.qi-plot {
  position: relative;
  height: 76mm;
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background-image:
    linear-gradient(to right, #9DB5C2 1px, transparent 1px),
    linear-gradient(to bottom, #9DB5C2 1px, transparent 1px);
  background-size: calc(100% / 7) calc(100% / 22);
}

.qi-average-band {
  position: absolute;
  left: 0;
  right: 0;
  top: 40.9%;
  height: 18.2%;
  background: rgba(39, 187, 208, 0.10);
  pointer-events: none;
}

.qi-marker {
  position: absolute;
  width: 6mm;
  height: 1.2mm;
  border-radius: 999px;
  background: #1B7F8C;
  border: none;
  box-shadow: none;
  transform: translate(-50%, -50%);
  z-index: 3;
}
```

## 12. Página 3: análise técnica

### Tabelas obrigatórias

1. Comparações entre as Discrepâncias.
2. Nível Subteste.
3. Análise de Clusters.
4. Comparações Clínicas.

### Regras visuais

- Usar painéis brancos com borda esquerda ciano ou cabeçalho azul profundo.
- Grades devem ser nítidas, porém menores que os gráficos da página 2.
- Fonte entre 6.4 pt e 7.2 pt, conforme quantidade de colunas.
- Cabeçalhos devem ter fundo `#E6F3F7` e texto `#123A5A`.
- Valores críticos ou alertas podem usar destaque pontual, mas sem excesso visual.

## 13. Página 4: interpretação clínica

### Regras obrigatórias

- Título: **Interpretação Clínica**.
- Remover os cards laterais:
  - Força relativa.
  - Maior cautela.
  - Perfil global.
- Usar bloco de texto principal em largura ampla.
- Manter nota técnica ao final.
- Texto justificado.
- Não usar travessão longo no corpo do laudo.

```css
.text-panel {
  border: 1px solid #CBD6DE;
  border-left: 1.2mm solid #27BBD0;
  border-radius: 0 4mm 4mm 0;
  background: #FFFFFF;
  padding: 5mm;
}

.text-panel h2 {
  margin: 0 0 4mm 0;
  color: #123A5A;
  font-size: 12pt;
  font-weight: 900;
}

.text-panel p {
  margin: 0 0 4mm 0;
  font-size: 10pt;
  line-height: 1.52;
  text-align: justify;
}
```

## 14. Página 5: síntese interpretativa

### Regras obrigatórias

- Título: **Síntese Interpretativa para o Laudo**.
- Manter bloco de síntese.
- Manter “Pontos de Atenção Clínica” se houver espaço.
- Remover o bloco final:
  - Profissional responsável.
  - Instrumento.
- Não finalizar com linhas de assinatura.
- Não usar “Modelo 5 - Editorial Moderno” no rodapé.

## 15. Dados esperados para popular o relatório

A IA deve receber ou montar um objeto de dados semelhante a este:

```js
const reportData = {
  paciente: {
    nome: "Asriel David´s Santana Alves",
    sexo: "Masculino",
    idade: "24 anos",
    escolaridade: "Superior Incompleto",
    profissional: "Andre Alekhine - CRP09/3820",
    tabelaNormativa: "WAIS-III / Brasil / 20 a 29 anos",
    codigo: "AVL-054",
    dataAplicacao: "19/05/2026"
  },
  indices: {
    QIV: { somaPP: 81, valor: 110, percentil: 75, ic95: "104-115" },
    QIE: { somaPP: 69, valor: 98, percentil: 45, ic95: "92-104" },
    QIT: { somaPP: 150, valor: 105, percentil: 63, ic95: "100-110" },
    ICV: { somaPP: 50, valor: 112, percentil: 79, ic95: "105-118" },
    IOP: { somaPP: 43, valor: 101, percentil: 53, ic95: "94-108" },
    IMO: { somaPP: 30, valor: 100, percentil: 50, ic95: "93-107" },
    IVP: { somaPP: 17, valor: 89, percentil: 23, ic95: "82-98" }
  },
  subtestes: {
    verbal: { V: 16, S: 13, I: 15, C: 16, A: 8, D: 10, SNL: 11 },
    execucao: { AF: 8, CF: 3, CB: 8, RM: 7, CD: 8, PS: null, AO: null }
  }
};
```

## 16. Regras para valores ausentes

- Valor ausente, nulo ou não aplicável deve renderizar célula vazia.
- Nunca usar hífen em PS e AO no gráfico de subtestes.
- Nunca renderizar círculos para valores ausentes.
- Em tabelas, usar vazio ou “Não aplicável” apenas quando clinicamente necessário. Para gráficos, deixar vazio.

## 17. Regras de tipografia

- Fonte principal do PDF: Arial, Helvetica, sans-serif.
- Títulos principais: 22 pt a 26 pt, peso 800 ou 900.
- Subtítulos de cards: 10 pt a 12 pt.
- Texto corrido: 10 pt, linha 1.45 a 1.55.
- Tabelas: 6.4 pt a 8 pt.
- Rótulos técnicos: uppercase, letter-spacing entre 1.5 e 2.5 px.
- Evitar fontes pequenas demais em tabelas críticas.

## 18. Hierarquia visual recomendada

1. Título da página.
2. Cards/painéis principais.
3. Tabelas técnicas.
4. Gráficos técnicos.
5. Nota técnica.
6. Rodapé discreto.

Nunca deixar componentes encostarem no rodapé. O conteúdo deve terminar acima da área do rodapé, respeitando a margem inferior.

## 19. Geração do PDF

Preferir geração por navegador headless, como Playwright/Chromium.

### Configuração recomendada

```js
await page.pdf({
  path: "wais3_modelo5_editorial.pdf",
  format: "A4",
  printBackground: true,
  margin: {
    top: "0mm",
    right: "0mm",
    bottom: "0mm",
    left: "0mm"
  }
});
```

As margens reais são controladas pela classe `.page`, não pelo motor de PDF. Isso evita deslocamentos e inconsistências entre páginas.

## 20. Checklist obrigatório de QA visual

Antes de entregar o HTML/PDF, verificar:

- A página tem tamanho A4 correto.
- Margem superior visual de 3 cm preservada.
- Margens esquerda e direita de 2 cm preservadas.
- Rodapé fica a 2 cm da borda inferior.
- As páginas no HTML não ficam grudadas.
- Página 1 não tem logo pequena no cabeçalho.
- Páginas 2 a 5 têm logo maior no cabeçalho.
- Rodapé usa logo no lado esquerdo.
- Rodapé não contém “Modelo 5 - Editorial Moderno”.
- Página 1 não contém “Identificação e dados técnicos”.
- Página 1 não contém badge “WAIS-III” dentro do bloco de dados do avaliado.
- Página 2 não contém cards superiores de QIV, QIE, QIT, ICV, IOP, IMO, IVP.
- Página 2 não contém etiquetas “TABELA TÉCNICA”.
- Página 2 não contém “faixa média 90-110”.
- Página 2 não contém seta externa da faixa média.
- Página 2 não contém números sobre marcadores.
- Subtestes ausentes não exibem hífen.
- Círculos dos subtestes são menores, cor única, sem borda e centralizados.
- Grids da página 2 estão visíveis e não apagados.
- Páginas 4 e 5 não contêm os blocos removidos.
- Conteúdo não invade o rodapé.

## 21. Erros que a IA deve evitar

- Gerar layout fluido sem páginas fixas A4.
- Usar margem do `@page` e também padding interno sem controle, causando margem dupla.
- Inserir elementos no rodapé fora da margem de 2 cm.
- Deixar as páginas coladas na visualização HTML.
- Usar grids claros demais nos gráficos técnicos.
- Usar marcadores com borda, brilho ou número.
- Recolocar textos removidos pelo usuário.
- Alterar os tipos de dados do WAIS-III.
- Trocar o gráfico de grade por gráfico de barras, pois o modelo final exige grade técnica.
- Usar o nome completo do modelo no rodapé.

## 22. Prompt-base para acionar esta skill

Use este prompt quando quiser que outra IA replique o modelo:

> Gere um relatório WAIS-III em HTML/CSS para PDF A4 no Modelo 5 - Editorial Moderno. Use margens de 3 cm superior, 2 cm esquerda, 2 cm direita e 2 cm inferior. Use a paleta #123A5A, #1B7F8C, #27BBD0, #CBD6DE e #FFFFFF. Na página 1, mantenha capa moderna, dados do avaliado e finalidade. Remova “Identificação e dados técnicos” e o badge WAIS-III dentro do bloco de dados. Nas páginas 2 a 5, coloque a logo maior no cabeçalho. No rodapé, use a logo à esquerda e número da página à direita, sem “Modelo 5 - Editorial Moderno”. Na página 2, não use cards superiores, não use etiquetas “TABELA TÉCNICA”, não use texto “faixa média 90-110”, não use seta externa e não use números nos marcadores. Os gráficos de subtestes devem seguir grade WAIS com quadrados iguais, círculos menores, centralizados, sem borda e com cor única. Reforce os grids dos gráficos e tabelas para não ficarem apagados. Preserve todos os tipos de dados do WAIS-III.

## 23. Resultado esperado

O resultado esperado é um relatório com aparência editorial moderna, institucional e técnica, mantendo estrutura psicométrica clara. O PDF deve parecer um relatório profissional de avaliação neuropsicológica, com gráficos legíveis, tabelas auditáveis, margens corretas, rodapé limpo e marca Neuroavalia aplicada de forma consistente.
