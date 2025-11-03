import request from './request'

// 执行批量计算
export function executeBatchCalculate() {
  return request({
    url: '/calculate/batch',
    method: 'post'
  })
}

// 获取计算状态
export function getCalculateStatus() {
  return request({
    url: '/calculate/status',
    method: 'get'
  })
}

