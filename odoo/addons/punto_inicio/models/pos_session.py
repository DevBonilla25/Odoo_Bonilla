# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class PosSession(models.Model):
    """
    Extensión del modelo pos.session
    =================================

    Este modelo NO crea una nueva tabla. Usa herencia clásica (_inherit)
    para agregar campos adicionales a la tabla 'pos_session' existente.

    Campos agregados:
    -----------------
    * x_is_punto_inicio: Boolean que indica si esta sesión pertenece a Punto de Inicio
    * x_source_module: Selection que indica el módulo de origen
    * x_config_is_punto_inicio: Campo relacionado de la configuración (para filtros)

    Lógica de marcado:
    ------------------
    Las sesiones se marcan automáticamente como 'Punto de Inicio' si:
    1. Se crean desde una acción con el contexto apropiado, O
    2. Se crean desde una configuración (config_id) que ya está marcada como Punto de Inicio
    """

    _inherit = 'pos.session'
    _description = 'Point of Sale Session - Extended for Punto de Inicio'

    # Campo booleano identificador principal
    x_is_punto_inicio = fields.Boolean(
        string='Es Punto de Inicio',
        default=False,
        help="Marca si esta sesión pertenece al módulo Punto de Inicio",
        copy=False,  # Las sesiones normalmente no se copian, pero por seguridad
        index=True,
    )

    # Campo de selección para origen del módulo
    x_source_module = fields.Selection(
        selection=[
            ('pos', 'Point of Sale'),
            ('punto_inicio', 'Punto de Inicio'),
        ],
        string='Módulo de Origen',
        default='pos',
        help="Indica desde qué módulo se creó esta sesión",
        copy=False,
        index=True,
    )

    # Campo relacionado de la configuración (útil para filtros y búsquedas)
    x_config_is_punto_inicio = fields.Boolean(
        string='Config es Punto de Inicio',
        related='config_id.x_is_punto_inicio',
        store=True,  # Lo almacenamos para mejorar rendimiento en búsquedas
        help="Indica si la configuración asociada es de Punto de Inicio",
    )

    @api.model
    def create(self, vals):
        """
        Sobrescribimos create para marcar automáticamente las sesiones.

        Estrategia de marcado (en orden de prioridad):
        -----------------------------------------------
        1. Si el contexto indica explícitamente 'default_x_is_punto_inicio': True
           -> Marcamos como Punto de Inicio

        2. Si no hay contexto pero config_id está en vals, verificamos si esa
           configuración es de Punto de Inicio
           -> Heredamos el marcado de la configuración

        3. Si config_id ya está establecido en self (al crear desde interfaz)
           -> También heredamos el marcado

        Esto garantiza que TODAS las sesiones creadas desde configuraciones
        de Punto de Inicio se marquen correctamente.
        """
        # Opción 1: Contexto explícito
        if self.env.context.get('default_x_is_punto_inicio'):
            vals['x_is_punto_inicio'] = True
            vals['x_source_module'] = 'punto_inicio'
        # Opción 2: Herencia de la configuración (config_id en vals)
        elif 'config_id' in vals:
            config = self.env['pos.config'].browse(vals['config_id'])
            if config.x_is_punto_inicio:
                vals['x_is_punto_inicio'] = True
                vals['x_source_module'] = 'punto_inicio'

        return super(PosSession, self).create(vals)

    def write(self, vals):
        """
        Sobrescribimos write por si se cambia la configuración de una sesión.
        Si se cambia a una config de Punto de Inicio, actualizamos los campos.

        Nota: En la práctica, cambiar config_id de una sesión existente es poco común,
        pero cubrimos este caso para robustez.
        """
        # Si se está cambiando la configuración
        if 'config_id' in vals:
            config = self.env['pos.config'].browse(vals['config_id'])
            if config.x_is_punto_inicio:
                vals['x_is_punto_inicio'] = True
                vals['x_source_module'] = 'punto_inicio'
            else:
                vals['x_is_punto_inicio'] = False
                vals['x_source_module'] = 'pos'

        return super(PosSession, self).write(vals)
