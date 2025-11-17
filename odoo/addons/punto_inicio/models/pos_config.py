# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class PosConfig(models.Model):
    """
    Extensión del modelo pos.config
    ================================

    Este modelo NO crea una nueva tabla. Usa herencia clásica (_inherit)
    para agregar campos adicionales a la tabla 'pos_config' existente.

    Campos agregados:
    -----------------
    * x_is_punto_inicio: Boolean que indica si esta configuración pertenece a Punto de Inicio
    * x_source_module: Selection que indica el módulo de origen ('pos' o 'punto_inicio')

    Propósito:
    ----------
    Permite identificar qué configuraciones de POS fueron creadas desde el módulo
    "Punto de Inicio" vs las creadas desde el POS normal. Esto permite:
    - Filtrar configuraciones en vistas específicas
    - Aplicar lógica diferenciada según el origen
    - Mantener separación lógica sin duplicar tablas
    """

    _inherit = 'pos.config'
    _description = 'Point of Sale Configuration - Extended for Punto de Inicio'

    # Campo booleano para marcar configuraciones de Punto de Inicio
    # Este es el campo principal que usaremos para filtrar
    x_is_punto_inicio = fields.Boolean(
        string='Es Punto de Inicio',
        default=False,
        help="Marca si esta configuración pertenece al módulo Punto de Inicio",
        copy=True,  # Se copia al duplicar el registro
        index=True,  # Indexado para mejorar el rendimiento en búsquedas
    )

    # Campo de selección alternativo/complementario
    # Útil si en el futuro necesitas más opciones además de 'pos' y 'punto_inicio'
    x_source_module = fields.Selection(
        selection=[
            ('pos', 'Point of Sale'),
            ('punto_inicio', 'Punto de Inicio'),
        ],
        string='Módulo de Origen',
        default='pos',
        help="Indica desde qué módulo se creó esta configuración",
        copy=True,
        index=True,
    )

    @api.model
    def create(self, vals):
        """
        Sobrescribimos el método create para establecer automáticamente
        los campos identificadores cuando se crea una configuración desde
        el contexto de Punto de Inicio.

        Funcionamiento:
        ---------------
        Si el contexto contiene 'default_x_is_punto_inicio' = True,
        automáticamente marcamos el registro como perteneciente a Punto de Inicio.

        Uso en acciones:
        ----------------
        Las acciones de menú de Punto de Inicio deben incluir en su context:
        {'default_x_is_punto_inicio': True, 'default_x_source_module': 'punto_inicio'}
        """
        # Si el contexto indica que viene de Punto de Inicio, marcar campos
        if self.env.context.get('default_x_is_punto_inicio'):
            vals['x_is_punto_inicio'] = True
            vals['x_source_module'] = 'punto_inicio'

        return super(PosConfig, self).create(vals)

    def copy(self, default=None):
        """
        Al duplicar una configuración, mantenemos los campos identificadores
        para preservar el origen del registro.
        """
        # El parámetro copy=True en los campos ya maneja esto,
        # pero dejamos este método como referencia para futuras extensiones
        return super(PosConfig, self).copy(default=default)
