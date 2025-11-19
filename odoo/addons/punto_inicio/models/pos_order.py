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
    * x_is_punto_inicio: Boolean que indica si esta orden pertenece a Punto de Inicio
    * x_source_module: Selection que indica el módulo de origen
    * x_session_is_punto_inicio: Campo relacionado de la sesión
    * x_config_is_punto_inicio: Campo relacionado de la configuración

    Lógica de marcado:
    ------------------
    Las órdenes se marcan automáticamente como 'Punto de Inicio' si:
    1. Se crean desde un contexto con el flag apropiado, O
    2. Se crean desde una sesión (session_id) marcada como Punto de Inicio, O
    3. Se crean desde una configuración marcada como Punto de Inicio

    Este es el modelo más importante porque representa las transacciones reales.
    """

    _inherit = 'pos.order'
    _description = 'Point of Sale Order - Extended for Punto de Inicio'

    # Campo booleano identificador principal
    x_is_punto_inicio = fields.Boolean(
        string='Es Punto de Inicio',
        default=False,
        help="Marca si esta orden pertenece al módulo Punto de Inicio",
        copy=False,  # Las órdenes no se copian normalmente
        index=True,  # Muy importante para reportes y filtros
    )

    # Campo de selección para origen
    x_source_module = fields.Selection(
        selection=[
            ('pos', 'Point of Sale'),
            ('punto_inicio', 'Punto de Inicio'),
        ],
        string='Módulo de Origen',
        default='pos',
        help="Indica desde qué módulo se creó esta orden",
        copy=False,
        index=True,
    )

    # Campos relacionados para facilitar filtros y búsquedas
    x_session_is_punto_inicio = fields.Boolean(
        string='Sesión es Punto de Inicio',
        related='session_id.x_is_punto_inicio',
        store=True,  # Almacenar para mejorar rendimiento
        help="Indica si la sesión asociada es de Punto de Inicio",
    )

    x_config_is_punto_inicio = fields.Boolean(
        string='Config es Punto de Inicio',
        related='config_id.x_is_punto_inicio',
        store=True,
        help="Indica si la configuración asociada es de Punto de Inicio",
    )

    @api.model
    def create(self, vals):
        """
        Sobrescribimos create para marcar automáticamente las órdenes.

        Estrategia de marcado (en orden de prioridad):
        -----------------------------------------------
        1. Contexto explícito: 'default_x_is_punto_inicio': True
        2. Herencia de session_id (si la sesión es de Punto de Inicio)
        3. Herencia de config_id (si la configuración es de Punto de Inicio)

        IMPORTANTE: Este método se llama tanto desde la interfaz web como
        desde las llamadas RPC del POS frontend. El marcado debe ser robusto
        para ambos casos.
        """
        # Prioridad 1: Contexto explícito
        if self.env.context.get('default_x_is_punto_inicio'):
            vals['x_is_punto_inicio'] = True
            vals['x_source_module'] = 'punto_inicio'

        # Prioridad 2: Herencia de la sesión
        elif 'session_id' in vals:
            session = self.env['pos.session'].browse(vals['session_id'])
            if session.x_is_punto_inicio:
                vals['x_is_punto_inicio'] = True
                vals['x_source_module'] = 'punto_inicio'

        # Prioridad 3: Herencia de la configuración (fallback)
        elif 'config_id' in vals:
            config = self.env['pos.config'].browse(vals['config_id'])
            if config.x_is_punto_inicio:
                vals['x_is_punto_inicio'] = True
                vals['x_source_module'] = 'punto_inicio'

        return super(PosOrder, self).create(vals)

    @api.model
    def _order_fields(self, ui_order):
        """
        Sobrescribimos este método que procesa órdenes desde el frontend del POS.

        Este método es llamado cuando el POS envía órdenes desde el navegador.
        Necesitamos asegurar que las órdenes de Punto de Inicio se marquen
        correctamente incluso cuando vienen del frontend.

        Estrategia:
        -----------
        Obtenemos la sesión de la orden y verificamos si es de Punto de Inicio.
        Si es así, agregamos el marcado a los campos de la orden.
        """
        # Llamamos al método padre para obtener los campos base
        order_fields = super(PosOrder, self)._order_fields(ui_order)

        # Verificamos si la sesión es de Punto de Inicio
        if 'session_id' in ui_order:
            session = self.env['pos.session'].browse(ui_order['session_id'])
            if session.x_is_punto_inicio:
                order_fields['x_is_punto_inicio'] = True
                order_fields['x_source_module'] = 'punto_inicio'

        return order_fields

    # MÉTODOS UTILITARIOS PARA REPORTES Y ANÁLISIS
    # ==============================================

    @api.model
    def get_punto_inicio_orders(self, date_from=None, date_to=None):
        """
        Método helper para obtener solo órdenes de Punto de Inicio.

        Útil para:
        - Reportes específicos de Punto de Inicio
        - Dashboard personalizado
        - Análisis de ventas separado

        Parámetros:
        -----------
        date_from: datetime - Fecha inicial (opcional)
        date_to: datetime - Fecha final (opcional)

        Retorna:
        --------
        recordset de pos.order filtrado por Punto de Inicio
        """
        domain = [('x_is_punto_inicio', '=', True)]

        if date_from:
            domain.append(('date_order', '>=', date_from))
        if date_to:
            domain.append(('date_order', '<=', date_to))

        return self.search(domain)

    @api.model
    def get_punto_inicio_stats(self):
        """
        Método helper para obtener estadísticas de Punto de Inicio.

        Retorna un diccionario con:
        - total_orders: Total de órdenes de Punto de Inicio
        - total_amount: Suma total de ventas
        - average_ticket: Ticket promedio

        Útil para dashboard o reportes personalizados.
        """
        orders = self.search([('x_is_punto_inicio', '=', True)])

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
    que pertenecen a órdenes de Punto de Inicio.

    Esto permite filtrar reportes de líneas de venta por módulo.
    """

    _inherit = 'pos.order.line'
    _description = 'Point of Sale Order Line - Extended for Punto de Inicio'

    # Campo relacionado de la orden padre
    x_is_punto_inicio = fields.Boolean(
        string='Es Punto de Inicio',
        related='order_id.x_is_punto_inicio',
        store=True,  # Almacenar para filtros eficientes
        help="Marca si esta línea pertenece a una orden de Punto de Inicio",
    )

    x_source_module = fields.Selection(
        string='Módulo de Origen',
        related='order_id.x_source_module',
        store=True,
        help="Indica desde qué módulo se creó la orden de esta línea",
    )
