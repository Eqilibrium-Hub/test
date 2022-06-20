from odoo import api, fields, models, _

class ResUsers(models.Model):
    _inherit = "res.users"
    
    temp_signature = fields.Text(company_dependent=True)
    
    @api.depends_context('company')
    def on_switch_company_click(self, company_id=False):
        company = self.env["res.company"].browse(company_id) if company_id else self.env.company
        if company_id:
            self.company_id = company
        res_users = self.env['res.users'].sudo().search([])
        for user in res_users:
            user.with_context(force_signature=True).signature = user.with_company(company).temp_signature
    
    def __init__(self, pool, cr):
        res = super().__init__(pool, cr)        
        type(self).SELF_READABLE_FIELDS = self.SELF_READABLE_FIELDS + ['temp_signature']
        type(self).SELF_WRITEABLE_FIELDS = self.SELF_WRITEABLE_FIELDS + ['temp_signature']
        return res
    
    def write(self, vals):
        for user in self:
            if not self.env.context.get('force_signature'):
                if vals.get('signature'):
                    user.temp_signature = vals.get('signature')
        return super(ResUsers, self).write(vals)
    
    @api.model_create_multi
    def create(self, vals_list):
        users = super(ResUsers, self).create(vals_list)
        for user in users:
            if user.signature:
                user.temp_signature = user.signature
        return users

class ResPartners(models.Model):
    _inherit = 'res.partner'

    email = fields.Char(company_dependent=True)
    
    def write(self, vals):
        res_company = self.env['res.company'].search([])
        if not self.env.context.get('force_email'):
            if 'email' in vals:
                for partner in self.filtered(lambda partner: not partner.user_ids):
                    for company in res_company:
                        partner.with_context(force_company=company.id, force_email=True).email = vals.get('email')
        return super(ResPartners, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        partners = super(ResPartners, self).create(vals_list)
        res_company = self.env['res.company'].search([])
        for partner in partners.filtered(lambda partner: partner.email):
            for company in res_company:
                partner.with_company(company.id).email = partner.email
        return partners
