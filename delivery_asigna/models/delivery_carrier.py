# Copyright 2025 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import zeep
from requests import Session
from zeep.transports import Transport

from odoo import fields, models
from odoo.exceptions import UserError


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("asigna", "Asigna")],
        ondelete={"asigna": "set default"},
    )
    asigna_api_url = fields.Char(
        string="URL",
    )
    asigna_api_user = fields.Char(
        string="Username",
    )
    asigna_api_password = fields.Char(
        string="Password",
    )

    def asigna_rate_shipment(self, order):
        """There's no public API so another price method should be used
        Not implemented with GLS-ASM, these values are so it works with websites"""
        return {
            "success": True,
            "price": self.product_id.lst_price,
            "error_message": self.env._(
                """Asigna API doesn't provide methods to compute delivery rates, so
                you should relay on another price method instead or override this
                one in your custom code."""
            ),
            "warning_message": self.env._(
                """Asigna API doesn't provide methods to compute delivery rates, so
                you should relay on another price method instead or override this
                one in your custom code."""
            ),
        }

    def _asigna_get_client(self):
        # TODO: We shouldn't ignore certificate verification, however Asigna
        # uses a self-signed certificate that makes the requests library to
        # raise an error. We are waiting for Asigna to fix this.
        session = Session()
        session.verify = False
        transport = Transport(session=session)
        client = zeep.Client(self.asigna_api_url, transport=transport)
        return client

    def asigna_send_shipping(self, pickings):
        client = self._asigna_get_client()
        envio_type = client.get_type("{http://WS/}envio")
        envios = []
        result = []
        for picking in pickings:
            envio = envio_type()
            # Fill in the envio object with the necessary data from the picking
            # For example:
            envio.albOrd = picking.origin or picking.name
            envio.departamento = "0"
            envio.desCP = picking.partner_id.zip or ""
            envio.desDom = picking.partner_id.street or ""
            envio.desMail = picking.partner_id.email or ""
            envio.desNIF = picking.partner_id.vat or ""
            envio.desNom = picking.partner_id.name or ""
            envio.desTel = picking.partner_id.mobile or picking.partner_id.phone or ""
            # envio.especialHora
            # envio.infoAdicional
            envio.listaBultos = []
            envio.numBultos = picking.number_of_packages or 1
            # envio.numPalets
            envio.obs = ""
            envio.peso = picking.weight
            envio.remB = ""
            envio.remitente = ""
            envio.servicio = ""
            envio.servicioEspecial = ""
            envio.volumen = picking.shipping_volume
            # Add more fields as required by the Asigna API
            envios.append(envio)
            response = client.service.GrabarEnvios(
                cliente=self.asigna_api_user,
                password=self.asigna_api_password,
                envio=envios,
            )
            if response["codError"] != 0:
                raise UserError(
                    self.env._(
                        "Asigna API error %(codError)s: %(desError)s",
                        codError=response["codError"],
                        desError=response["desError"],
                    )
                )
            picking_result = {
                "tracking_number": response["listaDatosEnvio"][0]["referencia"],
                "exact_price": 0,
            }
            result.append(picking_result)
        return result

    def asigna_get_tracking_link(self, picking):
        self.ensure_one()
        return False

    def asigna_cancel_shipment(self, picking):
        self.ensure_one()
        raise Exception(
            "Asigna API doesn't provide methods to cancel shipping requests."
        )
