from odoo.exceptions import AccessError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

from ..wizard.partihandel_setup_wizard import INTEGRATION_GROUPS


@tagged('post_install', '-at_install')
class TestPartihandelSetupWizard(AccountTestInvoicingCommon):

    def _run_wizard(self):
        action = self.env['partihandel.setup.wizard'].action_open('https://app.partihandel.se')
        wizard = self.env['partihandel.setup.wizard'].browse(action['res_id'])
        wizard.action_generate_key()
        return wizard, wizard._find_integration_user()

    def _key_owner(self, key):
        return self.env['res.users.apikeys']._check_credentials(scope='rpc', key=key)

    def test_creates_integration_user_with_working_key(self):
        wizard, user = self._run_wizard()
        self.assertEqual(wizard.state, 'done')
        self.assertTrue(wizard.api_key)
        self.assertEqual(self._key_owner(wizard.api_key), user.id)
        self.assertEqual(wizard.login, user.login)
        self.assertEqual(wizard.database, self.env.cr.dbname)
        for xmlid in INTEGRATION_GROUPS:
            self.assertTrue(user.has_group(xmlid), xmlid)
        self.assertFalse(user.has_group('base.group_system'))
        self.assertFalse(user.share)

    def test_rerun_rotates_the_key_and_reuses_the_user(self):
        first, user = self._run_wizard()
        second, same_user = self._run_wizard()
        self.assertEqual(user, same_user)
        self.assertFalse(self._key_owner(first.api_key))
        self.assertEqual(self._key_owner(second.api_key), user.id)

    def test_rerun_reactivates_an_archived_user(self):
        _wizard, user = self._run_wizard()
        user.active = False
        wizard, same_user = self._run_wizard()
        self.assertEqual(user, same_user)
        self.assertTrue(user.active)
        self.assertEqual(self._key_owner(wizard.api_key), user.id)

    def test_integration_user_can_do_what_partihandel_does(self):
        """Mirrors the calls pifa-api makes: partners, products, taxes/units/countries, invoices."""
        _wizard, user = self._run_wizard()
        env = self.env(user=user)
        partner = env['res.partner'].create({'name': 'Test Customer AB', 'country_id': env.ref('base.se').id})
        partner.write({'email': 'noreply@dittforetag.se'})
        product = env['product.template'].create({'name': 'Test Article', 'list_price': 10.0})
        product.write({'default_code': 'TEST-1'})
        env['account.tax'].search_read([], ['name'], limit=1)
        env['uom.uom'].search_read([], ['name'], limit=1)
        invoice = env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.product_variant_id.id,
                'quantity': 2,
                'price_unit': 10.0,
            })],
        })
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')

    def test_only_administrators_can_run_it(self):
        _wizard, integration_user = self._run_wizard()
        with self.assertRaises(AccessError):
            self.env['partihandel.setup.wizard'].with_user(integration_user).action_open()

    def test_open_partihandel_points_at_the_odoo_page(self):
        action = self.env['partihandel.setup.wizard'].action_open_partihandel('https://app.partihandel.se/')
        self.assertEqual(action['url'], 'https://app.partihandel.se/odoo')
