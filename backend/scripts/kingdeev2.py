# -*- coding: utf-8 -*-
"""
金蝶K3Cloud数据处理管道脚本 V2

功能：将OCR提取的数据转换为金蝶创建客户订单所需的格式
字段映射：
  - po_number -> FBillNo
  - ship_to -> F_fsh_shipto
  - due_date - 60天 -> F_FSH_CHCQ, F_fsh_Text
  - due_date - 7天 -> FBHRQ
  - order_list -> FEntity (订单明细)

可用变量（由管道工作器注入）：
  - task_id: str - 任务ID
  - extracted_data: dict - OCR提取的数据
  - ocr_text: str - OCR识别的全文
  - meta_info: dict - 任务元信息

输出：
  - output_data: dict - 处理后的金蝶订单数据（完整API提交格式）

extracted_data 预期结构：
{
    "po_number": "PO-2024-001",
    "ship_to": "收货地址",
    "due_date": "1/12/2026" 或 "2026-01-12",
    "order_list": [
        {
            "part_number": "客户物料编码",
            "order_qty": "100",
            "unit_price": "25.50"
        },
        ...
    ]
}
"""

import os
import requests
import json
from datetime import datetime, timedelta


# ================= 配置区域 =================
# 金蝶K3 Cloud API配置（从环境变量获取，支持默认值）
API_HOST = os.environ.get('KINGDEE_API_URL', 'http://192.168.16.158/k3cloud/')
DB_ID = os.environ.get('KINGDEE_DB_ID', '68f6f3dd8893a2')
USERNAME = os.environ.get('KINGDEE_USER', 'administrator')
PASSWORD = os.environ.get('KINGDEE_PASSWORD', 'kingdee@2025')
LANG_ID = 2052

# API 路由
URL_LOGIN = f"{API_HOST}Kingdee.BOS.WebApi.ServicesStub.AuthService.ValidateUser.common.kdsvc"
URL_QUERY = f"{API_HOST}Kingdee.BOS.WebApi.ServicesStub.DynamicFormService.ExecuteBillQuery.common.kdsvc"

# 金蝶表单ID
FORM_ID = "PAEZ_PO"


# ================= 工具类 =================
class KingdeeClient:
    """金蝶K3Cloud API客户端"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def login(self):
        """登录金蝶系统"""
        params = [DB_ID, USERNAME, PASSWORD, LANG_ID]
        payload = {"parameters": json.dumps(params)}
        try:
            response = self.session.post(URL_LOGIN, json=payload)
            res_json = response.json()
            if res_json.get("LoginResultType") == 1:
                print("金蝶登录成功")
                return True
            else:
                print(f"金蝶登录失败: {res_json.get('Message')}")
                return False
        except Exception as e:
            print(f"金蝶登录异常: {e}")
            return False

    def query_data(self, form_id, field_keys, filter_string):
        """
        通用查询接口

        Args:
            form_id: 表单ID
            field_keys: 查询字段，逗号分隔
            filter_string: 过滤条件

        Returns:
            查询结果列表
        """
        data = {
            "FormId": form_id,
            "FieldKeys": field_keys,
            "FilterString": filter_string,
            "Limit": 2000
        }
        payload = {"parameters": [data]}
        try:
            response = self.session.post(URL_QUERY, json=payload)
            result = response.json()
            return result
        except Exception as e:
            print(f"金蝶查询异常: {e}")
            return []


# ================= 工具函数 =================
def parse_date(date_str):
    """
    解析日期字符串，支持多种格式

    Args:
        date_str: 日期字符串，如 "1/12/2026", "2026-01-12", "2026/01/12"

    Returns:
        datetime对象，解析失败返回None
    """
    if not date_str:
        return None

    formats = [
        '%m/%d/%Y',      # 1/12/2026
        '%Y-%m-%d',      # 2026-01-12
        '%Y/%m/%d',      # 2026/01/12
        '%d/%m/%Y',      # 12/01/2026
        '%Y年%m月%d日',  # 2026年01月12日
    ]

    for fmt in formats:
        try:
            return datetime.strptime(str(date_str).strip(), fmt)
        except ValueError:
            continue

    print(f"警告: 无法解析日期 '{date_str}'，使用当前日期")
    return datetime.now()


def format_date(dt):
    """格式化日期为金蝶所需格式 YYYY-MM-DD"""
    if dt is None:
        return ""
    return dt.strftime('%Y-%m-%d')


def parse_number(value, default=0.0):
    """
    解析数字字符串

    Args:
        value: 数字字符串，可能包含逗号、货币符号等
        default: 解析失败时的默认值

    Returns:
        float数值
    """
    if value is None:
        return default
    try:
        # 移除常见的非数字字符
        cleaned = str(value).replace(',', '').replace(
            '$', '').replace('¥', '').strip()
        return float(cleaned) if cleaned else default
    except (ValueError, TypeError):
        return default


def query_material_mapping(client, cust_mat_no):
    """
    查询客户物料映射，获取内部物料编码

    SQL逻辑: 
    SELECT e.FMATERIALID 
    FROM T_SAL_CUSTMATMAPPING h
    JOIN T_SAL_CUSTMATMAPPINGENTRY e ON h.FID = e.FID
    WHERE h.FBILLNO='KHWLDYB0024' AND e.FCUSTMATNO='{cust_mat_no}'

    Args:
        client: KingdeeClient实例
        cust_mat_no: 客户物料编码

    Returns:
        内部物料编码，未找到则返回原编码
    """
    result = client.query_data(
        form_id="SAL_CustMatMapping",
        field_keys="FMaterialId.FNumber",
        filter_string=f"FBillNo = 'KHWLDYB0024' AND FCustMatNo = '{cust_mat_no}'"
    )

    if result and len(result) > 0 and len(result[0]) > 0:
        internal_no = result[0][0]
        print(f"物料映射: {cust_mat_no} -> {internal_no}")
        return internal_no
    else:
        print(f"警告: 未找到客户物料 {cust_mat_no} 的映射，使用原编码")
        return cust_mat_no


def query_material_attributes(client, material_no):
    """
    查询物料属性（FSYB/FXSY/FXSZ）

    SQL逻辑: SELECT FSYB, FXSY, FXSZ FROM T_BD_MATERIAL WHERE FNumber = '{material_no}'

    Args:
        client: KingdeeClient实例
        material_no: 内部物料编码

    Returns:
        dict: {fsyb, fxsy, fxsz}
    """
    defaults = {'fsyb': 'DBG', 'fxsy': '', 'fxsz': ''}

    result = client.query_data(
        form_id="BD_MATERIAL",
        field_keys="FSYB.FNumber,FXSY.FNumber,FXSZ.FNumber",
        filter_string=f"FNumber = '{material_no}'"
    )

    if result and len(result) > 0:
        row = result[0]
        attrs = {
            'fsyb': row[0] if row[0] else defaults['fsyb'],
            'fxsy': row[1] if len(row) > 1 and row[1] else defaults['fxsy'],
            'fxsz': row[2] if len(row) > 2 and row[2] else defaults['fxsz']
        }
        print(
            f"物料属性 {material_no}: FSYB={attrs['fsyb']}, FXSY={attrs['fxsy']}, FXSZ={attrs['fxsz']}")
        return attrs
    else:
        print(f"警告: 未查询到物料 {material_no} 的属性，使用默认值")
        return defaults


# ================= 主处理逻辑 =================
def process_data(ocr_data):
    """
    处理OCR提取数据，生成金蝶订单完整数据

    Args:
        ocr_data: OCR提取的数据字典

    Returns:
        金蝶API提交格式的完整数据
    """
    # 初始化金蝶客户端并登录
    client = KingdeeClient()
    if not client.login():
        raise Exception("金蝶K3 Cloud登录失败")

    # 1. 处理表头日期逻辑
    due_date_obj = parse_date(ocr_data.get("due_date", ""))
    if due_date_obj is None:
        due_date_obj = datetime.now()

    # F_fsh_Text, F_FSH_CHCQ = due_date - 60天
    date_minus_60 = due_date_obj - timedelta(days=60)
    # FBHRQ = due_date - 7天
    date_minus_7 = due_date_obj - timedelta(days=7)

    str_date_60 = format_date(date_minus_60)
    str_date_7 = format_date(date_minus_7)

    # 2. 准备分录数据
    entity_rows = []
    order_list = ocr_data.get("order_list", [])

    for item in order_list:
        cust_mat_no = item.get("part_number", "")
        if not cust_mat_no:
            print("警告: 订单行缺少part_number，跳过")
            continue

        # 查询内部物料编码
        internal_mat_no = query_material_mapping(client, cust_mat_no)

        # 查询物料属性
        mat_attrs = query_material_attributes(client, internal_mat_no)

        # 解析数量和单价
        qty = parse_number(item.get("order_qty", "0"))
        price = parse_number(item.get("unit_price", "0"))
        amount = qty * price

        # 构建分录行
        entry = {
            "FEntryID": 0,
            "FWL": {"FNUMBER": internal_mat_no},
            "FPOWL": cust_mat_no,
            "F_KHWL": {"FNUMBER": cust_mat_no},
            "FSYB": {"FNumber": mat_attrs['fsyb']},
            "FXSY": {"FNUMBER": mat_attrs['fxsy']},
            "FXSZ": {"FNUMBER": mat_attrs['fxsz']},
            "FSL": qty,
            "FDJ": price,
            "FJE": amount,
            "FHB": "6847bd4a489347",
            "F_FSH_JSZK": 0.9,
            "FISFREE": "false"
        }
        entity_rows.append(entry)

    # 3. 组装最终Model
    final_model = {
        "FBillNo": ocr_data.get("po_number", ""),
        "FDate": format_date(datetime.now()),
        "FDocumentStatus": "Z",
        "FSaleOrgId": {"FNumber": "101"},
        "FCustId": {"FNumber": "UPL"},
        "F_XSBB": {"FNumber": "PRE007"},
        "FLOCALCURRID": {"FNumber": "PRE007"},
        "F_fsh_Priceterms": "DDU",
        "F_fsh_shipto": ocr_data.get("ship_to", ""),
        "F_fsh_departure": {"FNumber": "02"},
        "F_fsh_Assistant": {"FNumber": "070"},
        "F_fsh_Text": str_date_60,
        "F_FSH_CHCQ": str_date_60,
        "FBHRQ": str_date_7,
        "F_PAEZ_Text": "Phillip Gilbert",
        "FEntity": entity_rows
    }

    # 4. 构建完整的金蝶API提交参数格式
    output = {
        "parameters": [
            FORM_ID,
            {
                "NeedUpDateFields": [],
                "NeedReturnFields": ["FBillNo", "FID"],
                "IsDeleteEntry": "true",
                "Model": final_model
            }
        ]
    }

    return output


output_data = process_data(extracted_data)
