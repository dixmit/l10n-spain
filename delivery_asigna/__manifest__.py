# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Delivery Asigna",
    "summary": """Integrates with Asigna, delivery agency for canary islands""",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "Dixmit,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "depends": [
        "stock_delivery",
        "delivery_package_number",
    ],
    "data": [
        "views/stock_picking.xml",
        "views/delivery_carrier.xml",
    ],
    "external_dependencies": {"python": ["zeep"]},
}
