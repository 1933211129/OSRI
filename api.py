"""
FastAPI后端接口
提供jsondata和output文件夹的JSON文件增删改查功能，以及批量计算接口
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import os
from pathlib import Path
import pandas as pd
from io import BytesIO
from fastapi.responses import StreamingResponse, FileResponse

# 导入计算模块
from calculate import batch_calculate_and_save, reload_data_cache

app = FastAPI(title="PDQ数据管理API", version="1.0.0")

# 配置CORS，允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据目录路径
JSONDATA_DIR = Path("jsondata")
OUTPUT_DIR = Path("output")

# 确保目录存在
JSONDATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


# ==================== 数据模型 ====================
class FileUpdateRequest(BaseModel):
    """文件更新请求模型"""
    data: Dict[str, Any]


class AddDataRequest(BaseModel):
    """添加数据请求模型"""
    year: Optional[str] = None  # 添加年份时使用
    country: Optional[str] = None  # 添加国家时使用
    value: Any  # 添加的值，可以是单个值或字典（取决于数据类型）


class DeleteDataRequest(BaseModel):
    """删除数据请求模型"""
    year: Optional[str] = None  # 删除年份
    country: Optional[str] = None  # 删除国家（从所有年份中删除）


class CalculateResponse(BaseModel):
    """计算响应模型"""
    status: str
    message: str


class ExcelImportResponse(BaseModel):
    """Excel导入响应模型"""
    status: str
    message: str
    added_years: List[str] = []
    added_countries: List[str] = []
    updated_cells: int = 0
    errors: List[str] = []


# ==================== 辅助函数 ====================
def read_json_file(file_path: Path) -> Dict[str, Any]:
    """读取JSON文件"""
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"文件不存在: {file_path.name}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"JSON格式错误: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取文件失败: {str(e)}")


def write_json_file(file_path: Path, data: Dict[str, Any]):
    """写入JSON文件，写入前创建备份"""
    try:
        # 先验证数据可以序列化
        try:
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
        except (TypeError, ValueError) as e:
            raise HTTPException(status_code=500, detail=f"数据无法序列化为JSON: {str(e)}")
        
        # 创建备份（只有在文件存在时才备份）
        backup_path = file_path.with_suffix('.json.bak')
        if file_path.exists():
            try:
                # 读取现有文件作为备份
                with open(file_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                # 写入备份
                with open(backup_path, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=2)
            except Exception as backup_error:
                print(f"警告: 创建备份失败: {backup_error}")
                # 备份失败不影响主流程，继续执行
        
        # 写入新文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
    except HTTPException:
        raise
    except Exception as e:
        # 如果写入失败，尝试从备份恢复
        backup_path = file_path.with_suffix('.json.bak')
        if backup_path.exists():
            try:
                print(f"错误: 写入文件失败，尝试从备份恢复: {str(e)}")
                with open(backup_path, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
                print(f"✓ 已从备份恢复 {file_path.name}")
            except Exception as restore_error:
                print(f"✗ 从备份恢复失败: {restore_error}")
        raise HTTPException(status_code=500, detail=f"写入文件失败: {str(e)}")


# ==================== jsondata API ====================
@app.get("/api/jsondata/files")
async def list_jsondata_files():
    """列出jsondata文件夹中的所有JSON文件"""
    files = []
    for file_path in JSONDATA_DIR.glob("*.json"):
        files.append({
            "filename": file_path.name,
            "size": file_path.stat().st_size,
            "modified": file_path.stat().st_mtime
        })
    return {"files": sorted(files, key=lambda x: x["filename"])}


@app.get("/api/jsondata/{filename}")
async def get_jsondata_file(filename: str):
    """读取jsondata文件夹中的JSON文件"""
    file_path = JSONDATA_DIR / filename
    if not filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="文件名必须以.json结尾")
    
    data = read_json_file(file_path)
    return {"filename": filename, "data": data}


@app.put("/api/jsondata/{filename}")
async def update_jsondata_file(filename: str, request: FileUpdateRequest):
    """更新jsondata文件夹中的JSON文件（完全覆盖）"""
    if not filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="文件名必须以.json结尾")
    
    file_path = JSONDATA_DIR / filename
    
    # 验证数据格式
    if not isinstance(request.data, dict):
        raise HTTPException(status_code=400, detail="数据必须是JSON对象")
    
    write_json_file(file_path, request.data)
    
    # 重新加载数据缓存，因为文件已被修改
    try:
        reload_data_cache()
    except Exception as e:
        # 如果重新加载失败，记录错误但不影响API响应
        print(f"警告: 重新加载数据缓存失败: {e}")
    
    return {"message": f"文件 {filename} 已更新", "filename": filename}


@app.post("/api/jsondata/{filename}/add")
async def add_jsondata_data(filename: str, request: AddDataRequest):
    """向jsondata文件中添加数据（添加年份或国家）"""
    if not filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="文件名必须以.json结尾")
    
    file_path = JSONDATA_DIR / filename
    data = read_json_file(file_path)
    
    if request.year:
        # 添加年份
        if request.year in data:
            raise HTTPException(status_code=400, detail=f"年份 {request.year} 已存在")
        data[request.year] = request.value
    elif request.country:
        # 添加国家（向所有年份添加该国家字段）
        if not data:
            raise HTTPException(status_code=400, detail="文件为空，无法添加国家")
        
        # 检查是否已存在该国家（至少在一个年份中）
        exists = any(request.country in year_data for year_data in data.values() if isinstance(year_data, dict))
        if exists:
            raise HTTPException(status_code=400, detail=f"国家 {request.country} 已存在")
        
        # 向所有年份添加该国家字段
        for year_key in data.keys():
            if isinstance(data[year_key], dict):
                data[year_key][request.country] = request.value
    else:
        raise HTTPException(status_code=400, detail="必须提供year或country参数")
    
    write_json_file(file_path, data)
    
    # 重新加载数据缓存
    try:
        reload_data_cache()
    except Exception as e:
        print(f"警告: 重新加载数据缓存失败: {e}")
    
    return {"message": "数据已添加", "filename": filename}


@app.delete("/api/jsondata/{filename}/delete")
async def delete_jsondata_data(filename: str, request: DeleteDataRequest):
    """从jsondata文件中删除数据（删除年份或国家）"""
    if not filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="文件名必须以.json结尾")
    
    file_path = JSONDATA_DIR / filename
    data = read_json_file(file_path)
    
    deleted = False
    
    if request.year:
        # 删除年份
        if request.year in data:
            del data[request.year]
            deleted = True
        else:
            raise HTTPException(status_code=404, detail=f"年份 {request.year} 不存在")
    elif request.country:
        # 删除国家（从所有年份中删除该国家字段）
        for year_key in data.keys():
            if isinstance(data[year_key], dict) and request.country in data[year_key]:
                del data[year_key][request.country]
                deleted = True
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"国家 {request.country} 不存在")
    else:
        raise HTTPException(status_code=400, detail="必须提供year或country参数")
    
    write_json_file(file_path, data)
    
    # 重新加载数据缓存
    try:
        reload_data_cache()
    except Exception as e:
        print(f"警告: 重新加载数据缓存失败: {e}")
    
    return {"message": "数据已删除", "filename": filename}


@app.post("/api/jsondata/{filename}/import-excel", response_model=ExcelImportResponse)
async def import_excel_data(filename: str, file: UploadFile = File(...)):
    """从Excel文件批量导入数据到jsondata文件"""
    try:
        if not filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="文件名必须以.json结尾")
        
        # 验证文件类型
        if not file.filename:
            raise HTTPException(status_code=400, detail="未提供文件名")
        
        if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
            raise HTTPException(status_code=400, detail="文件必须是Excel格式(.xlsx或.xls)")
        
        file_path = JSONDATA_DIR / filename
        
        # 读取现有数据（失败时从备份恢复）
        original_data = None
        try:
            data = read_json_file(file_path)
            # 保存原始数据的深拷贝作为备份
            import copy
            original_data = copy.deepcopy(data)
        except HTTPException as e:
            if e.status_code == 404:
                # 如果文件不存在，创建空数据
                data = {}
                original_data = {}
            else:
                raise
        
        # 读取Excel文件
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="上传的文件为空")
        
        # 尝试不同的引擎解析Excel
        df = None
        try:
            df = pd.read_excel(BytesIO(contents), engine='openpyxl')
        except Exception:
            try:
                df = pd.read_excel(BytesIO(contents), engine='xlrd')
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Excel文件解析失败: {str(e)}")
        
        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Excel文件为空或无法读取")
        
        # 验证Excel格式：第一列必须是年份列
        first_col = str(df.columns[0]).strip().lower()
        if first_col not in ['年份', 'year', '年']:
            raise HTTPException(
                status_code=400, 
                detail=f"Excel第一列必须是'年份'列，当前为: {df.columns[0]}"
            )
        
        # 统计信息
        added_years = []
        added_countries = []
        updated_cells = 0
        errors = []
        
        # 获取列名
        year_column = df.columns[0]
        country_columns = list(df.columns[1:])
        
        # 遍历Excel数据
        for index, row in df.iterrows():
            try:
                # 获取年份值
                year_value = row[year_column]
                if pd.isna(year_value):
                    errors.append(f"第{index+2}行: 年份为空，已跳过")
                    continue
                
                # 转换年份为字符串
                if isinstance(year_value, (int, float)):
                    year_str = str(int(year_value)) if year_value == int(year_value) else str(year_value)
                else:
                    year_str = str(year_value).strip()
                
                if not year_str:
                    errors.append(f"第{index+2}行: 年份无效，已跳过")
                    continue
                
                # 判断年份是否存在
                year_exists = year_str in data
                
                # 如果年份不存在，创建新年份
                if not year_exists:
                    data[year_str] = {}
                    added_years.append(year_str)
                
                # 遍历所有国家列
                for country_col in country_columns:
                    try:
                        country_name = str(country_col).strip()
                        cell_value = row[country_col]
                        
                        # 跳过空值
                        if pd.isna(cell_value):
                            continue
                        
                        # 处理数值：将numpy类型转换为Python原生类型
                        if isinstance(cell_value, str):
                            if cell_value.strip() == '':
                                continue
                            # 尝试转换为数字
                            try:
                                if '.' in cell_value:
                                    final_value = float(cell_value)
                                    if final_value == int(final_value):
                                        final_value = int(final_value)
                                else:
                                    final_value = int(cell_value)
                            except ValueError:
                                final_value = cell_value  # 保持原值
                        else:
                            # 处理numpy/int64/float64等类型
                            import numpy as np
                            if pd.isna(cell_value):
                                continue
                            # 转换为Python原生类型
                            if isinstance(cell_value, (np.integer, int)):
                                final_value = int(cell_value)
                            elif isinstance(cell_value, (np.floating, float)):
                                final_value = float(cell_value)
                                # 如果是整数形式的浮点数，转为整数
                                if final_value == int(final_value):
                                    final_value = int(final_value)
                            else:
                                # 其他类型，尝试转换
                                try:
                                    final_value = float(cell_value)
                                    if final_value == int(final_value):
                                        final_value = int(final_value)
                                except (ValueError, TypeError):
                                    final_value = str(cell_value)
                        
                        # 判断国家是否存在
                        country_exists_in_year = country_name in data[year_str]
                        
                        # 如果年份存在但国家不存在，新增国家列
                        if year_exists and not country_exists_in_year:
                            added_countries.append(country_name)
                        
                        # 更新或添加数据
                        data[year_str][country_name] = final_value
                        updated_cells += 1
                    except Exception as e:
                        errors.append(f"第{index+2}行, {country_name}列: 处理失败 ({str(e)})")
                        continue
            except Exception as e:
                errors.append(f"第{index+2}行: 处理失败 ({str(e)})")
                continue
        
        # 去重统计信息
        added_years = sorted(list(set(added_years)))
        added_countries = sorted(list(set(added_countries)))
        
        # 验证数据是否可以序列化为JSON（在保存前验证）
        try:
            import json
            # 尝试序列化，确保所有值都是JSON兼容的
            json.dumps(data, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            # 如果序列化失败，尝试修复数据
            print(f"警告: 数据序列化失败，尝试修复: {str(e)}")
            # 递归转换所有numpy类型
            def convert_to_native_types(obj):
                import numpy as np
                if isinstance(obj, dict):
                    return {k: convert_to_native_types(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_to_native_types(item) for item in obj]
                elif isinstance(obj, (np.integer, int)):
                    return int(obj)
                elif isinstance(obj, (np.floating, float)):
                    val = float(obj)
                    return int(val) if val == int(val) else val
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif pd.isna(obj):
                    return None
                else:
                    return obj
            
            data = convert_to_native_types(data)
            
            # 再次验证
            try:
                json.dumps(data, ensure_ascii=False)
            except (TypeError, ValueError) as e2:
                raise HTTPException(status_code=500, detail=f"数据格式错误，无法保存: {str(e2)}")
        
        # 保存文件（只有在验证通过后才保存）
        write_json_file(file_path, data)
        
        # 重新加载数据缓存
        try:
            reload_data_cache()
        except Exception as e:
            print(f"警告: 重新加载数据缓存失败: {e}")
        
        # 构建返回消息
        message_parts = []
        if added_years:
            message_parts.append(f"新增{len(added_years)}个年份: {', '.join(added_years[:5])}")
            if len(added_years) > 5:
                message_parts[-1] += f" 等共{len(added_years)}个"
        if added_countries:
            message_parts.append(f"新增{len(added_countries)}个国家: {', '.join(added_countries[:5])}")
            if len(added_countries) > 5:
                message_parts[-1] += f" 等共{len(added_countries)}个"
        if updated_cells > 0:
            message_parts.append(f"更新{updated_cells}个数据单元格")
        if errors:
            message_parts.append(f"遇到{len(errors)}个错误")
        
        message = "；".join(message_parts) if message_parts else "导入完成，无数据更新"
        
        return ExcelImportResponse(
            status="success",
            message=message,
            added_years=added_years,
            added_countries=added_countries,
            updated_cells=updated_cells,
            errors=errors[:20]  # 最多返回20个错误
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Excel导入错误: {error_detail}")
        
        # 如果导入失败，尝试恢复原始数据
        if original_data is not None and file_path.exists():
            try:
                print(f"尝试恢复原始数据...")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(original_data, f, ensure_ascii=False, indent=2)
                print(f"✓ 已恢复原始数据到 {file_path.name}")
            except Exception as restore_error:
                print(f"✗ 恢复原始数据失败: {restore_error}")
                # 尝试从备份恢复
                backup_path = file_path.with_suffix('.json.bak')
                if backup_path.exists():
                    try:
                        with open(backup_path, 'r', encoding='utf-8') as f:
                            backup_data = json.load(f)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            json.dump(backup_data, f, ensure_ascii=False, indent=2)
                        print(f"✓ 已从备份恢复 {file_path.name}")
                    except Exception as backup_restore_error:
                        print(f"✗ 从备份恢复也失败: {backup_restore_error}")
        
        raise HTTPException(status_code=500, detail=f"导入过程发生错误: {str(e)}")


# ==================== output API ====================
@app.get("/api/output/files")
async def list_output_files():
    """列出output文件夹中的所有JSON文件"""
    files = []
    for file_path in OUTPUT_DIR.glob("*.json"):
        files.append({
            "filename": file_path.name,
            "size": file_path.stat().st_size,
            "modified": file_path.stat().st_mtime
        })
    return {"files": sorted(files, key=lambda x: x["filename"])}


@app.get("/api/output/{filename}")
async def get_output_file(filename: str):
    """读取output文件夹中的JSON文件"""
    file_path = OUTPUT_DIR / filename
    if not filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="文件名必须以.json结尾")
    
    data = read_json_file(file_path)
    return {"filename": filename, "data": data}


@app.put("/api/output/{filename}")
async def update_output_file(filename: str, request: FileUpdateRequest):
    """更新output文件夹中的JSON文件（完全覆盖）"""
    if not filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="文件名必须以.json结尾")
    
    file_path = OUTPUT_DIR / filename
    
    # 验证数据格式
    if not isinstance(request.data, dict):
        raise HTTPException(status_code=400, detail="数据必须是JSON对象")
    
    write_json_file(file_path, request.data)
    
    return {"message": f"文件 {filename} 已更新", "filename": filename}


@app.post("/api/output/{filename}/add")
async def add_output_data(filename: str, request: AddDataRequest):
    """向output文件中添加数据（添加年份或国家）"""
    if not filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="文件名必须以.json结尾")
    
    file_path = OUTPUT_DIR / filename
    data = read_json_file(file_path)
    
    # 处理单值函数（如r_open_t1.json格式为{"value": 0.4036}）
    if "value" in data and len(data) == 1:
        raise HTTPException(status_code=400, detail="单值函数不支持添加数据")
    
    if request.year:
        # 添加年份
        if request.year in data:
            raise HTTPException(status_code=400, detail=f"年份 {request.year} 已存在")
        data[request.year] = request.value
    elif request.country:
        # 添加国家（向所有年份添加该国家字段）
        if not data:
            raise HTTPException(status_code=400, detail="文件为空，无法添加国家")
        
        # 检查是否已存在该国家（至少在一个年份中）
        exists = any(request.country in year_data for year_data in data.values() if isinstance(year_data, dict))
        if exists:
            raise HTTPException(status_code=400, detail=f"国家 {request.country} 已存在")
        
        # 向所有年份添加该国家字段
        for year_key in data.keys():
            if isinstance(data[year_key], dict):
                data[year_key][request.country] = request.value
    else:
        raise HTTPException(status_code=400, detail="必须提供year或country参数")
    
    write_json_file(file_path, data)
    return {"message": "数据已添加", "filename": filename}


@app.delete("/api/output/{filename}/delete")
async def delete_output_data(filename: str, request: DeleteDataRequest):
    """从output文件中删除数据（删除年份或国家）"""
    if not filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="文件名必须以.json结尾")
    
    file_path = OUTPUT_DIR / filename
    data = read_json_file(file_path)
    
    # 处理单值函数
    if "value" in data and len(data) == 1:
        raise HTTPException(status_code=400, detail="单值函数不支持删除数据")
    
    deleted = False
    
    if request.year:
        # 删除年份
        if request.year in data:
            del data[request.year]
            deleted = True
        else:
            raise HTTPException(status_code=404, detail=f"年份 {request.year} 不存在")
    elif request.country:
        # 删除国家（从所有年份中删除该国家字段）
        for year_key in data.keys():
            if isinstance(data[year_key], dict) and request.country in data[year_key]:
                del data[year_key][request.country]
                deleted = True
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"国家 {request.country} 不存在")
    else:
        raise HTTPException(status_code=400, detail="必须提供year或country参数")
    
    write_json_file(file_path, data)
    return {"message": "数据已删除", "filename": filename}


# ==================== 计算API ====================
@app.post("/api/calculate/batch", response_model=CalculateResponse)
async def execute_batch_calculate(background_tasks: BackgroundTasks):
    """执行批量计算"""
    try:
        # 在后台任务中执行计算，避免阻塞
        background_tasks.add_task(batch_calculate_and_save)
        
        return CalculateResponse(
            status="started",
            message="批量计算已开始，正在后台执行"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动计算失败: {str(e)}")


@app.get("/api/calculate/status")
async def get_calculate_status():
    """获取计算状态（简单版本，实际可以使用更复杂的状态管理）"""
    # 这里可以扩展为更复杂的状态管理，比如使用Redis或数据库
    # 目前返回简单的状态信息
    return {
        "status": "unknown",
        "message": "如需准确状态，请检查output文件夹的文件修改时间"
    }


# ==================== 导出Excel功能 ====================
@app.get("/api/jsondata/{filename}/export-excel")
async def export_jsondata_to_excel(filename: str):
    """导出单个jsondata文件为Excel"""
    try:
        if not filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="文件名必须以.json结尾")
        
        file_path = JSONDATA_DIR / filename
        
        # 读取JSON数据
        try:
            data = read_json_file(file_path)
        except HTTPException as e:
            if e.status_code == 404:
                raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
            raise
        
        # 转换为DataFrame
        if not data or len(data) == 0:
            raise HTTPException(status_code=400, detail="文件数据为空")
        
        # 检查是否是单值文件
        if 'value' in data and len(data) == 1:
            # 单值文件，创建一个简单的表格
            df = pd.DataFrame([{'函数名': filename.replace('.json', ''), '值': data['value']}])
        else:
            # 多值文件，转换为DataFrame
            # 收集所有年份和所有国家
            years = sorted(data.keys())
            all_countries = set()
            for year_data in data.values():
                if isinstance(year_data, dict):
                    all_countries.update(year_data.keys())
            
            all_countries = sorted(list(all_countries))
            
            # 构建DataFrame
            rows = []
            for year in years:
                row = {'年份': year}
                if isinstance(data[year], dict):
                    for country in all_countries:
                        row[country] = data[year].get(country, None)
                rows.append(row)
            
            df = pd.DataFrame(rows)
        
        # 创建Excel文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='数据')
        
        output.seek(0)
        
        # 返回文件流
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename.replace('.json', '')}.xlsx"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"导出Excel错误: {error_detail}")
        raise HTTPException(status_code=500, detail=f"导出Excel失败: {str(e)}")


@app.get("/api/output/{filename}/export-excel")
async def export_output_to_excel(filename: str):
    """导出单个output文件为Excel"""
    try:
        if not filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="文件名必须以.json结尾")
        
        file_path = OUTPUT_DIR / filename
        
        # 读取JSON数据
        try:
            data = read_json_file(file_path)
        except HTTPException as e:
            if e.status_code == 404:
                raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")
            raise
        
        # 转换为DataFrame
        if not data or len(data) == 0:
            raise HTTPException(status_code=400, detail="文件数据为空")
        
        # 检查是否是单值文件
        if 'value' in data and len(data) == 1:
            # 单值文件
            df = pd.DataFrame([{'函数名': filename.replace('.json', ''), '值': data['value']}])
        else:
            # 多值文件
            years = sorted(data.keys())
            all_countries = set()
            for year_data in data.values():
                if isinstance(year_data, dict):
                    all_countries.update(year_data.keys())
            
            all_countries = sorted(list(all_countries))
            
            rows = []
            for year in years:
                row = {'年份': year}
                if isinstance(data[year], dict):
                    for country in all_countries:
                        row[country] = data[year].get(country, None)
                rows.append(row)
            
            df = pd.DataFrame(rows)
        
        # 创建Excel文件
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='数据')
        
        output.seek(0)
        
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename={filename.replace('.json', '')}.xlsx"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"导出Excel错误: {error_detail}")
        raise HTTPException(status_code=500, detail=f"导出Excel失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)

