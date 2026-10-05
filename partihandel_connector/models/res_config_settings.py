from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

DEFAULT_PARTIHANDEL_URL = 'https://app.partihandel.se'
URL_PARAM = 'partihandel_connector.url'


def normalize_partihandel_url(url):
    """Strip whitespace and trailing slashes; Partihandel is only reachable over https."""
    url = (url or '').strip().rstrip('/')
    if url and not url.startswith('https://'):
        raise ValidationError(_('The Partihandel address must start with https://'))
    return url


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    partihandel_url = fields.Char(
        string='Partihandel address',
        config_parameter=URL_PARAM,
        default=DEFAULT_PARTIHANDEL_URL,
        help='The address you use to log in to Partihandel, for example https://app.partihandel.se',
    )

    @api.constrains('partihandel_url')
    def _check_partihandel_url(self):
        for settings in self:
            normalize_partihandel_url(settings.partihandel_url)

    def set_values(self):
        for settings in self:
            settings.partihandel_url = normalize_partihandel_url(settings.partihandel_url) or DEFAULT_PARTIHANDEL_URL
        return super().set_values()

    # The address is passed along from the form rather than read from the stored parameter, so the
    # buttons use what the admin just typed even before they press Save.
    def action_open_partihandel_setup(self):
        self.ensure_one()
        return self.env['partihandel.setup.wizard'].action_open(normalize_partihandel_url(self.partihandel_url))

    def action_open_partihandel(self):
        self.ensure_one()
        return self.env['partihandel.setup.wizard'].action_open_partihandel(normalize_partihandel_url(self.partihandel_url))
