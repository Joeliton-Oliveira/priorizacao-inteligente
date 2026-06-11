FROM node:22-alpine

ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH

WORKDIR /app

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

EXPOSE 3000

CMD ["sh", "-c", "if [ ! -d node_modules/.pnpm ]; then pnpm install --frozen-lockfile; fi && rm -rf .next/* && pnpm exec next build && pnpm exec next start --hostname 0.0.0.0 --port 3000"]
