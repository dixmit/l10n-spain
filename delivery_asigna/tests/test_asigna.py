# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Copyright 2020 Tecnativa - David Vidal
# Copyright 2021 Tecnativa - Víctor Martínez

from unittest import mock

from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class ZeepClientMock:
    def get_type(self, type_name):
        class EnviosType:
            def __init__(self):
                self.referencia = ""
                self.destinatario = ""
                self.direccion = ""
                self.poblacion = ""
                self.codigoPostal = ""
                self.provincia = ""
                self.pais = ""
                self.telefono = ""
                self.email = ""
                self.bultos = 0
                self.peso = 0.0
                self.volumen = 0.0

        if type_name == "{http://WS/}envio":
            return EnviosType
        raise ValueError("Unknown type")

    class Service:
        def SolicitarEtiqueta(self, cliente, password, referencia):
            return {
                "codError": 0,
                "desError": "OK",
                "etiq": b"%PDF-1.4\n%Mock PDF data for label\n%%EOF",
            }

        def GrabarEnvios(self, cliente, password, envio):
            return {
                "codError": 0,
                "descripcionError": "OK",
                "listaDatosEnvio": [{"referencia": "ASIGNA123456"}],
            }

    def __init__(self, wsdl, transport=None):
        self.service = self.Service()


class TestDeliveryAsigna(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shipping_product = cls.env["product.product"].create(
            {"type": "service", "name": "Test Shipping costs", "list_price": 10.0}
        )
        cls.carrier_asigna = cls.env["delivery.carrier"].create(
            {
                "name": "Asigna",
                "delivery_type": "asigna",
                "product_id": cls.shipping_product.id,
                "prod_environment": False,
                "asigna_api_url": "https://ws.asigna.es:8086/AsignaWS/Ws?wsdl",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"is_storable": True, "name": "Test product"}
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mr. Odoo & Co.",
                "city": "Odoo Ville",
                "zip": "28001",
                "street": "Calle de La Rua, 3",
            }
        )
        order_form = Form(cls.env["sale.order"].with_context(tracking_disable=True))
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line:
            line.product_id = cls.product
            line.product_uom_qty = 20.0
        cls.sale_order = order_form.save()
        cls.sale_order.carrier_id = cls.carrier_asigna.id
        cls.sale_order.action_confirm()
        cls.picking = cls.sale_order.picking_ids
        cls.picking.move_ids.quantity = 20
        cls.picking.number_of_packages = 1

    def test_asigna_picking_confirm(self):
        """The picking is confirm and the shipping is recorded to asigna"""
        # asigna API prevents duplicated references so in order to test we need a
        # unique key that doesn't collide with any CI around, as every test really
        # records an expedition
        with mock.patch("zeep.Client", new=ZeepClientMock):
            self.picking.button_validate()

        self.assertTrue(self.picking.carrier_tracking_ref)
        attachment_count = len(
            self.env["ir.attachment"].search(
                [("res_model", "=", "stock.picking"), ("res_id", "=", self.picking.id)]
            )
        )
        with mock.patch("zeep.Client", new=ZeepClientMock):
            self.picking.button_get_asigna_labels()
        self.assertEqual(
            len(
                self.env["ir.attachment"].search(
                    [
                        ("res_model", "=", "stock.picking"),
                        ("res_id", "=", self.picking.id),
                    ]
                )
            ),
            attachment_count + 1,
        )
        # self.picking.cancel_shipment()
        # self.assertFalse(self.picking.carrier_tracking_ref)
