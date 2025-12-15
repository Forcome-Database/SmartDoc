"""add webhook kingdee fields

Revision ID: add_webhook_kingdee
Revises: add_pipeline_001
Create Date: 2025-12-12

添加Webhook表的金蝶相关字段：
- webhook_type: Webhook类型（standard/kingdee）
- kingdee_config: 金蝶配置JSON
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_webhook_kingdee'
down_revision = 'add_pipeline_001'  # 依赖于pipeline迁移
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 添加 webhook_type 字段（使用枚举名称大写）
    op.add_column(
        'webhooks',
        sa.Column(
            'webhook_type',
            sa.Enum('STANDARD', 'KINGDEE', name='webhooktype'),
            nullable=True,
            server_default='STANDARD',
            comment='Webhook类型'
        )
    )
    
    # 添加 kingdee_config 字段
    op.add_column(
        'webhooks',
        sa.Column(
            'kingdee_config',
            sa.JSON(),
            nullable=True,
            comment='金蝶配置（金蝶类型使用）'
        )
    )
    
    # 修改 endpoint_url 为可空（金蝶类型不需要）
    op.alter_column(
        'webhooks',
        'endpoint_url',
        existing_type=sa.String(500),
        nullable=True
    )
    
    # 修改 request_template 为可空（金蝶类型不需要）
    op.alter_column(
        'webhooks',
        'request_template',
        existing_type=sa.JSON(),
        nullable=True
    )


def downgrade() -> None:
    # 删除 kingdee_config 字段
    op.drop_column('webhooks', 'kingdee_config')
    
    # 删除 webhook_type 字段
    op.drop_column('webhooks', 'webhook_type')
    
    # 恢复 endpoint_url 为非空
    op.alter_column(
        'webhooks',
        'endpoint_url',
        existing_type=sa.String(500),
        nullable=False
    )
    
    # 恢复 request_template 为非空
    op.alter_column(
        'webhooks',
        'request_template',
        existing_type=sa.JSON(),
        nullable=False
    )
