# OSRI指标计算系统

一个用于计算和管理 OSRI（Open Science Research Index）指标的全栈 Web 应用系统。系统提供数据管理、指标计算等功能。</br>
项目演示视频：https://meeting.tencent.com/crm/2Y7jqgo3d3
## 📋 目录

- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [API 文档](#api-文档)
- [使用说明](#使用说明)
- [数据格式](#数据格式)
- [计算指标说明](#计算指标说明)
- [注意事项](#注意事项)

## ✨ 功能特性

### 数据管理

- **JSON 数据文件管理**：通过 Web 界面直接查看、编辑、添加、删除数据
- **Excel 导入导出**：支持从 Excel 文件导入数据到 JSON，或将 JSON 导出为 Excel
- **数据一致性检查**：自动检测不同数据文件之间的年份和国家一致性
- **实时数据备份**：每次修改自动创建 `.bak` 备份文件，防止数据丢失

### 指标计算

- **批量计算**：一键计算所有年份（1996-2024）和所有国家的指标值
- **缓存机制**：智能缓存计算结果，大幅提升计算性能（从20秒降至毫秒级）
- **中间结果保存**：所有中间计算步骤的结果自动保存为 JSON 文件，便于分析和调试

### 前端界面

- **现代化 UI**：采用玻璃态设计和渐变背景
- **固定列表格**：年份列固定，支持水平滚动查看所有国家数据
- **响应式设计**：适配不同屏幕尺寸
- **实时编辑**：表格单元格直接编辑，即时保存

## 🛠 技术栈

### 后端

- **Python 3.10+**
- **FastAPI**：现代化的 Python Web 框架，提供 RESTful API
- **pandas**：数据处理和分析
- **openpyxl / xlrd**：Excel 文件读写支持

### 前端

- **Vue 3**：渐进式 JavaScript 框架
- **Vue Router**：单页面应用路由管理
- **Element Plus**：基于 Vue 3 的组件库
- **Axios**：HTTP 客户端，用于 API 请求
- **Vue CLI**：项目脚手架和构建工具

### 数据存储

- **JSON 文件**：轻量级数据存储，适合小型应用
- **文件备份**：自动 `.bak` 备份机制

## 📁 项目结构

```
root_dir/
├── api.py                 # FastAPI 后端主文件
├── calculate.py           # 指标计算核心逻辑
├── preset.json            # 前端预设配置
├── jsondata/              # 原始数据目录
│   ├── total.json         # 总发文量数据
│   ├── OA.json           # 开放获取论文数据
│   ├── cooperation.json  # 合作发文数据
│   ├── FWCI.json         # 领域加权引用影响指数
│   ├── retraction.json   # 撤稿数据
│   ├── scientist.json   # 科学家数据
│   ├── world_total.json # 全球总量数据
│   ├── weight.json       # 权重配置
│   └── ...               # 其他数据文件
├── output/               # 计算结果输出目录
│   ├── R.json           # 最终指标 R
│   ├── R_oa.json        # R_oa 指标
│   ├── R_od.json        # R_od 指标
│   ├── R_open.json      # R_open 指标
│   └── ...              # 其他中间计算结果
├── excel/                # Excel 原始数据（可选）
└── frontend/             # 前端项目目录
    ├── src/
    │   ├── api/          # API 请求封装
    │   ├── views/        # 页面组件
    │   ├── router/       # 路由配置
    │   └── App.vue       # 根组件
    ├── public/           # 静态资源
    └── package.json      # 前端依赖配置
```

## 🚀 快速开始

### 环境要求

- **Python 3.10+**
- **Node.js v24.9.0**（推荐使用 nvm 管理版本）
- **npm** 或 **yarn**

### 后端部署

1. **安装 Python 依赖**

```bash
# 使用 conda 环境（推荐）
conda activate env

pip install fastapi uvicorn pandas openpyxl xlrd
```

2. **启动后端服务**

```bash
# 方式一：使用 uvicorn
uvicorn api:app --host 0.0.0.0 --port 8010 --reload

# 方式二：直接运行
python api.py
```

后端服务将在 `http://localhost:8010` 启动。

### 前端部署

1. **安装依赖**

```bash
cd frontend
npm install
```

2. **启动开发服务器**

```bash
npm run serve
```

前端应用将在 `http://localhost:8080` 启动。

3. **生产构建**

```bash
npm run build
```

构建产物将输出到 `frontend/dist/` 目录。

### 服务器部署

#### 后端（生产环境）

```bash
# 使用 gunicorn（推荐）
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api:app --bind 0.0.0.0:8010

# 或使用 systemd 服务（参考配置）
# /etc/systemd/system/osri-api.service
```

#### 前端（Nginx）

1. 构建前端项目：`npm run build`
2. 配置 Nginx（参考 `frontend/nginx.conf.example`）
3. 部署到服务器：`10.3.35.21:8080`

## 📚 API 文档

### 数据管理 API

#### 1. 获取文件列表

```
GET /api/jsondata/files
GET /api/output/files
```

#### 2. 读取文件内容

```
GET /api/jsondata/{filename}
GET /api/output/{filename}
```

#### 3. 更新文件内容

```
PUT /api/jsondata/{filename}
Body: { "data": {...} }
```

#### 4. 添加数据

```
POST /api/jsondata/{filename}/add
Body: { "year": "2024", "country": "China", "value": 1000 }
```

#### 5. 删除数据

```
DELETE /api/jsondata/{filename}/year/{year}
DELETE /api/jsondata/{filename}/country/{country}
```

#### 6. Excel 导入

```
POST /api/jsondata/{filename}/import-excel
Content-Type: multipart/form-data
Body: file (Excel 文件)
```

#### 7. Excel 导出

```
GET /api/jsondata/{filename}/export-excel
GET /api/output/{filename}/export-excel
```

### 计算 API

#### 触发批量计算

```
POST /api/calculate/batch
```

该接口将在后台执行批量计算，计算所有指标的所有年份和国家组合。

## 📖 使用说明

### 数据管理页面

1. **查看数据**

   - 在左侧文件列表中点击文件名，切换到对应的数据表
   - 表格支持水平滚动查看所有国家列
   - 年份列固定在左侧，方便对照
2. **编辑数据**

   - 点击任意单元格进入编辑模式
   - 修改后点击"保存"按钮或按 `Enter` 键保存
   - 修改会自动备份，失败时可从备份恢复
3. **添加年份**

   - 点击"添加年份"按钮
   - 输入年份，系统会自动复制上一个年份的数据作为初始值
   - 确认后保存
4. **添加国家**

   - 点击"添加国家"按钮
   - 输入国家名称和初始值
   - 确认后会在所有年份中添加该国家列
5. **删除年份/国家**

   - 点击对应行的"删除"按钮
   - 确认后删除（删除国家会从所有年份中删除该列）
6. **Excel 导入**

   - 点击"导入Excel"按钮
   - 选择 Excel 文件（支持 `.xlsx` 和 `.xls` 格式）
   - 系统会自动合并数据（更新已存在的，添加新的年份和国家）
   - 查看导入结果摘要
7. **Excel 导出**

   - 点击"导出Excel"按钮，导出当前显示的文件
8. **数据一致性检查**

   - 系统自动检查所有数据文件的年份和国家是否一致
   - 如有不一致，头部会显示警告图标
   - 点击警告图标可查看详细信息

### 计算结果页面

1. **查看计算结果**

   - 左侧显示所有计算结果文件列表
   - 点击文件名查看对应的计算结果表
   - 支持查看中间计算步骤的结果
2. **编辑结果**

   - 部分结果支持手动编辑（如单值结果）
   - 修改后需要保存
3. **重新计算**

   - 在数据管理页面修改数据后，点击顶部导航栏的"重新计算"按钮
   - 系统会执行批量计算，更新所有结果文件
   - 计算完成后自动刷新结果页面

## 📊 数据格式

### JSON 数据格式

所有数据文件采用以下格式：

```json
{
  "1996": {
    "China": 1000,
    "USA": 2000,
    "EU27": 1500
  },
  "1997": {
    "China": 1200,
    "USA": 2100,
    "EU27": 1600
  }
}
```

- **键名**：年份（字符串）
- **值**：对象，键为国家/地区名，值为对应数据

### Excel 导入格式

Excel 文件第一列必须是年份列，列名可以是：

- `年份`
- `year`
- `年`

第一行是表头，后续行为数据：

- 第一列：年份
- 其他列：各个国家/地区的数据

## 🧮 计算指标说明

系统计算以下主要指标：

### 开放获取相关指标（OA）

- **r_open_t(year, country)**: 该年该国家的 OA/total 比例
- **r_open_t1()**: 历年各国 OA/total 比例平均值的最大值
- **P_open_t(year)**: 该年所有国家 OA 数量的平均值
- **P_open_t1()**: 历年各国 OA 数量均值的最大值
- **R_open(year, country)**: 综合开放获取指标

### 包容性相关指标（Inclusive）

- **r_incl_t(year, country)**: 该年该国家的包容性指标
- **r_incl_t1()**: 历年各国包容性指标平均值的最大值
- **P_incl_t(year)**: 该年所有国家包容性指标的平均值
- **P_incl_t1()**: 历年各国包容性指标均值的最大值
- **R_incl(year, country)**: 综合包容性指标

### 整体指标（Overall）

- **R_oa(year, country)**: 开放获取综合指标（基于 R_open 和 R_incl）
- **R_oa_bar(year, country)**: R_oa 的标准化值

### 多样性相关指标（OD - Open Diversity）

- **f1(year, country)**: 多样性因子 1
- **f2(year, country)**: 多样性因子 2
- **f3(year, country)**: 多样性因子 3
- **S_od_t(year, country)**: 多样性综合指标 S
- **A_od_t(year, country)**: 多样性综合指标 A
- **R_od(year, country)**: 多样性综合指标 R
- **R_od_bar(year, country)**: R_od 的标准化值

### 最终指标

- **R(year, country)**: 最终综合指标，加权组合 R_oa_bar、R_od_bar 和 R_op_bar

计算公式：

```
R = W_OA × R_oa_bar + W_OD × R_od_bar + W_OP × R_op_bar
```

权重配置在 `jsondata/weight.json` 文件中。

## ⚠️ 注意事项

### 数据管理

1. **备份机制**：系统会在修改文件前自动创建 `.bak` 备份文件
2. **数据一致性**：修改数据后建议检查数据一致性警告
3. **年份格式**：年份在 JSON 中为字符串格式（如 `"1996"`），但在计算函数中使用整数
4. **NULL 值处理**：数据中的 `null` 值在计算中会被正确处理

### 计算性能

1. **首次计算**：首次批量计算可能需要较长时间（取决于数据量）
2. **缓存机制**：计算结果会自动缓存，后续调用几乎瞬时完成
3. **数据更新**：修改 `jsondata` 中的数据后，需要调用 `reload_data_cache()` 刷新缓存
4. **重新计算**：添加新年份或新国家后，必须重新执行批量计算

### 文件操作

1. **文件锁定**：避免在计算过程中修改数据文件
2. **Excel 导入**：导入时会自动转换 numpy 类型为 Python 原生类型
3. **错误恢复**：如果文件损坏，系统会自动尝试从 `.bak` 备份恢复

### 开发调试

1. **日志查看**：后端日志输出到控制台
2. **前端调试**：使用浏览器开发者工具查看网络请求和错误
3. **数据验证**：建议在修改数据后验证计算结果

## 🔧 故障排查

### 后端无法启动

- 检查端口 8010 是否被占用
- 确认 Python 环境和依赖已正确安装
- 检查 `jsondata` 和 `output` 目录是否存在

### 前端无法连接后端

- 确认后端服务已启动
- 检查 `frontend/src/api/request.js` 中的 baseURL 配置
- 检查 CORS 配置是否允许前端域名

### 计算结果异常

- 检查 `jsondata` 中的数据是否完整
- 确认数据格式正确（年份为字符串，国家名称一致）
- 查看控制台错误信息，定位具体计算函数

### Excel 导入失败

- 确认 Excel 文件格式正确（第一列为年份）
- 检查文件编码是否为 UTF-8
- 查看后端日志获取详细错误信息

## 📝 更新日志

### v1.0.0

- 初始版本发布
- 实现数据管理功能
- 实现指标计算功能
- 实现 Excel 导入导出
- 实现前端界面

## 📄 许可证

本项目为内部使用项目。

## 👥 维护者

如有问题或建议，请联系项目维护团队。
