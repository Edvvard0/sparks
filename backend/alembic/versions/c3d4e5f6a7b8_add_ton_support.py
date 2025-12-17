"""add_ton_support

Revision ID: c3d4e5f6a7b8
Revises: b1b7946a6c3b
Create Date: 2025-01-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# Определяем тип БД для правильной настройки
def get_database_type():
    """Определяет тип базы данных"""
    bind = op.get_bind()
    return bind.dialect.name


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b1b7946a6c3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    db_type = get_database_type()
    
    # Добавляем поля в таблицу users
    op.add_column('users', sa.Column('wallet_address', sa.String(length=48), nullable=True))
    if db_type == 'sqlite':
        op.add_column('users', sa.Column('has_lifetime_subscription', sa.Boolean(), nullable=False, server_default='0'))
    else:
        op.add_column('users', sa.Column('has_lifetime_subscription', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index(op.f('ix_users_wallet_address'), 'users', ['wallet_address'], unique=True)
    
    # Изменяем enum PaymentMethod - удаляем YOOKASSA, добавляем TON
    # Для PostgreSQL используем ALTER TYPE, для SQLite просто обновляем данные
    if db_type == 'postgresql':
        # PostgreSQL-специфичные команды для изменения ENUM
        op.execute("ALTER TYPE paymentmethod RENAME TO paymentmethod_old")
        op.execute("CREATE TYPE paymentmethod AS ENUM ('ton', 'daily_bonus', 'system')")
        op.execute("ALTER TABLE transactions ALTER COLUMN payment_method TYPE paymentmethod USING payment_method::text::paymentmethod")
        op.execute("DROP TYPE paymentmethod_old")
    else:
        # Для SQLite просто обновляем существующие значения 'yookassa' на 'ton' (если есть)
        # SQLite хранит ENUM как TEXT, так что просто обновляем данные
        op.execute("UPDATE transactions SET payment_method = 'ton' WHERE payment_method = 'yookassa'")
    
    # Добавляем поля для TON в таблицу transactions
    op.add_column('transactions', sa.Column('ton_transaction_hash', sa.String(length=64), nullable=True))
    op.add_column('transactions', sa.Column('ton_from_address', sa.String(length=48), nullable=True))
    op.add_column('transactions', sa.Column('ton_to_address', sa.String(length=48), nullable=True))
    op.add_column('transactions', sa.Column('ton_amount', sa.String(length=20), nullable=True))
    op.create_index(op.f('ix_transactions_ton_transaction_hash'), 'transactions', ['ton_transaction_hash'], unique=False)


def downgrade() -> None:
    db_type = get_database_type()
    
    # Удаляем индексы и поля TON из transactions
    op.drop_index(op.f('ix_transactions_ton_transaction_hash'), table_name='transactions')
    op.drop_column('transactions', 'ton_amount')
    op.drop_column('transactions', 'ton_to_address')
    op.drop_column('transactions', 'ton_from_address')
    op.drop_column('transactions', 'ton_transaction_hash')
    
    # Возвращаем enum PaymentMethod
    if db_type == 'postgresql':
        # PostgreSQL-специфичные команды
        op.execute("ALTER TYPE paymentmethod RENAME TO paymentmethod_old")
        op.execute("CREATE TYPE paymentmethod AS ENUM ('yookassa', 'daily_bonus', 'system')")
        op.execute("ALTER TABLE transactions ALTER COLUMN payment_method TYPE paymentmethod USING payment_method::text::paymentmethod")
        op.execute("DROP TYPE paymentmethod_old")
    else:
        # Для SQLite просто обновляем данные обратно
        op.execute("UPDATE transactions SET payment_method = 'yookassa' WHERE payment_method = 'ton'")
    
    # Удаляем поля из users
    op.drop_index(op.f('ix_users_wallet_address'), table_name='users')
    op.drop_column('users', 'has_lifetime_subscription')
    op.drop_column('users', 'wallet_address')

