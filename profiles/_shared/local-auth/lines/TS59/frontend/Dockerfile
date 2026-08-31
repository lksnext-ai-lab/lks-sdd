FROM node:24.19.0-bookworm-slim@sha256:3638d9a6fe4030bd716be989438248074489337ba3275657f93595428be4fc03
WORKDIR /app
COPY . .
RUN npm install --global npm@11.12.0 && npm ci --ignore-scripts
RUN npm run build
CMD ["npm", "run", "test"]
