"""request_items.selected_options: vorab angekreuzte Optionen im Anschreiben

Revision ID: a7c3e91d5b24
Revises: 422bdc577ed0
Create Date: 2026-10-06 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7c3e91d5b24'
down_revision: Union[str, None] = '422bdc577ed0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Hinweis: Autogenerate findet weiterhin die bekannte, VORBESTEHENDE und
    # unabhaengige Typ-Abweichung auf authorities.phone - bewusst NICHT Teil
    # dieser Migration (eine Migration = eine fachliche Aenderung). Diese
    # Migration betrifft ausschliesslich request_items.selected_options
    # (JSON-Liste 0-basierter Indizes, z.B. '[0,2]'; NULL = nichts angekreuzt).
    with op.batch_alter_table('request_items', schema=None) as batch_op:
        batch_op.add_column(sa.Column('selected_options', sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('request_items', schema=None) as batch_op:
        batch_op.drop_column('selected_options')
