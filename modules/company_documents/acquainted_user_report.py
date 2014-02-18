# coding=utf-8
__author__ = 'skripnik'
from openerp import tools
from openerp.osv import fields
from openerp.osv.orm import Model


class AcquaintedUserReport(Model):
    _name = 'acquainted.user.report'
    _auto = False

    _columns = {
        'id':fields.integer('ID'),
        'doc_id': fields.integer('Номер распоряжения'),
        'user_id': fields.many2one('res.users', 'Пользователь'),
        'label':  fields.selection(
            [
                ('yes', 'Ознакомлен'),
                ('no', 'Не ознакомлен'),
            ],
            'Ознакомлен',
        ),
    }

    # def init(self, cr):
    #     tools.drop_view_if_exists(cr, 'acquainted_user_report')
    #     cr.execute("""
    #         create or replace view acquainted_user_report as (
    #         select
    #           row_number()
    #           OVER () AS id,
    #           doc_id,
    #           user_id,
    #           label
    #         from(
    #               select
    #               see_u.doc_id,
    #               see_u.user_id,
    #               CONCAT( CASE WHEN ((select au.user_id from acquainted_users as au where au.user_id = see_u.user_id and au.disposition_id = see_u.doc_id) is null) then 'no' else 'yes' end) as label
    #             from
    #               see_company_disposal_users_rel as see_u
    #
    #             union
    #
    #             select
    #               see_g.doc_id,
    #               st_g.usr_id as user_id,
    #               CONCAT( CASE WHEN  ((select au.user_id from acquainted_users as au where au.user_id = st_g.usr_id and au.disposition_id = see_g.doc_id) is null) then 'no' else 'yes' end) as label
    #             from
    #               see_company_disposal_groups_rel as see_g
    #             join res_user_storage_groups_rel as st_g
    #             on (st_g.gro_id = see_g.group_id)
    #             order by doc_id
    #
    #         ) r
    #         )""")


AcquaintedUserReport()