# Multi-stage Dockerfile for Frontend
# 支持开发和生产环境

# Development stage - 开发环境，支持热重载
FROM node:20-alpine as development

WORKDIR /app

# 安装 pnpm 并配置国内镜像
RUN corepack enable && corepack prepare pnpm@latest --activate && \
    pnpm config set registry https://registry.npmmirror.com

# 复制 package 文件
COPY package.json pnpm-lock.yaml* ./

# 安装依赖
RUN pnpm install

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 5173

# 开发命令
CMD ["pnpm", "run", "dev", "--", "--host"]


# Build stage - 构建阶段
FROM node:20-alpine as build

WORKDIR /app

# 安装 pnpm 并配置国内镜像
RUN corepack enable && corepack prepare pnpm@latest --activate && \
    pnpm config set registry https://registry.npmmirror.com

# 复制 package 文件
COPY package.json pnpm-lock.yaml* ./

# 安装所有依赖（构建需要 devDependencies）
RUN pnpm install

# 复制应用代码
COPY . .

# 构建应用
RUN pnpm run build


# Production stage - 生产环境，使用 Nginx 提供静态文件服务
FROM nginx:alpine as production

# 安装 curl 用于健康检查
RUN apk add --no-cache curl

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

# 从构建阶段复制构建产物
COPY --from=build /app/dist /usr/share/nginx/html

# 创建日志目录
RUN mkdir -p /var/log/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /usr/share/nginx/html

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
