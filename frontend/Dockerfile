FROM node:20-alpine AS base

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install --legacy-peer-deps

COPY . .

# --- Development ---
FROM base AS development
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]

# --- Production ---
FROM base AS production
RUN npm run build
EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
