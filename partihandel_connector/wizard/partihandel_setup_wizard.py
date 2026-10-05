from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError

from ..models.res_config_settings import DEFAULT_PARTIHANDEL_URL, URL_PARAM

INTEGRATION_LOGIN = 'partihandel-integration'
INTEGRATION_NAME = 'Partihandel Integration'
API_KEY_NAME = 'Partihandel'

# What Partihandel does in Odoo: create and update customers/suppliers (res.partner) and products
# (product.template), read taxes, units and countries, and create and post customer invoices
# (account.move). These are the smallest standard groups that cover it.
INTEGRATION_GROUPS = (
    'base.group_user',
    'base.group_partner_manager',
    'product.group_product_manager',
    'account.group_account_invoice',
)

# Partihandel's own page for entering the Odoo connection.
PARTIHANDEL_ODOO_PAGE = '/odoo'


class PartihandelSetupWizard(models.TransientModel):
    _name = 'partihandel.setup.wizard'
    _description = 'Connect to Partihandel'

    state = fields.Selection([('intro', 'Intro'), ('done', 'Done')], default='intro', required=True)
    partihandel_url = fields.Char(string='Partihandel address')
    user_exists = fields.Boolean(compute='_compute_user_exists')
    odoo_url = fields.Char(string='URL', compute='_compute_connection_details')
    odoo_url_is_https = fields.Boolean(compute='_compute_connection_details')
    database = fields.Char(string='Database', compute='_compute_connection_details')
    login = fields.Char(string='Login', default=INTEGRATION_LOGIN, readonly=True)
    # Shown once, like Odoo's own "New API key" dialog. Transient records are vacuumed shortly
    # after, and only the hash is kept in res.users.apikeys.
    api_key = fields.Char(string='API key', readonly=True)

    def _compute_user_exists(self):
        exists = bool(self._find_integration_user())
        for wizard in self:
            wizard.user_exists = exists

    def _compute_connection_details(self):
        base_url = (self.env['ir.config_parameter'].sudo().get_param('web.base.url') or '').rstrip('/')
        for wizard in self:
            wizard.odoo_url = base_url
            wizard.odoo_url_is_https = base_url.startswith('https://')
            wizard.database = self.env.cr.dbname

    @api.model
    def _check_admin(self):
        if not self.env.user.has_group('base.group_system'):
            raise AccessError(_('Only administrators can connect Odoo to Partihandel.'))

    @api.model
    def _find_integration_user(self):
        return self.env['res.users'].sudo().with_context(active_test=False).search([('login', '=', INTEGRATION_LOGIN)], limit=1)

    @api.model
    def _integration_groups(self):
        return self.env['res.groups'].browse([self.env.ref(xmlid).id for xmlid in INTEGRATION_GROUPS])

    @api.model
    def _groups_field(self):
        # Renamed from groups_id to group_ids in Odoo 19.
        return 'group_ids' if 'group_ids' in self.env['res.users']._fields else 'groups_id'

    @api.model
    def _ensure_integration_user(self):
        users = self.env['res.users'].sudo()
        groups = self._integration_groups()
        groups_field = self._groups_field()
        company = self.env.company
        user = self._find_integration_user()
        if not user:
            # No password: the user can only authenticate with the API key, never log in to the
            # web client.
            return users.with_context(no_reset_password=True).create({
                'name': INTEGRATION_NAME,
                'login': INTEGRATION_LOGIN,
                'company_id': company.id,
                'company_ids': [(6, 0, company.ids)],
                groups_field: [(6, 0, groups.ids)],
            })
        values = {groups_field: [(4, group.id) for group in groups]}
        if not user.active:
            values['active'] = True
        if company not in user.company_ids:
            values['company_ids'] = [(4, company.id)]
        user.write(values)
        return user

    @api.model
    def action_open(self, partihandel_url=None):
        self._check_admin()
        wizard = self.create({
            'partihandel_url': partihandel_url
            or self.env['ir.config_parameter'].sudo().get_param(URL_PARAM)
            or DEFAULT_PARTIHANDEL_URL,
        })
        return wizard._reopen()

    def _reopen(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Connect to Partihandel'),
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_generate_key(self):
        """Create (or reuse) the integration user and give it a fresh API key.

        Earlier keys issued by this wizard are revoked, so running it again is how the key is
        rotated: Partihandel keeps working only once the new key has been pasted in.
        """
        self.ensure_one()
        self._check_admin()
        user = self._ensure_integration_user()
        apikeys = self.env['res.users.apikeys'].sudo()
        apikeys.search([('user_id', '=', user.id), ('name', '=', API_KEY_NAME)])._remove()
        # with_user makes the key belong to the integration user; sudo allows a key without an
        # expiry date, which an integration needs (Odoo would otherwise cap it for a non-admin).
        key = apikeys.with_user(user).sudo()._generate(None, API_KEY_NAME, None)
        self.write({'api_key': key, 'state': 'done'})
        return self._reopen()

    def action_open_partihandel_page(self):
        self.ensure_one()
        return self.action_open_partihandel(self.partihandel_url)

    @api.model
    def action_open_partihandel(self, partihandel_url=None):
        base = (partihandel_url or DEFAULT_PARTIHANDEL_URL).rstrip('/')
        if not base.startswith('https://'):
            raise UserError(_('The Partihandel address must start with https://'))
        return {'type': 'ir.actions.act_url', 'url': base + PARTIHANDEL_ODOO_PAGE, 'target': 'new'}
