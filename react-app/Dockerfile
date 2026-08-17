# Stage 1: Build React App
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json ./
RUN npm install --no-package-lock
COPY . .
ENV CI=false
ENV DISABLE_ESLINT_PLUGIN=true
ENV GENERATE_SOURCEMAP=false
RUN npm run build

# Stage 2: Serve Production Build
FROM node:20-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/build ./build
EXPOSE 3000
CMD ["serve", "-s", "build", "-l", "3000"]
