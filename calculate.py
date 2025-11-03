# 计算具体指标的函数
import json
import os
import math
from functools import lru_cache

# 读取所有json文件存储到字典中
json_files = {
    "alpha_F": "jsondata/alpha_F.json",
    "cooperation": "jsondata/cooperation.json",
    "OA": "jsondata/OA.json",
    "alpha_I": "jsondata/alpha_I.json",
    "F2": "jsondata/F2.json",
    "OP": "jsondata/OP.json",
    "alpha_L": "jsondata/alpha_L.json",
    "FWCI": "jsondata/FWCI.json",
    "retraction": "jsondata/retraction.json",
    "scientist": "jsondata/scientist.json",
    "total": "jsondata/total.json",
    "world_total": "jsondata/world_total.json",
    "weight": "jsondata/weight.json",
    "F3": "jsondata/F3.json"
}

# ==================== 数据预加载和缓存 ====================
# 预加载所有JSON文件到内存
_data_cache = {}

# 缓存计算结果
_cache = {
    'constants': {},  # 单值函数的结果
    'functions': {}    # 多参数函数的结果
}

def reload_data_cache():
    """重新加载所有JSON文件到内存（当文件被修改后调用）"""
    global _data_cache, _cache
    _data_cache = {}
    for key, path in json_files.items():
        try:
            if not os.path.exists(path):
                print(f"警告: 文件不存在，跳过: {path}")
                _data_cache[key] = {}
                continue
            # 尝试读取文件
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    _data_cache[key] = json.load(f)
            except json.JSONDecodeError as e:
                # JSON格式错误，尝试从备份恢复
                backup_path = path + '.bak'
                if os.path.exists(backup_path):
                    print(f"警告: {path} JSON格式错误，尝试从备份恢复...")
                    try:
                        with open(backup_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        _data_cache[key] = data
                        # 尝试修复原文件
                        try:
                            with open(path, 'w', encoding='utf-8') as wf:
                                json.dump(data, wf, ensure_ascii=False, indent=2)
                            print(f"      ✓ 已从备份恢复并修复文件: {path}")
                        except:
                            print(f"      已从备份恢复数据，但无法修复文件")
                    except Exception as restore_error:
                        print(f"      ✗ 从备份恢复失败: {str(restore_error)}")
                        _data_cache[key] = {}
                else:
                    print(f"错误: JSON文件格式错误且无备份 {path}: {str(e)}")
                    _data_cache[key] = {}
        except Exception as e:
            print(f"错误: 读取文件失败 {path}: {str(e)}")
            _data_cache[key] = {}
    # 清空计算结果缓存，因为数据已更新
    _cache = {
        'constants': {},
        'functions': {}
    }

# 初始加载
reload_data_cache()

# 输出文件夹
_output_dir = "output"
os.makedirs(_output_dir, exist_ok=True)

def save_to_json(func_name, data):
    """保存计算结果到JSON文件"""
    output_path = os.path.join(_output_dir, f"{func_name}.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==================== 辅助函数 ====================
def get_cache_key(func_name, *args):
    """生成缓存key"""
    if args:
        return f"{func_name}_{args[0]}_{args[1]}"
    return func_name

def get_from_cache(func_name, *args):
    """从缓存获取值"""
    key = get_cache_key(func_name, *args)
    if args:
        year_str = str(args[0])
        country = args[1]
        if func_name in _cache['functions']:
            if year_str in _cache['functions'][func_name]:
                if country in _cache['functions'][func_name][year_str]:
                    return _cache['functions'][func_name][year_str][country]
    else:
        if func_name in _cache['constants']:
            return _cache['constants'][func_name]
    return None

def set_cache(func_name, value, *args):
    """设置缓存值"""
    if args:
        year_str = str(args[0])
        country = args[1]
        if func_name not in _cache['functions']:
            _cache['functions'][func_name] = {}
        if year_str not in _cache['functions'][func_name]:
            _cache['functions'][func_name][year_str] = {}
        _cache['functions'][func_name][year_str][country] = value
    else:
        _cache['constants'][func_name] = value

# ==================== 基础函数 ====================
# 计算R_op_bar的函数
def R_op_bar(year, country):
    '''
    输入year和地区，计算该年该地区的OP指标。
    公式：各国该年固定值/ max(该年所有国家中的最大值)
    '''
    # 检查缓存
    cached = get_from_cache('R_op_bar', year, country)
    if cached is not None:
        return cached
    
    year_str = str(year)
    data = _data_cache['OP']
    result = data[year_str][country] / max(data[year_str].values())
    
    set_cache('R_op_bar', result, year, country)
    return result

# 2
def r_open_t1():
    '''计算r_open_t1'''
    if 'r_open_t1' in _cache['constants']:
        return _cache['constants']['r_open_t1']
    
    data_oa = _data_cache['OA']
    data_total = _data_cache['total']
    
    years = sorted([int(y) for y in data_oa.keys()])
    year_avg_ratios = []
    
    for year in years:
        year_str = str(year)
        oa_values = data_oa[year_str]
        total_values = data_total[year_str]
        
        country_ratios = []
        for country in oa_values.keys():
            if country in total_values:
                oa_val = oa_values[country]
                total_val = total_values[country]
                if oa_val is not None and total_val is not None and total_val > 0:
                    ratio = oa_val / total_val
                    country_ratios.append(ratio)
        
        if country_ratios:
            avg_ratio = sum(country_ratios) / len(country_ratios)
            year_avg_ratios.append((year, avg_ratio))
    
    if not year_avg_ratios:
        result = None
    else:
        result = max(year_avg_ratios, key=lambda x: x[1])[1]
    
    _cache['constants']['r_open_t1'] = result
    save_to_json('r_open_t1', {"value": result})
    return result

# 3
def r_open_t(year, country):
    '''公式：该年该国家的OA/该年该国家的total'''
    cached = get_from_cache('r_open_t', year, country)
    if cached is not None:
        return cached
    
    data_oa = _data_cache['OA']
    data_total = _data_cache['total']
    year_str = str(year)

    if year_str not in data_oa or year_str not in data_total:
        result = None
    elif country not in data_oa[year_str] or country not in data_total[year_str]:
        result = None
    else:
        oa_val = data_oa[year_str][country]
        total_val = data_total[year_str][country]
        
        if oa_val is None or total_val is None or total_val == 0:
            result = None
        else:
            result = oa_val / total_val
    
    set_cache('r_open_t', result, year, country)
    return result

# 4
def P_open_t1():
    '''计算P_open_t1'''
    if 'P_open_t1' in _cache['constants']:
        return _cache['constants']['P_open_t1']
    
    data_oa = _data_cache['OA']
    years = sorted([int(y) for y in data_oa.keys()])
    year_avg_ratios = []
    
    for year in years:
        year_str = str(year)
        oa_values = data_oa[year_str]
        
        oa_sum = sum(v for v in oa_values.values() if v is not None)
        country_count = sum(1 for v in oa_values.values() if v is not None)
        
        if country_count > 0:
            avg_per_region = oa_sum / country_count
            year_avg_ratios.append(avg_per_region)
    
    result = max(year_avg_ratios) if year_avg_ratios else None
    
    _cache['constants']['P_open_t1'] = result
    save_to_json('P_open_t1', {"value": result})
    return result

# 5
def P_open_t(year, country):
    '''计算P_open_t'''
    cached = get_from_cache('P_open_t', year, country)
    if cached is not None:
        return cached
    
    year_str = str(year)
    data_oa = _data_cache['OA']
    result = data_oa[year_str][country]
    
    set_cache('P_open_t', result, year, country)
    return result

# 计算R_open的函数
def R_open(year, country):
    '''计算R_open'''
    cached = get_from_cache('R_open', year, country)
    if cached is not None:
        return cached
    
    r_open_t_value = r_open_t(year, country)
    p_open_t_value = P_open_t(year, country)
    r_open_t1_value = r_open_t1()
    p_open_t1_value = P_open_t1()
    
    if r_open_t_value is None or p_open_t_value is None or r_open_t1_value is None or p_open_t1_value is None:
        result = None
    else:
        valueac = r_open_t_value / r_open_t1_value
        valuebd = p_open_t_value / p_open_t1_value
        result = 0.5 * (valueac + valuebd)
    
    set_cache('R_open', result, year, country)
    return result

# 6
def r_incl_t(year, country):
    '''计算r_incl_t'''
    cached = get_from_cache('r_incl_t', year, country)
    if cached is not None:
        return cached
    
    year_str = str(year)
    data_cooperation = _data_cache['cooperation']
    data_total = _data_cache['total']
    result = data_cooperation[year_str][country] / data_total[year_str][country]
    
    set_cache('r_incl_t', result, year, country)
    return result

# 7
def r_incl_t1():
    '''计算r_incl_t1'''
    if 'r_incl_t1' in _cache['constants']:
        return _cache['constants']['r_incl_t1']
    
    data_cooperation = _data_cache['cooperation']
    data_total = _data_cache['total']
    
    years = sorted([int(y) for y in data_cooperation.keys()])
    year_avg_ratios = []
    
    for year in years:
        year_str = str(year)
        
        if year_str not in data_cooperation or year_str not in data_total:
            continue
        
        cooperation_values = data_cooperation[year_str]
        total_values = data_total[year_str]
        
        country_r_incl_values = []
        for country in cooperation_values.keys():
            if country in total_values:
                cooperation_val = cooperation_values[country]
                total_val = total_values[country]
                
                if cooperation_val is not None and total_val is not None and total_val > 0:
                    r_incl_value = cooperation_val / total_val
                    country_r_incl_values.append(r_incl_value)
        
        if country_r_incl_values:
            avg_ratio = sum(country_r_incl_values) / len(country_r_incl_values)
            year_avg_ratios.append(avg_ratio)
    
    result = max(year_avg_ratios) if year_avg_ratios else None
    
    _cache['constants']['r_incl_t1'] = result
    save_to_json('r_incl_t1', {"value": result})
    return result

# 8
def P_incl_t(year, country):
    '''计算P_incl_t'''
    cached = get_from_cache('P_incl_t', year, country)
    if cached is not None:
        return cached
    
    year_str = str(year)
    data_cooperation = _data_cache['cooperation']
    result = data_cooperation[year_str][country]
    
    set_cache('P_incl_t', result, year, country)
    return result

# 9
def P_incl_t1():
    '''计算P_incl_t1'''
    if 'P_incl_t1' in _cache['constants']:
        return _cache['constants']['P_incl_t1']
    
    data_cooperation = _data_cache['cooperation']
    years = sorted([int(y) for y in data_cooperation.keys()])
    year_avg_values = []
    
    for year in years:
        year_str = str(year)
        
        if year_str not in data_cooperation:
            continue
        
        cooperation_values = data_cooperation[year_str]
        country_p_incl_values = [v for v in cooperation_values.values() if v is not None]
        
        if country_p_incl_values:
            avg_value = sum(country_p_incl_values) / len(country_p_incl_values)
            year_avg_values.append(avg_value)
    
    result = max(year_avg_values) if year_avg_values else None
    
    _cache['constants']['P_incl_t1'] = result
    save_to_json('P_incl_t1', {"value": result})
    return result

# 计算R_incl的函数
def R_incl(year, country):
    '''计算R_incl'''
    cached = get_from_cache('R_incl', year, country)
    if cached is not None:
        return cached
    
    r_incl_t_value = r_incl_t(year, country)
    p_incl_t_value = P_incl_t(year, country)
    r_incl_t1_value = r_incl_t1()
    p_incl_t1_value = P_incl_t1()
    
    if r_incl_t_value is None or p_incl_t_value is None or r_incl_t1_value is None or p_incl_t1_value is None:
        result = None
    else:
        valueac = r_incl_t_value / r_incl_t1_value
        valuebd = p_incl_t_value / p_incl_t1_value
        result = 0.5 * (valueac + valuebd)
    
    set_cache('R_incl', result, year, country)
    return result

# 计算R_oa的函数
def R_oa(year, country):
    '''计算R_oa'''
    cached = get_from_cache('R_oa', year, country)
    if cached is not None:
        return cached
    
    R_open_value = R_open(year, country)
    R_incl_value = R_incl(year, country)
    
    if R_open_value is None or R_incl_value is None:
        result = None
    else:
        result = math.sqrt(R_open_value ** 2 + R_incl_value ** 2)
    
    set_cache('R_oa', result, year, country)
    return result

# 计算R_oa_bar的函数
def R_oa_bar(year, country):
    '''计算R_oa_bar'''
    cached = get_from_cache('R_oa_bar', year, country)
    if cached is not None:
        return cached
    
    # 检查是否有缓存的历年最大值
    cache_key_max = 'R_oa_bar_max_of_max'
    if cache_key_max in _cache['constants']:
        max_of_max = _cache['constants'][cache_key_max]
    else:
        # 计算历年最大值
        data_oa = _data_cache['OA']
        years = sorted([int(y) for y in data_oa.keys()])
        year_max_R_oa = []
        
        for y in years:
            year_str = str(y)
            countries = list(data_oa[year_str].keys())
            
            country_R_oa_values = []
            for c in countries:
                r_oa_val = R_oa(y, c)
                if r_oa_val is not None:
                    country_R_oa_values.append(r_oa_val)
            
            if country_R_oa_values:
                max_R_oa = max(country_R_oa_values)
                year_max_R_oa.append(max_R_oa)
        
        max_of_max = max(year_max_R_oa) if year_max_R_oa else None
        _cache['constants'][cache_key_max] = max_of_max
    
    R_oa_current = R_oa(year, country)
    
    if R_oa_current is None or max_of_max is None or max_of_max == 0:
        result = None
    else:
        result = R_oa_current / max_of_max
    
    set_cache('R_oa_bar', result, year, country)
    return result

# 10
def f1(year, country):
    '''计算f1'''
    cached = get_from_cache('f1', year, country)
    if cached is not None:
        return cached
    
    year_int = int(year) if isinstance(year, str) else year
    year_str = str(year)
    
    data_fwci = _data_cache['FWCI']
    
    if year_str not in data_fwci or country not in data_fwci[year_str]:
        result = None
    else:
        fwci_value = data_fwci[year_str][country]
        
        if fwci_value is None:
            result = None
        elif year_int < 2014:
            result = fwci_value
        else:
            data_scientist = _data_cache['scientist']
            data_world_total = _data_cache['world_total']
            
            if year_str not in data_scientist or country not in data_scientist[year_str]:
                result = None
            elif year_str not in data_world_total:
                result = None
            else:
                scientist_value = data_scientist[year_str][country]
                word_scientist_value = data_world_total[year_str].get('word_scientist')
                
                if scientist_value is None or word_scientist_value is None or word_scientist_value == 0:
                    result = fwci_value
                else:
                    Au_current = scientist_value / word_scientist_value
                    
                    Au_ratios = []
                    for c in data_scientist[year_str].keys():
                        sci_val = data_scientist[year_str][c]
                        if sci_val is not None and word_scientist_value is not None and word_scientist_value > 0:
                            Au_ratio = sci_val / word_scientist_value
                            Au_ratios.append(Au_ratio)
                    
                    if not Au_ratios or sum(Au_ratios) / len(Au_ratios) == 0:
                        result = fwci_value
                    else:
                        Au_average = sum(Au_ratios) / len(Au_ratios)
                        result = 0.8 * fwci_value + 0.2 * (Au_current / Au_average)
    
    set_cache('f1', result, year, country)
    return result

# 11
def f2(year, country):
    '''计算f2'''
    cached = get_from_cache('f2', year, country)
    if cached is not None:
        return cached
    
    year_str = str(year)
    data_f2 = _data_cache['F2']
    result = data_f2[year_str][country] / 4
    
    set_cache('f2', result, year, country)
    return result

# 12
def f3(year, country):
    '''计算f3'''
    cached = get_from_cache('f3', year, country)
    if cached is not None:
        return cached
    
    year_str = str(year)
    data_f3 = _data_cache['F3']
    result = data_f3[year_str][country]
    
    set_cache('f3', result, year, country)
    return result

# 13
def S_od_t(year, country):
    '''计算S_od_t'''
    cached = get_from_cache('S_od_t', year, country)
    if cached is not None:
        return cached
    
    year_str = str(year)
    
    f1_value = f1(year, country)
    f2_value = f2(year, country)
    f3_value = f3(year, country)
    
    if f1_value is None or f2_value is None or f3_value is None:
        result = None
    else:
        avg_f = (f1_value + f2_value + f3_value) / 3
        
        data_total = _data_cache['total']
        
        if year_str not in data_total or country not in data_total[year_str]:
            result = None
        else:
            total_value = data_total[year_str][country]
            
            if total_value is None:
                result = None
            else:
                result = avg_f * total_value
    
    set_cache('S_od_t', result, year, country)
    return result

# 14
def S_od_t1():
    '''计算S_od_t1'''
    if 'S_od_t1' in _cache['constants']:
        return _cache['constants']['S_od_t1']
    
    data_total = _data_cache['total']
    years = sorted([int(y) for y in data_total.keys()])
    year_avg_values = []
    
    for year in years:
        year_str = str(year)
        
        if year_str not in data_total:
            continue
        
        countries = list(data_total[year_str].keys())
        country_S_od_values = []
        
        for country in countries:
            s_od_value = S_od_t(year, country)
            if s_od_value is not None:
                country_S_od_values.append(s_od_value)
        
        if country_S_od_values:
            avg_value = sum(country_S_od_values) / len(country_S_od_values)
            year_avg_values.append(avg_value)
    
    result = max(year_avg_values) if year_avg_values else None
    
    _cache['constants']['S_od_t1'] = result
    save_to_json('S_od_t1', {"value": result})
    return result

# 15
def A_od_t(year, country):
    '''计算A_od_t'''
    cached = get_from_cache('A_od_t', year, country)
    if cached is not None:
        return cached
    
    year_str = str(year)
    data_world_total = _data_cache['world_total']
    data_alpha_L = _data_cache['alpha_L']
    data_alpha_F = _data_cache['alpha_F']
    data_alpha_I = _data_cache['alpha_I']
    
    result = data_world_total[year_str]['world_oa_total'] * \
             data_alpha_L[year_str][country] * \
             data_alpha_F[year_str][country] * \
             data_alpha_I[year_str][country]
    
    set_cache('A_od_t', result, year, country)
    return result

# 16
def A_od_t1():
    '''计算A_od_t1'''
    if 'A_od_t1' in _cache['constants']:
        return _cache['constants']['A_od_t1']
    
    data_world_total = _data_cache['world_total']
    years = sorted([int(y) for y in data_world_total.keys()])
    
    if not years:
        result = None
    else:
        first_year = str(years[0])
        data_alpha_L = _data_cache['alpha_L']
        
        if first_year not in data_alpha_L:
            result = None
        else:
            countries = list(data_alpha_L[first_year].keys())
            year_avg_values = []
            
            for y in years:
                year_str = str(y)
                
                if year_str not in data_world_total:
                    continue
                
                if 'world_oa_total' not in data_world_total[year_str] or \
                   data_world_total[year_str]['world_oa_total'] is None:
                    continue
                
                country_A_od_values = []
                for c in countries:
                    a_od_value = A_od_t(y, c)
                    if a_od_value is not None:
                        country_A_od_values.append(a_od_value)
                
                if country_A_od_values:
                    avg_value = sum(country_A_od_values) / len(country_A_od_values)
                    year_avg_values.append(avg_value)
            
            result = max(year_avg_values) if year_avg_values else None
    
    _cache['constants']['A_od_t1'] = result
    save_to_json('A_od_t1', {"value": result})
    return result

# 17 计算R_od的函数
def R_od(year, country):
    '''计算R_od'''
    cached = get_from_cache('R_od', year, country)
    if cached is not None:
        return cached
    
    S_od_t_value = S_od_t(year, country)
    A_od_t_value = A_od_t(year, country)
    S_od_t1_value = S_od_t1()
    A_od_t1_value = A_od_t1()
    
    if S_od_t_value is None or A_od_t_value is None or \
       S_od_t1_value is None or A_od_t1_value is None:
        result = None
    else:
        valueac = S_od_t_value / S_od_t1_value
        valuebd = A_od_t_value / A_od_t1_value
        result = math.sqrt(valueac ** 2 + valuebd ** 2)
    
    set_cache('R_od', result, year, country)
    return result

# 计算R_od_bar的函数
def R_od_bar(year, country):
    '''计算R_od_bar'''
    cached = get_from_cache('R_od_bar', year, country)
    if cached is not None:
        return cached
    
    # 检查是否有缓存的历年最大值
    cache_key_max = 'R_od_bar_max_of_max'
    if cache_key_max in _cache['constants']:
        max_of_max = _cache['constants'][cache_key_max]
    else:
        # 计算历年最大值
        data_total = _data_cache['total']
        years = sorted([int(y) for y in data_total.keys()])
        year_max_R_od = []
        
        for y in years:
            year_str = str(y)
            countries = list(data_total[year_str].keys())
            
            country_R_od_values = []
            for c in countries:
                r_od_val = R_od(y, c)
                if r_od_val is not None:
                    country_R_od_values.append(r_od_val)
            
            if country_R_od_values:
                max_R_od = max(country_R_od_values)
                year_max_R_od.append(max_R_od)
        
        max_of_max = max(year_max_R_od) if year_max_R_od else None
        _cache['constants'][cache_key_max] = max_of_max
    
    R_od_current = R_od(year, country)
    
    if R_od_current is None or max_of_max is None or max_of_max == 0:
        result = None
    else:
        result = R_od_current / max_of_max
    
    set_cache('R_od_bar', result, year, country)
    return result

def R(year, country):
    '''计算R'''
    cached = get_from_cache('R', year, country)
    if cached is not None:
        return cached
    
    year_str = str(year)
    data_weight = _data_cache['weight']
    R_oa_bar_value = R_oa_bar(year, country)
    R_od_bar_value = R_od_bar(year, country)
    R_op_bar_value = R_op_bar(year, country)
    
    if R_oa_bar_value is None or R_od_bar_value is None or R_op_bar_value is None:
        result = None
    else:
        result = data_weight['W_OA'] * R_oa_bar_value + \
                 data_weight['W_OD'] * R_od_bar_value + \
                 data_weight['W_OP'] * R_op_bar_value
    
    set_cache('R', result, year, country)
    return result

# ==================== 批量计算和保存函数 ====================
def batch_calculate_and_save():
    """批量计算所有函数的所有(year, country)组合，并保存到JSON文件"""
    # 获取所有年份和国家
    data_total = _data_cache['total']
    years = sorted([int(y) for y in data_total.keys()])
    countries = list(data_total[str(years[0])].keys())
    
    print(f"开始批量计算: {len(years)}年 × {len(countries)}国家 = {len(years) * len(countries)}个组合")
    
    # 需要计算的函数列表（按依赖顺序）
    functions_to_calculate = [
        ('r_open_t', r_open_t),
        ('P_open_t', P_open_t),
        ('R_open', R_open),
        ('r_incl_t', r_incl_t),
        ('P_incl_t', P_incl_t),
        ('R_incl', R_incl),
        ('R_oa', R_oa),
        ('f1', f1),
        ('f2', f2),
        ('f3', f3),
        ('S_od_t', S_od_t),
        ('A_od_t', A_od_t),
        ('R_od', R_od),
        ('R_oa_bar', R_oa_bar),
        ('R_od_bar', R_od_bar),
        ('R_op_bar', R_op_bar),
        ('R', R),
    ]
    
    # 计算每个函数的所有组合
    for func_name, func in functions_to_calculate:
        print(f"计算 {func_name}...")
        results = {}
        
        for year in years:
            year_str = str(year)
            results[year_str] = {}
            
            for country in countries:
                try:
                    value = func(year, country)
                    results[year_str][country] = value
                except Exception as e:
                    print(f"  错误: {year}年 {country} - {e}")
                    results[year_str][country] = None
        
        # 保存到JSON
        save_to_json(func_name, results)
        print(f"  ✓ {func_name} 计算完成并已保存")
    
    print("\n所有计算完成！")

if __name__ == "__main__":
    batch_calculate_and_save()
