import axios from 'axios'
import { ElMessage } from 'element-plus'

// 根据环境自动判断API地址
const getApiBaseURL = () => {
  // 开发环境：使用代理
  if (process.env.NODE_ENV === 'development') {
    return '/api'
  }
  // 生产环境：根据当前主机名判断
  const hostname = window.location.hostname
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8010/api'
  } else {
    // 内网服务器
    return 'http://10.3.35.21:8010/api'
  }
}

const service = axios.create({
  baseURL: getApiBaseURL(),
  timeout: 60000, // 文件上传需要更长时间
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 如果是 FormData，不设置 Content-Type，让浏览器自动设置（包括 boundary）
    if (config.data instanceof FormData) {
      // 不设置 Content-Type，让 axios/browser 自动处理
    } else if (!config.headers['Content-Type']) {
      // 其他请求默认使用 JSON
      config.headers['Content-Type'] = 'application/json'
    }
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    // 如果是blob类型（文件下载），直接返回response
    if (response.config.responseType === 'blob' || response.data instanceof Blob) {
      return response
    }
    return response.data
  },
  error => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

export default service

