"""3.3.0 : fonctionnalites_9

Revision ID: 2b6ac7b172d3
Revises: 25a21d2410b7
Create Date: 2016-06-21 11:12:57.071400

"""

# revision identifiers, used by Alembic.
revision = '2b6ac7b172d3'
down_revision = '25a21d2410b7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    import logging
    logger = logging.getLogger('alembic.here')
    op.add_column(
        "user_datas",
        sa.Column(
            'statut_social_status_today_id',
            sa.Integer,
            sa.ForeignKey('social_status_option.id'),
        )
    )
    op.add_column(
        "user_datas",
        sa.Column(
            "parcours_employee_quality_id",
            sa.Integer,
            sa.ForeignKey('employee_quality_option.id'),
        )
    )

    op.add_column(
        "task",
        sa.Column(
            "company_id",
            sa.Integer,
            sa.ForeignKey('company.id'),
        )
    )
    op.add_column(
        "task",
        sa.Column(
            "internal_number",
            sa.String(40),
        )
    )
    logger.warn("######################## Company stuff")
    from autonomie.models.base import (
        DBSESSION,
    )
    from alembic.context import get_bind
    conn = get_bind()

    session = DBSESSION()
    query = "select t.id, p.company_id from task t, project p where t.project_id = p.id"

    for id, company_id in conn.execute(query):
        req = "update task set company_id={0} where id={1}".format(company_id, id)
        session.execute(req)

    logger.warn("######################## Task stuff")
    from autonomie.models.task import Task
    from autonomie.models.customer import Customer
    from autonomie.models.project import Project
    from autonomie.models.project import Phase

    from sqlalchemy.orm import joinedload
    from sqlalchemy.orm import load_only

    query = Task.query().options(
        load_only("sequence_number", "date", "phase_id")
    )
    query = query.filter(
        Task.type_.in_(['invoice', 'estimation', 'cancelinvoice'])
    )
    query = query.options(joinedload(Task.customer).load_only(Customer.code))
    query = query.options(joinedload(Task.project).load_only(Project.code))

    for task in query:
        if Phase.get(task.phase_id) is None:
            session.delete(task)
        else:
            task.internal_number = task._number_tmpl.format(s=task)
            session.merge(task)

    logger.warn("######################## Contract stuff")
    from autonomie.models.user import UserDatas, ContractHistory
    for id_, last_avenant in UserDatas.query('id', 'parcours_last_avenant'):
        if last_avenant:
            session.add(
                ContractHistory(
                    userdatas_id=id_,
                    date=last_avenant,
                    number=-1
                )
            )

    from zope.sqlalchemy import mark_changed
    mark_changed(session)


def downgrade():
    op.execute("SET FOREIGN_KEY_CHECKS=0;")
    op.drop_table('employee_quality_option')
    op.drop_column('user_datas', 'statut_social_today_id',)
    op.drop_column('user_datas', 'parcours_employee_quality_id',)
    op.execute("SET FOREIGN_KEY_CHECKS=1;")
