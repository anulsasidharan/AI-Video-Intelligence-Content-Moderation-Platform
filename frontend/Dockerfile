# ---- deps ----
FROM node:20-alpine AS deps
WORKDIR /app
# libc6-compat: helps native deps (e.g. sharp) on Alpine/musl
RUN apk add --no-cache libc6-compat
COPY package.json package-lock.json ./
# npm ci installs exactly from the lockfile; there is no --frozen-lockfile flag for npm (unlike Yarn/pnpm).
RUN npm ci

# ---- builder ----
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ARG NEXT_PUBLIC_API_URL=""
ARG NEXT_PUBLIC_WS_URL=""
ARG NEXT_PUBLIC_APP_ENV=production
# Where Next.js rewrites /api/v1/* (server-side). Defaults to NEXT_PUBLIC_API_URL if unset.
ARG API_UPSTREAM_URL=""

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL
ENV NEXT_PUBLIC_APP_ENV=$NEXT_PUBLIC_APP_ENV
ENV API_UPSTREAM_URL=$API_UPSTREAM_URL
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# ---- runner ----
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000

CMD ["node", "server.js"]
