-- ============================================
-- 智能文档处理中台 - 初始化数据脚本
-- Enterprise IDP Platform - Initial Data Script
-- ============================================

-- 注意：此脚本在数据库迁移完成后执行

-- ============================================
-- 1. 创建默认管理员账号
-- ============================================
-- 密码: admin123 (使用bcrypt加密)
-- 注意：生产环境必须修改默认密码
INSERT INTO users (id, username, email, password_hash, role, is_active, created_at)
VALUES (
    'U_ADMIN_001',
    'admin',
    'admin@idp-platform.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIxF6q0OXm',  -- admin123
    'admin',
    TRUE,
    NOW()
) ON DUPLICATE KEY UPDATE id=id;

-- ============================================
-- 2. 创建默认系统配置
-- ============================================

-- OCR超时时间配置
INSERT INTO system_configs (`key`, `value`, description, updated_at)
VALUES (
    'ocr_timeout',
    '300',
    'OCR处理超时时间（秒）',
    NOW()
) ON DUPLICATE KEY UPDATE `value`='300';

-- LLM超时时间配置
INSERT INTO system_configs (`key`, `value`, description, updated_at)
VALUES (
    'llm_timeout',
    '60',
    'LLM请求超时时间（秒）',
    NOW()
) ON DUPLICATE KEY UPDATE `value`='60';

-- 最大并行任务数配置
INSERT INTO system_configs (`key`, `value`, description, updated_at)
VALUES (
    'max_parallel_tasks',
    '4',
    '最大并行OCR任务数',
    NOW()
) ON DUPLICATE KEY UPDATE `value`='4';

-- LLM Token单价配置
INSERT INTO system_configs (`key`, `value`, description, updated_at)
VALUES (
    'llm_token_price',
    '0.002',
    'LLM Token单价（用于成本估算）',
    NOW()
) ON DUPLICATE KEY UPDATE `value`='0.002';

-- 消息队列最大长度配置
INSERT INTO system_configs (`key`, `value`, description, updated_at)
VALUES (
    'mq_max_length',
    '10000',
    '消息队列最大长度',
    NOW()
) ON DUPLICATE KEY UPDATE `value`='10000';

-- 原始文件留存期配置
INSERT INTO system_configs (`key`, `value`, description, updated_at)
VALUES (
    'file_retention_days',
    '30',
    '原始文件留存期（天）',
    NOW()
) ON DUPLICATE KEY UPDATE `value`='30';

-- 提取数据留存期配置
INSERT INTO system_configs (`key`, `value`, description, updated_at)
VALUES (
    'data_retention_days',
    '0',
    '提取数据留存期（天，0表示永久保留）',
    NOW()
) ON DUPLICATE KEY UPDATE `value`='0';

-- 上传接口限流配置
INSERT INTO system_configs (`key`, `value`, description, updated_at)
VALUES (
    'rate_limit_upload',
    '100',
    '上传接口限流（次/分钟）',
    NOW()
) ON DUPLICATE KEY UPDATE `value`='100';

-- 查询接口限流配置
INSERT INTO system_configs (`key`, `value`, description, updated_at)
VALUES (
    'rate_limit_query',
    '1000',
    '查询接口限流（次/分钟）',
    NOW()
) ON DUPLICATE KEY UPDATE `value`='1000';

-- 熔断器失败阈值配置
INSERT INTO system_configs (`key`, `value`, description, updated_at)
VALUES (
    'circuit_breaker_threshold',
    '5',
    'LLM服务熔断阈值（连续失败次数）',
    NOW()
) ON DUPLICATE KEY UPDATE `value`='5';

-- 熔断器恢复超时配置
INSERT INTO system_configs (`key`, `value`, description, updated_at)
VALUES (
    'circuit_breaker_timeout',
    '300',
    '熔断器恢复超时时间（秒）',
    NOW()
) ON DUPLICATE KEY UPDATE `value`='300';

-- ============================================
-- 3. 创建示例规则（可选）
-- ============================================

-- 示例：发票识别规则
INSERT INTO rules (id, name, code, document_type, current_version, created_by, created_at)
VALUES (
    'R_INVOICE_001',
    '增值税发票识别',
    'INVOICE_VAT',
    '发票',
    NULL,
    'U_ADMIN_001',
    NOW()
) ON DUPLICATE KEY UPDATE id=id;

-- 示例规则的草稿版本
INSERT INTO rule_versions (rule_id, version, status, config, created_at)
VALUES (
    'R_INVOICE_001',
    'V0.1',
    'draft',
    JSON_OBJECT(
        'ocr_engine', 'paddleocr',
        'language', 'zh',
        'page_strategy', JSON_OBJECT(
            'mode', 'single_page',
            'separator', '\n'
        ),
        'schema', JSON_OBJECT(
            'invoice_number', JSON_OBJECT(
                'label', '发票号码',
                'type', 'String',
                'required', TRUE
            ),
            'invoice_date', JSON_OBJECT(
                'label', '开票日期',
                'type', 'Date',
                'required', TRUE
            ),
            'total_amount', JSON_OBJECT(
                'label', '价税合计',
                'type', 'Decimal',
                'required', TRUE
            )
        ),
        'extraction_rules', JSON_ARRAY(),
        'validation_rules', JSON_ARRAY(),
        'enhancement', JSON_OBJECT(
            'enabled', FALSE
        )
    ),
    NOW()
) ON DUPLICATE KEY UPDATE rule_id=rule_id;

-- ============================================
-- 完成初始化
-- ============================================
SELECT '初始化数据脚本执行完成' AS message;
SELECT CONCAT('默认管理员账号: admin / admin123 (请在生产环境修改密码)') AS notice;
