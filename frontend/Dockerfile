# ---------- Stage 1: build do Vue ----------
FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --no-audit --no-fund

COPY . .

# Variáveis do Vite são embutidas no build (não funcionam em runtime)
ARG VITE_API_URL=
ARG VITE_APP_NAME=Dekto
ARG VITE_ROOT_DOMAIN=dekto.com
ARG VITE_TERMS_URL=
ARG VITE_PRIVACY_URL=
ENV VITE_API_URL=$VITE_API_URL \
    VITE_APP_NAME=$VITE_APP_NAME \
    VITE_ROOT_DOMAIN=$VITE_ROOT_DOMAIN \
    VITE_TERMS_URL=$VITE_TERMS_URL \
    VITE_PRIVACY_URL=$VITE_PRIVACY_URL

RUN npm run build

# ---------- Stage 2: nginx ----------
FROM nginx:1.27-alpine

# O entrypoint oficial do nginx gera /etc/nginx/conf.d/default.conf a partir do template
ENV BACKEND_UPSTREAM=backend:8000 \
    SERVER_NAME=_

RUN rm -f /etc/nginx/conf.d/default.conf
COPY templates/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q --spider http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
