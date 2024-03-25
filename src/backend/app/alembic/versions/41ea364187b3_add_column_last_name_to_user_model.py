"""Add column last_name to User model

Revision ID: 41ea364187b3
Revises: 95adabbfb9ec
Create Date: 2024-03-15 02:00:11.812434

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '41ea364187b3'
down_revision = '95adabbfb9ec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('template', 'prompt',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               type_=sqlmodel.sql.sqltypes.AutoString(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('template', 'prompt',
               existing_type=sqlmodel.sql.sqltypes.AutoString(),
               type_=postgresql.JSON(astext_type=sa.Text()),
               nullable=True)
    # ### end Alembic commands ###
