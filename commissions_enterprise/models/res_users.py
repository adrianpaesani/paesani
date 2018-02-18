# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import Warning

class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if self._context.get('ctx_job_id'):
            emp_ids = self.env['hr.employee'].search([('user_id', '!=', False),
                                                      ('job_id', '=', self._context['ctx_job_id'])])
            args += [('id', 'in', [emp.user_id.id for emp in emp_ids])]
        return super(ResUsers, self).name_search(name=name, args=args, operator='ilike', limit=limit)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: