FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN if [ -f package-lock.json ]; then npm ci; else npm install --no-audit --no-fund; fi

COPY . .

ARG VITE_DOCUMENT_PROCESSING_BASE_URL=http://localhost:8000
ARG VITE_BFF_BASE_URL=http://localhost:4000
ARG VITE_SOCKET_IO_NAMESPACE=/notifications

ENV VITE_DOCUMENT_PROCESSING_BASE_URL=$VITE_DOCUMENT_PROCESSING_BASE_URL
ENV VITE_BFF_BASE_URL=$VITE_BFF_BASE_URL
ENV VITE_SOCKET_IO_NAMESPACE=$VITE_SOCKET_IO_NAMESPACE

RUN npm run build

FROM nginx:1.27-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 3000

HEALTHCHECK --interval=10s --timeout=5s --retries=5 \
  CMD wget -qO- http://127.0.0.1:3000/health || exit 1
