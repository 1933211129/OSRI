<template>
  <div id="app">
    <div class="app-container">
      <!-- 顶部导航栏 -->
      <header class="main-header">
        <div class="header-wrapper">
          <div class="logo-section">
            <div class="logo-icon">
              <el-icon :size="32"><DataAnalysis /></el-icon>
            </div>
            <div class="logo-text">
              <h1 class="app-title">OSRI指标计算平台</h1>
              <p class="app-subtitle">Open Science Research Index Calculation System</p>
            </div>
          </div>
          
          <nav class="main-nav">
            <div class="nav-buttons">
              <router-link 
                to="/jsondata" 
                class="nav-button"
                :class="{ 'is-active': activeMenu === '/jsondata' || activeMenu.startsWith('/jsondata') }"
              >
                <el-icon><FolderOpened /></el-icon>
                <span>数据管理</span>
              </router-link>
              <router-link 
                to="/output" 
                class="nav-button"
                :class="{ 'is-active': activeMenu === '/output' || activeMenu.startsWith('/output') }"
              >
                <el-icon><TrendCharts /></el-icon>
                <span>计算结果</span>
              </router-link>
            </div>
          </nav>
          
          <div class="header-actions">
            <el-button 
              type="primary"
              size="large"
              :loading="calculating"
              @click="handleCalculate"
              class="calculate-btn"
            >
              <template #icon>
                <el-icon v-if="!calculating"><RefreshRight /></el-icon>
              </template>
              {{ calculating ? '计算中...' : '重新计算' }}
            </el-button>
          </div>
        </div>
      </header>

      <!-- 主内容区 -->
      <main class="main-content">
        <div class="content-wrapper">
          <router-view v-slot="{ Component }">
            <transition name="fade-slide" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>
      </main>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { DataAnalysis, FolderOpened, TrendCharts, RefreshRight } from '@element-plus/icons-vue'
import { executeBatchCalculate } from './api/calculate'

export default {
  name: 'App',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const calculating = ref(false)

    const activeMenu = computed(() => route.path)

    const handleCalculate = async () => {
      calculating.value = true
      try {
        await executeBatchCalculate()
        ElMessage.success({
          message: '批量计算已开始，请稍候刷新结果',
          type: 'success',
          duration: 3000
        })
        setTimeout(() => {
          router.go(0)
        }, 2000)
      } catch (error) {
        ElMessage.error({
          message: '计算启动失败: ' + (error.message || '未知错误'),
          duration: 3000
        })
      } finally {
        calculating.value = false
      }
    }

    return {
      calculating,
      activeMenu,
      handleCalculate,
      DataAnalysis,
      FolderOpened,
      TrendCharts,
      RefreshRight
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB',
    'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  background-attachment: fixed;
}

.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* 顶部导航栏 */
.main-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
  border-bottom: 1px solid rgba(255, 255, 255, 0.18);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.header-wrapper {
  max-width: 1600px;
  margin: 0 auto;
  padding: 0 40px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 80px;
  gap: 40px;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.logo-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.logo-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.app-title {
  font-size: 24px;
  font-weight: 700;
  color: #1a202c;
  margin: 0;
  line-height: 1.2;
}

.app-subtitle {
  font-size: 12px;
  color: #718096;
  margin: 0;
  font-weight: 400;
  letter-spacing: 0.5px;
}

.main-nav {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}

.nav-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.nav-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  color: #4a5568;
  text-decoration: none;
  border-radius: 10px;
  transition: all 0.3s ease;
  background: transparent;
  border: none;
  cursor: pointer;
}

.nav-button:hover {
  background: rgba(102, 126, 234, 0.08);
  color: #667eea;
}

.nav-button.is-active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.nav-button.is-active:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.nav-button .el-icon {
  font-size: 18px;
}

.header-actions {
  flex-shrink: 0;
}

.calculate-btn {
  height: 44px;
  padding: 0 28px;
  font-size: 15px;
  font-weight: 600;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
  transition: all 0.3s ease;
}

.calculate-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

/* 主内容区 */
.main-content {
  flex: 1;
  padding: 40px;
  display: flex;
  justify-content: center;
}

.content-wrapper {
  width: 100%;
  max-width: 1600px;
}

/* 页面过渡动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .header-wrapper {
    padding: 0 24px;
  }
  
  .main-content {
    padding: 24px;
  }
}

@media (max-width: 768px) {
  .header-wrapper {
    flex-wrap: wrap;
    height: auto;
    padding: 16px;
  }
  
  .logo-section {
    width: 100%;
  }
  
  .main-nav {
    width: 100%;
    margin-top: 16px;
  }
  
  .nav-buttons {
    width: 100%;
    justify-content: center;
  }
  
  .nav-button {
    flex: 1;
    justify-content: center;
    max-width: 200px;
  }
  
  .header-actions {
    width: 100%;
    margin-top: 16px;
  }
  
  .calculate-btn {
    width: 100%;
  }
}
</style>

