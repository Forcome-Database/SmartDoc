"""
数据清洗与校验服务

提供数据清洗、类型转换、校验等功能
"""
import re
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from decimal import Decimal, InvalidOperation
from loguru import logger
import js2py


class ValidationError:
    """校验错误"""
    def __init__(self, field: str, message: str, value: Any = None):
        self.field = field
        self.message = message
        self.value = value
    
    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "message": self.message,
            "value": self.value
        }


class ValidationResult:
    """校验结果"""
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[str] = []
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def is_valid(self) -> bool:
        return not self.has_errors
    
    def add_error(self, field: str, message: str, value: Any = None):
        self.errors.append(ValidationError(field, message, value))
    
    def add_warning(self, message: str):
        self.warnings.append(message)
    
    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": self.warnings
        }


class ValidationService:
    """数据清洗与校验服务"""
    
    # 常用日期格式
    DATE_FORMATS = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y年%m月%d日",
        "%Y.%m.%d",
        "%Y%m%d",
    ]
    
    # 常用正则模式
    PATTERNS = {
        "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "phone": r"^1[3-9]\d{9}$",  # 中国手机号
        "url": r"^https?://[^\s]+$",
        "id_card": r"^\d{17}[\dXx]$",  # 中国身份证号
    }
    
    def __init__(self):
        """初始化服务"""
        pass
    
    # ==================== 11.1 数据清洗 ====================
    
    def clean_data(
        self, 
        data: Dict[str, Any], 
        cleaning_rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        清洗数据管道（支持嵌套字段路径）
        
        Args:
            data: 原始数据字典
            cleaning_rules: 清洗规则列表
                [
                    {
                        "field": "amount",  # 或 "order_line.jinge" 嵌套路径
                        "operations": [
                            {"type": "regex_replace", "pattern": ",", "replacement": ""},
                            {"type": "trim"}
                        ]
                    }
                ]
        
        Returns:
            清洗后的数据字典
        """
        import copy
        cleaned_data = copy.deepcopy(data)
        
        for rule in cleaning_rules:
            field = rule.get("field")
            operations = rule.get("operations", [])
            
            if not field or not operations:
                continue
            
            # 处理嵌套字段路径（如 order_line.jinge）
            if '.' in field:
                self._clean_nested_field(cleaned_data, field, operations)
            else:
                # 简单字段
                if field not in cleaned_data:
                    continue
                
                value = cleaned_data[field]
                value = self._apply_operations(value, operations, field)
                cleaned_data[field] = value
        
        return cleaned_data
    
    def _clean_nested_field(
        self,
        data: Dict[str, Any],
        field_path: str,
        operations: List[Dict[str, Any]]
    ):
        """
        清洗嵌套字段（支持数组）
        
        Args:
            data: 数据字典（会被原地修改）
            field_path: 字段路径，如 "order_line.jinge"
            operations: 清洗操作列表
        """
        parts = field_path.split('.')
        
        if len(parts) < 2:
            return
        
        parent_key = parts[0]
        child_path = '.'.join(parts[1:])
        
        if parent_key not in data:
            return
        
        parent_value = data[parent_key]
        
        if isinstance(parent_value, list):
            # 数组类型，遍历每个元素
            for item in parent_value:
                if isinstance(item, dict):
                    if '.' in child_path:
                        # 继续递归
                        self._clean_nested_field(item, child_path, operations)
                    else:
                        # 到达目标字段
                        if child_path in item:
                            item[child_path] = self._apply_operations(
                                item[child_path], operations, field_path
                            )
        elif isinstance(parent_value, dict):
            # 对象类型
            if '.' in child_path:
                self._clean_nested_field(parent_value, child_path, operations)
            else:
                if child_path in parent_value:
                    parent_value[child_path] = self._apply_operations(
                        parent_value[child_path], operations, field_path
                    )
    
    def _apply_operations(
        self,
        value: Any,
        operations: List[Dict[str, Any]],
        field_name: str
    ) -> Any:
        """
        对值应用清洗操作
        
        Args:
            value: 原始值
            operations: 操作列表
            field_name: 字段名（用于日志）
            
        Returns:
            清洗后的值
        """
        for operation in operations:
            op_type = operation.get("type")
            
            try:
                if op_type == "regex_replace":
                    value = self.regex_replace(
                        value,
                        operation.get("pattern"),
                        operation.get("replacement", "")
                    )
                elif op_type == "trim":
                    value = self.trim(value)
                elif op_type == "format_date":
                    value = self.format_date(
                        value,
                        operation.get("target_format", "%Y-%m-%d")
                    )
                else:
                    logger.warning(f"未知的清洗操作类型: {op_type}")
            
            except Exception as e:
                logger.warning(f"清洗字段 {field_name} 时出错: {str(e)}")
        
        return value
    
    def regex_replace(
        self, 
        value: Any, 
        pattern: str, 
        replacement: str
    ) -> str:
        """
        正则替换操作
        
        Args:
            value: 原始值
            pattern: 正则表达式模式
            replacement: 替换字符串
        
        Returns:
            替换后的字符串
        """
        if value is None:
            return None
        
        text = str(value)
        return re.sub(pattern, replacement, text)
    
    def trim(self, value: Any) -> str:
        """
        去空格操作
        
        Args:
            value: 原始值
        
        Returns:
            去除首尾空格后的字符串
        """
        if value is None:
            return None
        
        return str(value).strip()
    
    def format_date(
        self, 
        value: Any, 
        target_format: str = "%Y-%m-%d"
    ) -> Optional[str]:
        """
        日期格式化操作，支持多种日期格式识别
        
        Args:
            value: 原始日期值
            target_format: 目标日期格式
        
        Returns:
            格式化后的日期字符串，识别失败返回原值
        """
        if value is None:
            return None
        
        date_str = str(value).strip()
        
        # 尝试各种日期格式
        for fmt in self.DATE_FORMATS:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime(target_format)
            except ValueError:
                continue
        
        # 如果所有格式都失败，记录警告并返回原值
        logger.warning(f"无法识别日期格式: {date_str}")
        return date_str
    
    # ==================== 11.2 数据类型转换 ====================
    
    def convert_type(
        self, 
        value: Any, 
        target_type: str,
        decimal_places: Optional[int] = None
    ) -> tuple[Any, Optional[str]]:
        """
        数据类型转换
        
        Args:
            value: 原始值
            target_type: 目标类型 (String, Int, Date, Decimal, Boolean)
            decimal_places: Decimal类型的小数位数
        
        Returns:
            (转换后的值, 错误信息)
        """
        if value is None or value == "":
            return None, None
        
        try:
            if target_type == "String":
                return str(value), None
            
            elif target_type == "Int":
                # 移除可能的逗号分隔符
                if isinstance(value, str):
                    value = value.replace(",", "")
                return int(float(value)), None
            
            elif target_type == "Date":
                if isinstance(value, datetime):
                    return value.strftime("%Y-%m-%d"), None
                
                date_str = str(value).strip()
                for fmt in self.DATE_FORMATS:
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        return dt.strftime("%Y-%m-%d"), None
                    except ValueError:
                        continue
                
                return value, f"无法转换为日期类型: {value}"
            
            elif target_type == "Decimal":
                # 移除可能的逗号分隔符
                if isinstance(value, str):
                    value = value.replace(",", "")
                
                decimal_value = Decimal(str(value))
                
                # 如果指定了小数位数，进行四舍五入
                if decimal_places is not None:
                    quantize_str = "0." + "0" * decimal_places
                    decimal_value = decimal_value.quantize(Decimal(quantize_str))
                
                return float(decimal_value), None
            
            elif target_type == "Boolean":
                # 真值表示
                true_values = ["true", "yes", "是", "1", "y", "t"]
                false_values = ["false", "no", "否", "0", "n", "f"]
                
                value_lower = str(value).lower().strip()
                
                if value_lower in true_values:
                    return True, None
                elif value_lower in false_values:
                    return False, None
                else:
                    return value, f"无法转换为布尔类型: {value}"
            
            else:
                return value, f"不支持的类型: {target_type}"
        
        except (ValueError, InvalidOperation) as e:
            return value, f"类型转换失败: {str(e)}"
    
    def convert_schema_types(
        self, 
        data: Dict[str, Any], 
        schema: Dict[str, Any]
    ) -> tuple[Dict[str, Any], List[str]]:
        """
        根据Schema定义转换所有字段类型
        
        Args:
            data: 数据字典
            schema: Schema定义
        
        Returns:
            (转换后的数据, 警告列表)
        """
        converted_data = {}
        warnings = []
        
        for field_name, field_config in schema.items():
            if field_name not in data:
                continue
            
            field_type = field_config.get("type", "String")
            decimal_places = field_config.get("decimal_places")
            
            value = data[field_name]
            converted_value, error = self.convert_type(
                value, 
                field_type, 
                decimal_places
            )
            
            if error:
                warnings.append(f"{field_name}: {error}")
            
            converted_data[field_name] = converted_value
        
        return converted_data, warnings
    
    # ==================== 11.3 数据校验 ====================
    
    def validate(
        self, 
        data: Dict[str, Any], 
        validation_rules: List[Dict[str, Any]]
    ) -> ValidationResult:
        """
        数据校验（支持普通字段、对象、数组）
        
        Args:
            data: 数据字典
            validation_rules: 校验规则列表
                [
                    {"field": "email", "required": true, "pattern": "email"},
                    {"field": "age", "range": {"min": 0, "max": 150}},
                    {"field": "jianyi", "type": "not_empty"},  # 对象非空
                    {"field": "pangbai", "type": "array_length", "min": 1, "max": 10},  # 数组长度
                    {"field": "jianyi", "type": "has_fields", "required_fields": ["fengge", "yinyue"]},  # 必须包含子字段
                    {"field": "pangbai", "type": "array_unique", "unique_key": "scene"}  # 数组元素唯一
                ]
        
        Returns:
            ValidationResult对象
        """
        result = ValidationResult()
        
        for rule in validation_rules:
            field = rule.get("field")
            rule_type = rule.get("type", "")
            
            # 支持嵌套字段路径
            value = self._get_nested_value(data, field)
            
            # 必填校验（兼容旧格式）
            if rule.get("required", False):
                error = self.validate_required(field, value)
                if error:
                    result.add_error(field, error, value)
                    continue
            
            # 非空校验（对象/数组）
            if rule_type == "not_empty":
                error = self.validate_not_empty(field, value)
                if error:
                    result.add_error(field, error, value)
                continue
            
            # 数组长度校验
            if rule_type == "array_length":
                # 兼容前端字段名（minLength/maxLength）和后端字段名（min/max）
                min_len = rule.get("min") or rule.get("minLength")
                max_len = rule.get("max") or rule.get("maxLength")
                error = self.validate_array_length(
                    field, value, min_len, max_len
                )
                if error:
                    result.add_error(field, error, value)
                continue
            
            # 对象必须包含子字段校验
            if rule_type == "has_fields":
                # 兼容前端字段名（requiredFields）和后端字段名（required_fields）
                req_fields = rule.get("required_fields") or rule.get("requiredFields", [])
                error = self.validate_has_fields(field, value, req_fields)
                if error:
                    result.add_error(field, error, value)
                continue
            
            # 数组元素唯一性校验
            if rule_type == "array_unique":
                # 兼容前端字段名（uniqueKey）和后端字段名（unique_key）
                unique_key = rule.get("unique_key") or rule.get("uniqueKey")
                error = self.validate_array_unique(field, value, unique_key)
                if error:
                    result.add_error(field, error, value)
                continue
            
            # 数组元素必填子字段校验
            if rule_type == "array_items_required":
                req_fields = rule.get("required_fields", [])
                errors = self.validate_array_items_required(field, value, req_fields)
                for error in errors:
                    result.add_error(field, error, value)
                continue
            
            # 如果值为空且非必填，跳过其他校验
            if value is None or value == "":
                continue
            
            # 正则格式校验
            if "pattern" in rule or "custom_pattern" in rule:
                error = self.validate_pattern(
                    field, 
                    value, 
                    rule.get("pattern"),
                    rule.get("custom_pattern")
                )
                if error:
                    result.add_error(field, error, value)
            
            # 数值范围校验
            if "range" in rule:
                error = self.validate_range(
                    field, 
                    value, 
                    rule["range"].get("min"),
                    rule["range"].get("max")
                )
                if error:
                    result.add_error(field, error, value)
        
        return result

    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """
        获取嵌套字段的值
        
        Args:
            data: 数据字典
            field_path: 字段路径，如 "jianyi.fengge"
            
        Returns:
            字段值
        """
        if '.' not in field_path:
            return data.get(field_path)
        
        parts = field_path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                idx = int(part)
                current = current[idx] if idx < len(current) else None
            else:
                return None
            
            if current is None:
                return None
        
        return current
    
    def validate_required(self, field: str, value: Any) -> Optional[str]:
        """
        必填校验
        
        Args:
            field: 字段名
            value: 字段值
        
        Returns:
            错误信息，校验通过返回None
        """
        if value is None or value == "":
            return f"必填字段为空: {field}"
        
        return None
    
    def validate_pattern(
        self, 
        field: str, 
        value: Any,
        pattern_name: Optional[str] = None,
        custom_pattern: Optional[str] = None
    ) -> Optional[str]:
        """
        正则格式校验，支持Email、Phone等
        
        Args:
            field: 字段名
            value: 字段值
            pattern_name: 预定义模式名称 (email, phone, url, id_card)
            custom_pattern: 自定义正则表达式
        
        Returns:
            错误信息，校验通过返回None
        """
        value_str = str(value)
        
        # 使用自定义模式
        if custom_pattern:
            pattern = custom_pattern
        # 使用预定义模式
        elif pattern_name:
            if pattern_name in self.PATTERNS:
                pattern = self.PATTERNS[pattern_name]
            else:
                # 未知的预定义模式
                supported = ', '.join(self.PATTERNS.keys())
                return f"未知的校验模式: '{pattern_name}'，支持的模式: {supported}"
        else:
            # pattern_name 为空且没有 custom_pattern，跳过校验
            return None
        
        if not re.match(pattern, value_str):
            pattern_desc = pattern_name or "自定义格式"
            return f"字段 {field} 格式不正确，期望格式: {pattern_desc}"
        
        return None
    
    def validate_range(
        self, 
        field: str, 
        value: Any,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None
    ) -> Optional[str]:
        """
        数值范围校验
        
        Args:
            field: 字段名
            value: 字段值
            min_value: 最小值
            max_value: 最大值
        
        Returns:
            错误信息，校验通过返回None
        """
        try:
            # 转换为数值
            if isinstance(value, str):
                value = value.replace(",", "")
            numeric_value = float(value)
            
            if min_value is not None and numeric_value < min_value:
                return f"字段 {field} 的值 {numeric_value} 小于最小值 {min_value}"
            
            if max_value is not None and numeric_value > max_value:
                return f"字段 {field} 的值 {numeric_value} 大于最大值 {max_value}"
            
            return None
        
        except (ValueError, TypeError):
            return f"字段 {field} 无法转换为数值类型"

    # ==================== 对象/数组校验 ====================

    def validate_not_empty(
        self,
        field: str,
        value: Any
    ) -> Optional[str]:
        """
        非空校验（支持对象和数组）
        
        Args:
            field: 字段名
            value: 字段值
            
        Returns:
            错误信息，校验通过返回None
        """
        if value is None:
            return f"字段 {field} 不能为空"
        
        if isinstance(value, dict) and len(value) == 0:
            return f"字段 {field} 对象不能为空"
        
        if isinstance(value, list) and len(value) == 0:
            return f"字段 {field} 数组不能为空"
        
        if isinstance(value, str) and value.strip() == "":
            return f"字段 {field} 不能为空字符串"
        
        return None

    def validate_array_length(
        self,
        field: str,
        value: Any,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None
    ) -> Optional[str]:
        """
        数组长度校验
        
        Args:
            field: 字段名
            value: 字段值（应为数组）
            min_length: 最小长度
            max_length: 最大长度
            
        Returns:
            错误信息，校验通过返回None
        """
        if not isinstance(value, list):
            return f"字段 {field} 不是数组类型"
        
        length = len(value)
        
        if min_length is not None and length < min_length:
            return f"字段 {field} 数组长度 {length} 小于最小长度 {min_length}"
        
        if max_length is not None and length > max_length:
            return f"字段 {field} 数组长度 {length} 大于最大长度 {max_length}"
        
        return None

    def validate_has_fields(
        self,
        field: str,
        value: Any,
        required_fields: List[str]
    ) -> Optional[str]:
        """
        对象必须包含指定子字段校验
        
        Args:
            field: 字段名
            value: 字段值（应为对象）
            required_fields: 必须包含的子字段列表
            
        Returns:
            错误信息，校验通过返回None
        """
        if not isinstance(value, dict):
            return f"字段 {field} 不是对象类型"
        
        missing_fields = []
        for req_field in required_fields:
            if req_field not in value or value[req_field] is None or value[req_field] == "":
                missing_fields.append(req_field)
        
        if missing_fields:
            return f"字段 {field} 缺少必要的子字段: {', '.join(missing_fields)}"
        
        return None

    def validate_array_unique(
        self,
        field: str,
        value: Any,
        unique_key: Optional[str] = None
    ) -> Optional[str]:
        """
        数组元素唯一性校验
        
        Args:
            field: 字段名
            value: 字段值（应为数组）
            unique_key: 如果数组元素是对象，指定用于判断唯一性的键
            
        Returns:
            错误信息，校验通过返回None
        """
        if not isinstance(value, list):
            return f"字段 {field} 不是数组类型"
        
        if len(value) == 0:
            return None
        
        seen = set()
        duplicates = []
        
        for i, item in enumerate(value):
            if unique_key and isinstance(item, dict):
                # 对象数组，按指定键判断
                check_value = item.get(unique_key)
            else:
                # 简单数组，直接判断值
                check_value = str(item) if not isinstance(item, (str, int, float)) else item
            
            if check_value in seen:
                duplicates.append(f"索引{i}: {check_value}")
            else:
                seen.add(check_value)
        
        if duplicates:
            return f"字段 {field} 存在重复元素: {', '.join(duplicates[:3])}{'...' if len(duplicates) > 3 else ''}"
        
        return None

    def validate_array_items_required(
        self,
        field: str,
        value: Any,
        required_fields: List[str]
    ) -> List[str]:
        """
        数组元素必填子字段校验
        
        检查数组是否存在且非空，以及每个元素是否包含必填子字段
        
        Args:
            field: 字段名
            value: 字段值（应为数组）
            required_fields: 数组元素中必须包含的子字段列表
            
        Returns:
            错误信息列表，校验通过返回空列表
        """
        errors = []
        
        # 检查数组是否存在
        if value is None:
            errors.append(f"必填字段为空: {field}")
            return errors
        
        # 检查是否为数组类型
        if not isinstance(value, list):
            errors.append(f"字段 {field} 应为数组类型")
            return errors
        
        # 检查数组是否为空
        if len(value) == 0:
            errors.append(f"必填数组为空: {field}")
            return errors
        
        # 检查每个元素的必填子字段
        for i, item in enumerate(value):
            if not isinstance(item, dict):
                continue
            
            for req_field in required_fields:
                if req_field not in item or item[req_field] is None or item[req_field] == "":
                    errors.append(f"数组 {field} 第{i+1}项缺少必填字段: {req_field}")
        
        return errors
    
    # ==================== 11.4 自定义脚本校验 ====================
    
    def execute_js_expression(
        self, 
        expression: str, 
        fields: Dict[str, Any],
        timeout_ms: int = 100
    ) -> tuple[bool, Optional[str]]:
        """
        执行JavaScript表达式校验
        
        Args:
            expression: JavaScript表达式 (如 "fields.amount * fields.count == fields.total")
            fields: 字段值字典
            timeout_ms: 超时时间（毫秒）
        
        Returns:
            (校验结果, 错误信息)
        """
        try:
            # 构建JavaScript上下文
            js_code = f"""
            var fields = {json.dumps(fields)};
            var result = ({expression});
            result;
            """
            
            # 使用js2py执行JavaScript代码
            # 注意: js2py不支持真正的超时，这里只是示意
            context = js2py.EvalJs()
            context.fields = fields
            
            # 执行表达式
            result = context.eval(expression)
            
            # 转换结果为布尔值
            if isinstance(result, bool):
                return result, None
            else:
                # 如果结果不是布尔值，尝试转换
                return bool(result), None
        
        except Exception as e:
            error_msg = f"JavaScript表达式执行失败: {str(e)}"
            logger.warning(error_msg)
            return False, error_msg
    
    def validate_custom_scripts(
        self, 
        data: Dict[str, Any], 
        script_rules: List[Dict[str, Any]]
    ) -> ValidationResult:
        """
        执行自定义脚本校验
        
        Args:
            data: 数据字典
            script_rules: 脚本规则列表
                [
                    {
                        "name": "金额校验",
                        "expression": "fields.amount * fields.count == fields.total",
                        "error_message": "金额计算不正确"
                    }
                ]
        
        Returns:
            ValidationResult对象
        """
        result = ValidationResult()
        
        for rule in script_rules:
            expression = rule.get("expression")
            error_message = rule.get("error_message", "自定义校验失败")
            rule_name = rule.get("name", "未命名规则")
            
            if not expression:
                continue
            
            # 执行JavaScript表达式
            is_valid, error = self.execute_js_expression(expression, data)
            
            if error:
                result.add_error(rule_name, error)
            elif not is_valid:
                result.add_error(rule_name, error_message)
        
        return result
    
    # ==================== 综合处理 ====================
    
    def process_data(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
        cleaning_rules: Optional[List[Dict[str, Any]]] = None,
        validation_rules: Optional[List[Dict[str, Any]]] = None,
        script_rules: Optional[List[Dict[str, Any]]] = None
    ) -> tuple[Dict[str, Any], ValidationResult]:
        """
        综合处理：清洗 -> 类型转换 -> 校验
        
        Args:
            data: 原始数据
            schema: Schema定义
            cleaning_rules: 清洗规则
            validation_rules: 校验规则
            script_rules: 自定义脚本规则
        
        Returns:
            (处理后的数据, 校验结果)
        """
        result = ValidationResult()
        
        # 1. 数据清洗
        if cleaning_rules:
            data = self.clean_data(data, cleaning_rules)
        
        # 2. 类型转换
        data, warnings = self.convert_schema_types(data, schema)
        for warning in warnings:
            result.add_warning(warning)
        
        # 3. 数据校验
        if validation_rules:
            validation_result = self.validate(data, validation_rules)
            result.errors.extend(validation_result.errors)
            result.warnings.extend(validation_result.warnings)
        
        # 4. 自定义脚本校验
        if script_rules:
            script_result = self.validate_custom_scripts(data, script_rules)
            result.errors.extend(script_result.errors)
            result.warnings.extend(script_result.warnings)
        
        return data, result
