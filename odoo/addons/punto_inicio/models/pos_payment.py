# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class PosPayment(models.Model):
    """
    Extensión del modelo pos.payment
    =================================

    Este modelo NO crea una nueva tabla. Usa herencia clásica (_inherit)
    para agregar campos adicionales a la tabla 'pos_payment' existente.

    Campos agregados:
    -----------------
    * x_is_punto_inicio: Boolean que indica si este pago pertenece a Punto de Inicio
    * x_source_module: Selection que indica el módulo de origen
    * x_order_is_punto_inicio: Campo relacionado de la orden

    Lógica de marcado:
    ------------------
    Los pagos heredan automáticamente el marcado de su orden (pos_order_id).
    Si la orden es de Punto de Inicio, el pago también lo es.
    """

    _inherit = 'pos.payment'
    _description = 'Point of Sale Payment - Extended for Punto de Inicio'

    # Campo booleano identificador
    x_is_punto_inicio = fields.Boolean(
        string='Es Punto de Inicio',
        default=False,
        help="Marca si este pago pertenece al módulo Punto de Inicio",
        copy=False,
        index=True,
    )

    # Campo de selección para origen
    x_source_module = fields.Selection(
        selection=[
            ('pos', 'Point of Sale'),
            ('punto_inicio', 'Punto de Inicio'),
        ],
        string='Módulo de Origen',
        default='pos',
        help="Indica desde qué módulo se creó este pago",
        copy=False,
        index=True,
    )

    # Campo relacionado de la orden (útil para filtros)
    x_order_is_punto_inicio = fields.Boolean(
        string='Orden es Punto de Inicio',
        related='pos_order_id.x_is_punto_inicio',
        store=True,
        help="Indica si la orden asociada es de Punto de Inicio",
    )

    @api.model
    def create(self, vals):
        """
        Sobrescribimos create para marcar automáticamente los pagos.

        Los pagos SIEMPRE están asociados a una orden (pos_order_id).
        Heredamos el marcado de la orden automáticamente.

        Estrategia:
        -----------
        1. Si pos_order_id está en vals, verificamos si es de Punto de Inicio
        2. Heredamos el marcado de la orden al pago
        """
        # Heredar marcado de la orden
        if 'pos_order_id' in vals:
            order = self.env['pos.order'].browse(vals['pos_order_id'])
            if order.x_is_punto_inicio:
                vals['x_is_punto_inicio'] = True
                vals['x_source_module'] = 'punto_inicio'

        return super(PosPayment, self).create(vals)
