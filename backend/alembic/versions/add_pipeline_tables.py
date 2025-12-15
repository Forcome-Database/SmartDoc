"""add pipeline tables

Revision ID: add_pipeline_001
Revises: 
Create Date: 2025-01-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_pipeline_001'
down_revision = '3dba847fa795'  # 依赖于初始迁移
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建管道表
    op.create_table(
        'pipelines',
        sa.Column('id', sa.String(50), primary_key=True, comment='管道ID'),
        sa.Column('name', sa.String(100), nullable=False, comment='管道名称'),
        sa.Column('description', sa.Text, nullable=True, comment='管道描述'),
        sa.Column('rule_id', sa.String(50), sa.ForeignKey('rules.id'), nullable=False, unique=True, comment='规则ID'),
        sa.Column('status', sa.Enum('draft', 'active', 'inactive', name='pipelinestatus'), default='draft', comment='管道状态'),
        sa.Column('script_content', sa.Text, nullable=False, comment='Python脚本内容'),
        sa.Column('requirements', sa.Text, nullable=True, comment='依赖包列表'),
        sa.Column('timeout_seconds', sa.Integer, default=300, comment='执行超时时间'),
        sa.Column('max_retries', sa.Integer, default=1, comment='最大重试次数'),
        sa.Column('memory_limit_mb', sa.Integer, default=512, comment='内存限制'),
        sa.Column('env_variables', sa.JSON, nullable=True, comment='环境变量'),
        sa.Column('created_at', sa.DateTime, default=sa.func.now(), comment='创建时间'),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now(), comment='更新时间'),
        sa.Column('created_by', sa.String(50), sa.ForeignKey('users.id'), nullable=True, comment='创建人ID'),
    )
    
    op.create_index('ix_pipelines_rule_id', 'pipelines', ['rule_id'])
    
    # 创建管道执行记录表
    op.create_table(
        'pipeline_executions',
        sa.Column('id', sa.String(50), primary_key=True, comment='执行ID'),
        sa.Column('pipeline_id', sa.String(50), sa.ForeignKey('pipelines.id'), nullable=False, comment='管道ID'),
        sa.Column('task_id', sa.String(50), sa.ForeignKey('tasks.id'), nullable=False, comment='任务ID'),
        sa.Column('status', sa.Enum('pending', 'running', 'success', 'failed', 'timeout', name='executionstatus'), default='pending', comment='执行状态'),
        sa.Column('retry_count', sa.Integer, default=0, comment='重试次数'),
        sa.Column('input_data', sa.JSON, nullable=True, comment='输入数据'),
        sa.Column('output_data', sa.JSON, nullable=True, comment='输出数据'),
        sa.Column('stdout', sa.Text, nullable=True, comment='标准输出'),
        sa.Column('stderr', sa.Text, nullable=True, comment='错误输出'),
        sa.Column('error_message', sa.Text, nullable=True, comment='错误信息'),
        sa.Column('duration_ms', sa.Integer, nullable=True, comment='执行耗时'),
        sa.Column('memory_used_mb', sa.Integer, nullable=True, comment='内存使用'),
        sa.Column('created_at', sa.DateTime, default=sa.func.now(), comment='创建时间'),
        sa.Column('started_at', sa.DateTime, nullable=True, comment='开始时间'),
        sa.Column('completed_at', sa.DateTime, nullable=True, comment='完成时间'),
    )
    
    op.create_index('ix_pipeline_executions_pipeline_id', 'pipeline_executions', ['pipeline_id'])
    op.create_index('ix_pipeline_executions_task_id', 'pipeline_executions', ['task_id'])
    op.create_index('ix_pipeline_executions_status', 'pipeline_executions', ['status'])
    op.create_index('ix_pipeline_executions_created_at', 'pipeline_executions', ['created_at'])


def downgrade() -> None:
    op.drop_table('pipeline_executions')
    op.drop_table('pipelines')
    
    # 删除枚举类型
    op.execute("DROP TYPE IF EXISTS executionstatus")
    op.execute("DROP TYPE IF EXISTS pipelinestatus")
