# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def button_get_asigna_labels(self):
        for picking in self:
            if (
                picking.carrier_id.delivery_type != "asigna"
                or not picking.carrier_tracking_ref
            ):
                continue
            client = picking.carrier_id._asigna_get_client()
            response = client.service.SolicitarEtiqueta(
                cliente=picking.carrier_id.asigna_api_user,
                password=picking.carrier_id.asigna_api_password,
                referencia=picking.carrier_tracking_ref,
            )
            if response["codError"] != 0:
                raise UserError(
                    self.env._(
                        "Asigna API error {}: {}",
                        response["codError"],
                        response["desError"],
                    )
                )
            data = response["etiq"]
            picking.message_post(
                body=_("Asigna shipping label"),
                attachments=[("label.pdf", data)],
            )
