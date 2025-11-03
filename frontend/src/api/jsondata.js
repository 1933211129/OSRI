import request from './request'

// 列出所有jsondata文件
export function listJsonDataFiles() {
  return request({
    url: '/jsondata/files',
    method: 'get'
  })
}

// 读取jsondata文件
export function getJsonDataFile(filename) {
  return request({
    url: `/jsondata/${filename}`,
    method: 'get'
  })
}

// 更新jsondata文件
export function updateJsonDataFile(filename, data) {
  return request({
    url: `/jsondata/${filename}`,
    method: 'put',
    data: { data }
  })
}

// 添加数据（年份或国家）
export function addJsonDataData(filename, year, country, value) {
  return request({
    url: `/jsondata/${filename}/add`,
    method: 'post',
    data: {
      year,
      country,
      value
    }
  })
}

// 删除数据（年份或国家）
export function deleteJsonDataData(filename, year, country) {
  return request({
    url: `/jsondata/${filename}/delete`,
    method: 'delete',
    data: {
      year: year || null,
      country: country || null
    }
  })
}

// 从Excel导入数据
export function importExcelData(filename, file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: `/jsondata/${filename}/import-excel`,
    method: 'post',
    data: formData
  })
}

// 导出单个文件为Excel
export function exportJsonDataToExcel(filename) {
  return request({
    url: `/jsondata/${filename}/export-excel`,
    method: 'get',
    responseType: 'blob'
  })
}


