-- 创建数据处理管道相关表
-- 执行命令: mysql -u root -p idp_platform < create_pipeline_tables.sql

-- 删除旧表（如果存在）
DROP TABLE IF EXISTS pipeline_executions;
DROP TABLE IF EXISTS pipelines;

-- 创建管道表
CREATE TABLE IF NOT EXISTS pipelines (
    id VARCHAR(50) PRIMARY KEY COMMENT '管道ID',
    name VARCHAR(100) NOT NULL COMMENT '管道名称',
    description TEXT COMMENT '管道描述',
    rule_id VARCHAR(50) NOT NULL UNIQUE COMMENT '规则ID',
    status VARCHAR(20) DEFAULT 'draft' COMMENT '管道状态',
    script_content TEXT NOT NULL COMMENT 'Python脚本内容',
    requirements TEXT COMMENT '依赖包列表',
    timeout_seconds INT DEFAULT 300 COMMENT '执行超时时间（秒）',
    max_retries INT DEFAULT 1 COMMENT '最大重试次数',
    memory_limit_mb INT DEFAULT 512 COMMENT '内存限制（MB）',
    env_variables JSON COMMENT '环境变量',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    created_by VARCHAR(50) COMMENT '创建人ID',
    FOREIGN KEY (rule_id) REFERENCES rules(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX ix_pipelines_rule_id (rule_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据处理管道';

-- 创建管道执行记录表
CREATE TABLE IF NOT EXISTS pipeline_executions (
    id VARCHAR(50) PRIMARY KEY COMMENT '执行ID',
    pipeline_id VARCHAR(50) NOT NULL COMMENT '管道ID',
    task_id VARCHAR(50) NOT NULL COMMENT '任务ID',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '执行状态',
    retry_count INT DEFAULT 0 COMMENT '重试次数',
    input_data JSON COMMENT '输入数据',
    output_data JSON COMMENT '输出数据',
    stdout TEXT COMMENT '标准输出',
    stderr TEXT COMMENT '错误输出',
    error_message TEXT COMMENT '错误信息',
    duration_ms INT COMMENT '执行耗时（毫秒）',
    memory_used_mb INT COMMENT '内存使用（MB）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    started_at DATETIME COMMENT '开始时间',
    completed_at DATETIME COMMENT '完成时间',
    FOREIGN KEY (pipeline_id) REFERENCES pipelines(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    INDEX ix_pipeline_executions_pipeline_id (pipeline_id),
    INDEX ix_pipeline_executions_task_id (task_id),
    INDEX ix_pipeline_executions_status (status),
    INDEX ix_pipeline_executions_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='管道执行记录';
