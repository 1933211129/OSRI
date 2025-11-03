import request from './request'

// 列出所有output文件
export function listOutputFiles() {
  return request({
    url: '/output/files',
    method: 'get'
  })
}

// 读取output文件
export function getOutputFile(filename) {
  return request({
    url: `/output/${filename}`,
    method: 'get'
  })
}

// 更新output文件
export function updateOutputFile(filename, data) {
  return request({
    url: `/output/${filename}`,
    method: 'put',
    data: { data }
  })
}

// 添加数据（年份或国家）
export function addOutputData(filename, year, country, value) {
  return request({
    url: `/output/${filename}/add`,
    method: 'post',
    data: {
      year,
      country,
      value
    }
  })
}

// 删除数据（年份或国家）
export function deleteOutputData(filename, year, country) {
  return request({
    url: `/output/${filename}/delete`,
    method: 'delete',
    data: {
      year: year || null,
      country: country || null
    }
  })
}

// 导出单个文件为Excel
export function exportOutputToExcel(filename) {
  return request({
    url: `/output/${filename}/export-excel`,
    method: 'get',
    responseType: 'blob'
  })
}


