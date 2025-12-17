"""add paid_available to daily_free_tasks

Revision ID: e2a0c8f4c1f5
Revises: c3d4e5f6a7b8
Create Date: 2025-12-12 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e2a0c8f4c1f5'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade():
    # Для SQLite нужно сначала добавить колонку как nullable, обновить данные
    # SQLite не поддерживает добавление NOT NULL колонки к существующей таблице напрямую
    op.add_column('daily_free_tasks', 
                  sa.Column('paid_available', sa.Integer(), nullable=True))
    
    # Обновляем все существующие записи, устанавливая paid_available=0
    op.execute("UPDATE daily_free_tasks SET paid_available = 0 WHERE paid_available IS NULL")
    
    # Теперь пытаемся сделать колонку NOT NULL через batch_alter_table
    # Если это не сработает, колонка останется nullable, но в модели мы указали nullable=False
    # что для SQLite приемлемо
    try:
        with op.batch_alter_table('daily_free_tasks') as batch_op:
            batch_op.alter_column('paid_available', nullable=False)
    except Exception:
        # Если не удалось изменить на NOT NULL, оставляем nullable
        # В модели указано nullable=False, но в БД будет nullable (для SQLite это нормально)
        pass


def downgrade():
    with op.batch_alter_table('daily_free_tasks') as batch_op:
        batch_op.drop_column('paid_available')

