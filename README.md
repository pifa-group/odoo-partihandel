# Partihandel Connector for Odoo

Connects an Odoo database to [Partihandel](https://partihandel.se), the order and warehouse system
for wholesalers, in one step. Requires a Partihandel account. The module itself is free.

## What it does

- Adds **Settings > Partihandel**, with your Partihandel address and a **Connect to Partihandel**
  button.
- Creates a dedicated user, **Partihandel Integration**, with only the access the integration
  needs: create and update contacts and products, and create and post customer invoices. It is not
  an administrator and cannot log in to the web client.
- Issues an API key for that user and shows the four values to paste into Partihandel. Running the
  setup again replaces the key.

Your Odoo must be reachable over https. The integration user is an internal user, so on a paid
Odoo plan it counts as one user.

## Install

Install **Partihandel Connector** from the Odoo Apps store, or add this repository's branch for
your Odoo version (`18.0`, `19.0`) to your addons path and install `partihandel_connector`.

## Support

support@partihandel.se

## License

LGPL-3. See [LICENSE](LICENSE).

This repository is published from the Partihandel source tree; please send changes to
support@partihandel.se rather than opening pull requests here.
