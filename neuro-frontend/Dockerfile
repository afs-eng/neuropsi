# ============================================================
# NeuroAvalia — Frontend Dockerfile (Multi-stage: dev + prod)
# ============================================================

FROM node:20-bookworm-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
  ca-certificates \
  libasound2 \
  libatk-bridge2.0-0 \
  libatk1.0-0 \
  libc6 \
  libcairo2 \
  libcups2 \
  libdbus-1-3 \
  libdrm2 \
  libexpat1 \
  libgbm1 \
  libglib2.0-0 \
  libgtk-3-0 \
  libnspr4 \
  libnss3 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libstdc++6 \
  libx11-6 \
  libx11-xcb1 \
  libxcb1 \
  libxcomposite1 \
  libxdamage1 \
  libxext6 \
  libxfixes3 \
  libxkbcommon0 \
  libxrandr2 \
  xdg-utils \
  && rm -rf /var/lib/apt/lists/*
WORKDIR /app

# --------------------------------------------------------
# Stage 1: Dev (hot-reload)
# --------------------------------------------------------
FROM base AS dev

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

EXPOSE 3000
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["npm", "run", "dev"]

# --------------------------------------------------------
# Stage 2: Deps (instalacao de dependencias)
# --------------------------------------------------------
FROM base AS deps

COPY package.json package-lock.json* ./
RUN \
  if [ -f package-lock.json ]; then npm ci; \
  else npm install; \
  fi

# --------------------------------------------------------
# Stage 3: Builder (build de producao)
# --------------------------------------------------------
FROM base AS builder

WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL
ENV BUILD_STANDALONE=true

RUN npm run build

# --------------------------------------------------------
# Stage 4: Prod (standalone otimizado)
# --------------------------------------------------------
FROM base AS prod

WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]