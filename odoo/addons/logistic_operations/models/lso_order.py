# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class PosOrder(models.Model):
    """
    Extensión del modelo pos.order
    ===============================

    Este modelo NO crea una nueva tabla. Usa herencia clásica (_inherit)
    para agregar campos adicionales a la tabla 'pos_order' existente.

    Campos agregados:
    -----------------
    * x_is_logistic_operations: Boolean que indica si esta orden pertenece a Operaciones Logísticas
    * x_source_module: Selection que indica el módulo de origen
    * x_session_is_logistic_operations: Campo relacionado de la sesión
    * x_config_is_logistic_operations: Campo relacionado de la configuración

    Lógica de marcado:
    ------------------
    Las órdenes se marcan automáticamente como 'Operaciones Logísticas' si:
    1. Se crean desde un contexto con el flag apropiado, O
    2. Se crean desde una sesión (session_id) marcada como Operaciones Logísticas, O
    3. Se crean desde una configuración marcada como Operaciones Logísticas

    Este es el modelo más importante porque representa las transacciones reales.
    """

    _inherit = 'pos.order'
    _description = 'Point of Sale Order - Extended for Operaciones Logísticas'

    # Campo booleano identificador principal
    x_is_logistic_operations = fields.Boolean(
        string='Es Operaciones Logísticas',
        default=False,
        help="Marca si esta orden pertenece al módulo Operaciones Logísticas",
        copy=False,  # Las órdenes no se copian normalmente
        index=True,  # Muy importante para reportes y filtros
    )

    # Campo de selección para origen
    x_source_module = fields.Selection(
        selection=[
            ('pos', 'Point of Sale'),
            ('logistic_operations', 'Operaciones Logísticas'),
        ],
        string='Módulo de Origen',
        default='pos',
        help="Indica desde qué módulo se creó esta orden",
        copy=False,
        index=True,
    )

    # Campos relacionados para facilitar filtros y búsquedas
    x_session_is_logistic_operations = fields.Boolean(
        string='Sesión es Operaciones Logísticas',
        related='session_id.x_is_logistic_operations',
        store=True,  # Almacenar para mejorar rendimiento
        help="Indica si la sesión asociada es de Operaciones Logísticas",
    )

    x_config_is_logistic_operations = fields.Boolean(
        string='Config es Operaciones Logísticas',
        related='config_id.x_is_logistic_operations',
        store=True,
        help="Indica si la configuración asociada es de Operaciones Logísticas",
    )

    @api.model
    def create(self, vals):
        """
        Sobrescribimos create para marcar automáticamente las órdenes.

        Estrategia de marcado (en orden de prioridad):
        -----------------------------------------------
        1. Contexto explícito: 'default_x_is_logistic_operations': True
        2. Herencia de session_id (si la sesión es de Operaciones Logísticas)
        3. Herencia de config_id (si la configuración es de Operaciones Logísticas)

        IMPORTANTE: Este método se llama tanto desde la interfaz web como
        desde las llamadas RPC del POS frontend. El marcado debe ser robusto
        para ambos casos.
        """
        # Prioridad 1: Contexto explícito
        if self.env.context.get('default_x_is_logistic_operations'):
            vals['x_is_logistic_operations'] = True
            vals['x_source_module'] = 'logistic_operations'

        # Prioridad 2: Herencia de la sesión
        elif 'session_id' in vals:
            session = self.env['pos.session'].browse(vals['session_id'])
            if session.x_is_logistic_operations:
                vals['x_is_logistic_operations'] = True
                vals['x_source_module'] = 'logistic_operations'

        # Prioridad 3: Herencia de la configuración (fallback)
        elif 'config_id' in vals:
            config = self.env['pos.config'].browse(vals['config_id'])
            if config.x_is_logistic_operations:
                vals['x_is_logistic_operations'] = True
                vals['x_source_module'] = 'logistic_operations'

        return super(PosOrder, self).create(vals)

    @api.model
    def _order_fields(self, ui_order):
        """
        Sobrescribimos este método que procesa órdenes desde el frontend del POS.

        Este método es llamado cuando el POS envía órdenes desde el navegador.
        Necesitamos asegurar que las órdenes de Operaciones Logísticas se marquen
        correctamente incluso cuando vienen del frontend.

        Estrategia:
        -----------
        Obtenemos la sesión de la orden y verificamos si es de Operaciones Logísticas.
        Si es así, agregamos el marcado a los campos de la orden.
        """
        # Llamamos al método padre para obtener los campos base
        order_fields = super(PosOrder, self)._order_fields(ui_order)

        # Verificamos si la sesión es de Operaciones Logísticas
        if 'session_id' in ui_order:
            session = self.env['pos.session'].browse(ui_order['session_id'])
            if session.x_is_logistic_operations:
                order_fields['x_is_logistic_operations'] = True
                order_fields['x_source_module'] = 'logistic_operations'

        return order_fields

    # MÉTODOS UTILITARIOS PARA REPORTES Y ANÁLISIS
    # ==============================================

    @api.model
    def get_logistic_operations_orders(self, date_from=None, date_to=None):
        """
        Método helper para obtener solo órdenes de Operaciones Logísticas.

        Útil para:
        - Reportes específicos de Operaciones Logísticas
        - Dashboard personalizado
        - Análisis de ventas separado

        Parámetros:
        -----------
        date_from: datetime - Fecha inicial (opcional)
        date_to: datetime - Fecha final (opcional)

        Retorna:
        --------
        recordset de pos.order filtrado por Operaciones Logísticas
        """
        domain = [('x_is_logistic_operations', '=', True)]

        if date_from:
            domain.append(('date_order', '>=', date_from))
        if date_to:
            domain.append(('date_order', '<=', date_to))

        return self.search(domain)

    @api.model
    def get_logistic_operations_stats(self):
        """
        Método helper para obtener estadísticas de Operaciones Logísticas.

        Retorna un diccionario con:
        - total_orders: Total de órdenes de Operaciones Logísticas
        - total_amount: Suma total de ventas
        - average_ticket: Ticket promedio

        Útil para dashboard o reportes personalizados.
        """
        orders = self.search([('x_is_logistic_operations', '=', True)])

        total_orders = len(orders)
        total_amount = sum(orders.mapped('amount_total'))
        average_ticket = total_amount / total_orders if total_orders > 0 else 0

        return {
            'total_orders': total_orders,
            'total_amount': total_amount,
            'average_ticket': average_ticket,
        }


class PosOrderLine(models.Model):
    """
    Extensión del modelo pos.order.line
    ====================================

    Agregamos campos relacionados para identificar líneas de orden
    que pertenecen a órdenes de Operaciones Logísticas.

    Esto permite filtrar reportes de líneas de venta por módulo.
    """

    _inherit = 'pos.order.line'
    _description = 'Point of Sale Order Line - Extended for Operaciones Logísticas'

    # Campo relacionado de la orden padre
    x_is_logistic_operations = fields.Boolean(
        string='Es Operaciones Logísticas',
        related='order_id.x_is_logistic_operations',
        store=True,  # Almacenar para filtros eficientes
        help="Marca si esta línea pertenece a una orden de Operaciones Logísticas",
    )

    x_source_module = fields.Selection(
        string='Módulo de Origen',
        related='order_id.x_source_module',
        store=True,
        help="Indica desde qué módulo se creó la orden de esta línea",
    )
