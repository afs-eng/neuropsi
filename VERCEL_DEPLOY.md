# Guia Oficial de Deploy na Vercel (Frontend Next.js)

Este documento detalha exatamente como configurar e hospedar o frontend do `NeuroAvalia` (`neuro-frontend`) na plataforma Vercel. 

> [!CAUTION]
> A Vercel hospedará **apenas o Frontend**. O servidor Django (Backend) deve estar no ar em outra plataforma (como Render ou Railway) antes de seguir este guia.

## 1. Importando o Projeto na Vercel

Para este projeto, manter o projeto existente e o domínio `neuropsi-eta.vercel.app`.
As instruções de importação abaixo são apenas para instalações novas.

1. Faça login em [Vercel.com](https://vercel.com) com sua conta do Github.
2. Clique em **"Add New..."** e selecione **"Project"**.
3. Encontre o repositório `neuro` (o repositório completo) e clique em **"Import"**.

## 2. Configurações Iniciais da Build

> [!IMPORTANT]
> A etapa a seguir é **CRÍTICA**. O Vercel assumirá que o código está na raiz se você não especificar o "Root Directory".

Na tela "Configure Project":

1. Expanda a seção **"Project Settings"** (ou "Build and Output Settings").
2. No item **"Root Directory"**, clique em *Edit* e escolha a pasta `neuro-frontend`.
3. Os campos de *Framework Preset* mudarão sozinhos para "Next.js". Não precisa alterar o *Build Command* nem *Output Directory*.
4. O `vercel.json` configura `npm ci` para instalação e `npm run build` para build.

## 3. Configurando Variáveis de Ambiente

> [!WARNING]
> As URLs públicas abaixo já estão configuradas no `vercel.json` para build e runtime.
> Conferir valores antigos no painel; não colocar chaves privadas no frontend.

Na mesma tela, expanda a aba **"Environment Variables"** e insira as seguintes chaves (uma por vez):

| Variable Name | Value a ser inserido | Descrição |
|:--------------|:---------------------|:----------|
| `NEXT_PUBLIC_API_BASE_URL` | `https://neuropsi-ddag.onrender.com` | URL raiz pública do backend no Render, sem `/api` no final |
| `INTERNAL_API_BASE_URL` | `https://neuropsi-ddag.onrender.com` | URL usada por rewrites/SSR da Vercel para alcançar o backend |
| `NEXT_PUBLIC_APP_URL` | `https://neuropsi-eta.vercel.app` | URL pública do frontend usada em links absolutos |

Não alterar o domínio atual. Mudanças em variáveis `NEXT_PUBLIC_*` exigem um novo build.

## 4. O Lado do Django (Backend / Render)

Depois do Vercel subir seu site em um domínio (exemplo: `https://meu-neuro-front.vercel.app`), o Django precisa permitir que esse domínio faça acesso cruzado (CORS).

No **Painel do Render** (onde o backend Django está hospedado):

1. Vá ao serviço do Backend.
2. Acesse **"Environment"**.
3. Encontre a variável `FRONTEND_BASE_URL` ou crie-a.
4. Coloque como valor exatamente o domínio da Vercel: `https://neuropsi-eta.vercel.app` (sem barra final e com HTTPS).
5. Se quiser aceitar previews de branch da Vercel, deixe `ALLOW_VERCEL_PREVIEWS=True` no backend.
6. Salve. O Render vai reiniciar a API.

## 5. Teste Prático

Após os deployments da Vercel e do Render terminarem:
1. Acesse sua URL da Vercel no navegador.
2. Você deve ver a tela de Login. 
3. Tente fazer o acesso. Se acessar a Dashboard com sucesso, o fluxo Next.js ⟷ Django CORS está rodando em perfeita harmonia!
