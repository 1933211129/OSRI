const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    port: 8080,
    host: '0.0.0.0', // 允许内网访问
    proxy: {
      '/api': {
        target: 'http://localhost:8010',
        changeOrigin: true,
        ws: true
      }
    },
    client: {
      overlay: false, // 完全禁用 overlay，这是最彻底的方法
      webSocketTransport: 'ws',
    }
  },
  publicPath: process.env.NODE_ENV === 'production' ? './' : '/',
  outputDir: 'dist',
  assetsDir: 'static',
  // 忽略 ResizeObserver 相关的警告
  configureWebpack: {
    devtool: 'eval-source-map',
    resolve: {
      fallback: {
        // 如果使用某些 polyfills
      }
    }
  }
})

