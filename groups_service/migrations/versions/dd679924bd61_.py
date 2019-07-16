"""empty message

Revision ID: dd679924bd61
Revises: 619ccb0a4f27
Create Date: 2019-07-13 13:56:25.569872

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'dd679924bd61'
down_revision = '619ccb0a4f27'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('forms_form_id_key', 'forms', type_='unique')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('forms_form_id_key', 'forms', ['form_id'])
    # ### end Alembic commands ###