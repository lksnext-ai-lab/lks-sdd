FROM node:24.19.0-bookworm-slim@sha256:3638d9a6fe4030bd716be989438248074489337ba3275657f93595428be4fc03
WORKDIR /app
COPY . .
RUN npm install --global pnpm@10.34.5 && pnpm install --frozen-lockfile --ignore-scripts
RUN pnpm run build
CMD ["pnpm", "run", "test"]
