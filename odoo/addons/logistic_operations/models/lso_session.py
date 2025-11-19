# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class PosSession(models.Model):
    """Extensión del modelo pos.session para Operaciones Logísticas"""
    
    _inherit = 'pos.session'
    _description = 'Point of Sale Session - Extended for Operaciones Logísticas'

    # Campo booleano identificador principal
    x_is_logistic_operations = fields.Boolean(
        string='Es Operaciones Logísticas',
        default=False,
        help="Marca si esta sesión pertenece al módulo Operaciones Logísticas",
        copy=False,  # Las sesiones normalmente no se copian, pero por seguridad
        index=True,
    )

    # Campo de selección para origen del módulo
    x_source_module = fields.Selection(
        selection=[
            ('pos', 'Point of Sale'),
            ('logistic_operations', 'Operaciones Logísticas'),
        ],
        string='Módulo de Origen',
        default='pos',
        help="Indica desde qué módulo se creó esta sesión",
        copy=False,
        index=True,
    )

    # Campo relacionado de la configuración (útil para filtros y búsquedas)
    x_config_is_logistic_operations = fields.Boolean(
        string='Config es Operaciones Logísticas',
        related='config_id.x_is_logistic_operations',
        store=True,  # Lo almacenamos para mejorar rendimiento en búsquedas
        help="Indica si la configuración asociada es de Operaciones Logísticas",
    )

    # Campos para gestión de vehículo y kilometraje
    x_vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Vehículo',
        help="Vehículo utilizado en esta sesión",
        domain="[('active', '=', True)]",
        copy=False,
    )

    x_odometer_start = fields.Float(
        string='Kilometraje Inicial',
        help="Lectura del odómetro al iniciar la sesión",
        digits=(10, 2),  # Permite hasta 2 decimales
        copy=False,
    )

    x_odometer_end = fields.Float(
        string='Kilometraje Final',
        help="Lectura del odómetro al finalizar la sesión",
        digits=(10, 2),
        copy=False,
    )

    x_odometer_difference = fields.Float(
        string='Kilómetros Recorridos',
        compute='_compute_odometer_difference',
        store=True,
        digits=(10, 2),
        help="Diferencia entre kilometraje final e inicial",
    )

    x_session_notes = fields.Text(
        string='Notas de Sesión',
        help="Observaciones o comentarios sobre la sesión",
        copy=False,
    )

    @api.depends('x_odometer_start', 'x_odometer_end')
    def _compute_odometer_difference(self):
        """
        Calcula los kilómetros recorridos durante la sesión.
        """
        for session in self:
            if session.x_odometer_end and session.x_odometer_start:
                session.x_odometer_difference = session.x_odometer_end - session.x_odometer_start
            else:
                session.x_odometer_difference = 0.0

    @api.model_create_multi
    def create(self, vals_list):
        """
        Marca automáticamente las sesiones de Operaciones Logísticas.
        Si no tiene vehículo/kilometraje, mantiene el estado en 'opening_control' para mostrar el popup.
        """
        for vals in vals_list:
            # Opción 1: Contexto explícito
            if self.env.context.get('default_x_is_logistic_operations'):
                vals['x_is_logistic_operations'] = True
                vals['x_source_module'] = 'logistic_operations'
            # Opción 2: Herencia de la configuración (config_id en vals)
            elif 'config_id' in vals:
                config = self.env['pos.config'].browse(vals['config_id'])
                if config.x_is_logistic_operations:
                    vals['x_is_logistic_operations'] = True
                    vals['x_source_module'] = 'logistic_operations'

                    # Precargar vehículo de la configuración si existe
                    if config.x_vehicle_id and 'x_vehicle_id' not in vals:
                        vals['x_vehicle_id'] = config.x_vehicle_id.id

        # Crear las sesiones (el método base llamará automáticamente a action_pos_session_open())
        sessions = super(PosSession, self).create(vals_list)

        # Después de la creación, verificar sesiones de Operaciones Logísticas
        for session in sessions:
            if session.x_is_logistic_operations:
                # Si es de Operaciones Logísticas, cambiar el nombre de la sesión para usar el prefijo PID
                if session.name.startswith('POS/'):
                    new_name = self.env['ir.sequence'].next_by_code('pid.session')
                    if new_name:
                        session.write({'name': new_name})
                
                # SOLUCIÓN SENCILLA: Si no tiene vehículo/kilometraje, forzar estado a 'opening_control'
                # Esto evita que se abra automáticamente sin pasar por el popup
                if session.state == 'opened' and not (session.x_vehicle_id and session.x_odometer_start):
                    session.write({'state': 'opening_control'})

        return sessions

    def write(self, vals):
        """Actualiza los campos si se cambia la configuración de una sesión"""
        if 'config_id' in vals:
            config = self.env['pos.config'].browse(vals['config_id'])
            if config.x_is_logistic_operations:
                vals['x_is_logistic_operations'] = True
                vals['x_source_module'] = 'logistic_operations'
            else:
                vals['x_is_logistic_operations'] = False
                vals['x_source_module'] = 'pos'

        return super(PosSession, self).write(vals)

    def action_open_logistic_operations_session(self):
        """
        Abre una sesión de Operaciones Logísticas mostrando el popup de apertura de caja.

        Este método se llama desde la vista kanban cuando el usuario hace clic
        en "Abrir Sesión" desde una configuración de Operaciones Logísticas.

        Retorna:
            dict: Acción que redirige a la página de apertura de caja
        """
        self.ensure_one()

        # Verificar que la sesión sea de Operaciones Logísticas
        if not self.x_is_logistic_operations:
            from odoo.exceptions import UserError
            raise UserError(_("Esta sesión no pertenece a Operaciones Logísticas"))

        # Verificar que la sesión no esté ya abierta
        if self.state != 'new_session':
            from odoo.exceptions import UserError
            raise UserError(_("Esta sesión ya está abierta o cerrada"))

        # Redirigir a la página de apertura de caja
        return {
            'type': 'ir.actions.act_url',
            'url': f'/logistic_operations/cash_opening?session_id={self.id}',
            'target': 'self',
        }

    def set_vehicle_opening(self, vehicle_id, odometer_start, notes=''):
        """
        Establece el vehículo y kilometraje inicial al abrir la sesión.

        Este método se llama desde el frontend cuando el conductor ingresa
        los datos del vehículo en el popup de apertura.

        Parámetros:
            vehicle_id (int): ID del vehículo seleccionado
            odometer_start (float): Lectura inicial del odómetro
            notes (str): Notas u observaciones de inicio
        """
        self.ensure_one()

        # Validar que se proporcionen los datos requeridos
        if not vehicle_id:
            from odoo.exceptions import UserError
            raise UserError(_("Debe seleccionar un vehículo"))

        if not odometer_start or odometer_start <= 0:
            from odoo.exceptions import UserError
            raise UserError(_("Debe ingresar el kilometraje inicial del vehículo"))

        # Actualizar los datos del vehículo
        self.write({
            'x_vehicle_id': vehicle_id,
            'x_odometer_start': odometer_start,
            'x_session_notes': notes or '',
        })

        # Registrar en el chatter
        vehicle = self.env['fleet.vehicle'].browse(vehicle_id)
        self.message_post(
            body=_("Inicio de sesión<br/>Vehículo: %s<br/>Kilometraje inicial: %.2f km<br/>Notas: %s") % (
                vehicle.name, odometer_start, notes or 'N/A'
            ),
            subject=_("Inicio de Sesión"),
        )

        # Cambiar el estado a 'opened'
        self.action_pos_session_open()

        return True

    def set_vehicle_closing(self, odometer_end, notes=''):
        """
        Establece el kilometraje final y notas de cierre.

        Este método se llama desde el frontend cuando el conductor ingresa
        el kilometraje final en el popup de cierre.

        Parámetros:
            odometer_end (float): Lectura final del odómetro
            notes (str): Notas u observaciones de cierre
        """
        self.ensure_one()

        # Verificar que la sesión esté abierta
        if self.state != 'opened':
            from odoo.exceptions import UserError
            raise UserError(_("Solo se pueden cerrar sesiones que estén abiertas"))

        # Validar kilometraje final
        if not odometer_end or odometer_end <= 0:
            from odoo.exceptions import UserError
            raise UserError(_("Debe ingresar el kilometraje final del vehículo"))

        if odometer_end < self.x_odometer_start:
            from odoo.exceptions import UserError
            raise UserError(_("El kilometraje final no puede ser menor al inicial"))

        # Actualizar el kilometraje final
        self.write({
            'x_odometer_end': odometer_end,
        })

        # Agregar notas si se proporcionan
        if notes:
            current_notes = self.x_session_notes or ''
            self.write({
                'x_session_notes': current_notes + '\n\n--- Cierre de Sesión ---\n' + notes
            })

        # Calcular kilómetros recorridos
        km_recorridos = odometer_end - self.x_odometer_start

        # Registrar en el chatter
        self.message_post(
            body=_("Cierre de sesión<br/>Vehículo: %s<br/>Kilometraje final: %.2f km<br/>Kilómetros recorridos: %.2f km<br/>Notas: %s") % (
                self.x_vehicle_id.name, odometer_end, km_recorridos, notes or 'N/A'
            ),
            subject=_("Cierre de Sesión"),
        )

        return True
