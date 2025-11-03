# OSRI指标计算系统 - 前端

## 安装依赖

```bash
npm install
```

## 开发运行

```bash
npm run serve
```

前端将运行在 http://localhost:8080

## 构建生产版本

```bash
npm run build
```

构建后的文件在 `dist/` 目录

## 部署说明

### 本地部署
前端运行在 8080 端口，后端API运行在 8010 端口。

### 内网服务器部署（10.3.35.21）

1. 构建项目：
```bash
npm run build
```

2. 将 `dist/` 目录上传到服务器

3. 使用 Nginx 或其他 Web 服务器部署：
   - 前端：10.3.35.21:8080（或使用80端口）
   - 后端API：10.3.35.21:8010

4. 确保后端API已正确配置，前端会自动根据主机名判断API地址

## 技术栈

- Vue 3
- Vue Router 4
- Element Plus
- Axios

