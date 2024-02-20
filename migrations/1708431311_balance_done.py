"""Balance_DONE

Revision ID: 1708431311
Revises: 1708368006
Create Date: 2024-02-20 12:15:11.625115

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1708431311'
down_revision: Union[str, None] = '1708368006'
branch_labels: Union[str, Sequence[str], None] = ()
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_balance_id', table_name='balance')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_balance_id', 'balance', ['id'], unique=False)
    # ### end Alembic commands ###
