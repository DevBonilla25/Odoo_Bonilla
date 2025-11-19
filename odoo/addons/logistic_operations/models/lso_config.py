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
    * x_is_logistic_operations: Boolean que indica si esta configuración pertenece a Operaciones Logísticas
    * x_source_module: Selection que indica el módulo de origen ('pos' o 'logistic_operations')

    Propósito:
    ----------
    Permite identificar qué configuraciones de POS fueron creadas desde el módulo
    "Operaciones Logísticas" vs las creadas desde el POS normal. Esto permite:
    - Filtrar configuraciones en vistas específicas
    - Aplicar lógica diferenciada según el origen
    - Mantener separación lógica sin duplicar tablas
    """

    _inherit = 'pos.config'
    _description = 'Point of Sale Configuration - Extended for Operaciones Logísticas'

    # Campo booleano para marcar configuraciones de Operaciones Logísticas
    # Este es el campo principal que usaremos para filtrar
    x_is_logistic_operations = fields.Boolean(
        string='Es Operaciones Logísticas',
        default=False,
        help="Marca si esta configuración pertenece al módulo Operaciones Logísticas",
        copy=True,  # Se copia al duplicar el registro
        index=True,  # Indexado para mejorar el rendimiento en búsquedas
    )

    # Campo de selección alternativo/complementario
    # Útil si en el futuro necesitas más opciones además de 'pos' y 'logistic_operations'
    x_source_module = fields.Selection(
        selection=[
            ('pos', 'Point of Sale'),
            ('logistic_operations', 'Operaciones Logísticas'),
        ],
        string='Módulo de Origen',
        default='pos',
        help="Indica desde qué módulo se creó esta configuración",
        copy=True,
        index=True,
    )

    # Campo para asignar vehículo de flota a la configuración
    x_vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Vehículo Asignado',
        help="Vehículo asignado a esta configuración de Operaciones Logísticas",
        domain="[('active', '=', True)]",  # Solo vehículos activos
        copy=False,  # No copiar al duplicar
    )

    # Campo relacionado para mostrar la placa del vehículo
    x_vehicle_license_plate = fields.Char(
        string='Placa',
        related='x_vehicle_id.license_plate',
        readonly=True,
        store=False,
    )

    @api.model
    def create(self, vals):
        """
        Sobrescribimos el método create para establecer automáticamente
        los campos identificadores cuando se crea una configuración desde
        el contexto de Operaciones Logísticas.

        Funcionamiento:
        ---------------
        Si el contexto contiene 'default_x_is_logistic_operations' = True,
        automáticamente marcamos el registro como perteneciente a Operaciones Logísticas.

        Uso en acciones:
        ----------------
        Las acciones de menú de Operaciones Logísticas deben incluir en su context:
        {'default_x_is_logistic_operations': True, 'default_x_source_module': 'logistic_operations'}
        """
        # Si el contexto indica que viene de Operaciones Logísticas, marcar campos
        if self.env.context.get('default_x_is_logistic_operations'):
            vals['x_is_logistic_operations'] = True
            vals['x_source_module'] = 'logistic_operations'

        return super(PosConfig, self).create(vals)

    def copy(self, default=None):
        """
        Al duplicar una configuración, mantenemos los campos identificadores
        para preservar el origen del registro.
        """
        # El parámetro copy=True en los campos ya maneja esto,
        # pero dejamos este método como referencia para futuras extensiones
        return super(PosConfig, self).copy(default=default)

    def open_logistic_operations_ui(self):
        """
        Abre la interfaz de Operaciones Logísticas.

        Este método reemplaza open_ui() del POS para configuraciones de Operaciones Logísticas.
        Maneja tres escenarios:
        1. Nueva Sesión: Crea sesión y redirige a popup de apertura de caja
        2. Opening Control: Redirige a popup de apertura de caja
        3. Sesión Abierta: Redirige al frontend de LSO

        Retorna:
            dict: Acción de redirección
        """
        self.ensure_one()
        import logging
        _logger = logging.getLogger(__name__)

        # Verificar que sea una configuración de Operaciones Logísticas
        if not self.x_is_logistic_operations:
            from odoo.exceptions import UserError
            raise UserError(_("Esta configuración no pertenece a Operaciones Logísticas"))

        # Escenario 1: No hay sesión actual -> Crear nueva sesión
        if not self.current_session_id:
            # Crear una nueva sesión marcada como Operaciones Logísticas
            # El estado por defecto es 'opening_control' según el modelo base
            session = self.env['pos.session'].create({
                'user_id': self.env.uid,
                'config_id': self.id,
                'x_is_logistic_operations': True,
                'x_source_module': 'logistic_operations',
                'state': 'opening_control',  # Asegurar que el estado sea opening_control
            })

            _logger.info(f"logistic_operations: Nueva sesión creada - ID: {session.id}, Nombre: {session.name}, Estado: {session.state}, Es LSO: {session.x_is_logistic_operations}")

            # Verificar que la sesión se creó correctamente
            if not session.x_is_logistic_operations:
                _logger.error(f"logistic_operations: ERROR - La sesión {session.id} no se marcó como Operaciones Logísticas")
                from odoo.exceptions import UserError
                raise UserError(_("Error al crear la sesión. La sesión no se marcó correctamente como Operaciones Logísticas."))

            # Redirigir a la página de apertura de caja
            return {
                'type': 'ir.actions.act_url',
                'url': f'/logistic_operations/cash_opening?session_id={session.id}',
                'target': 'self',
            }

        # Escenario 2: Sesión en estado opening_control o new_session -> Abrir caja
        elif self.current_session_state in ['opening_control', 'new_session']:
            _logger.info(f"logistic_operations: Sesión existente en estado {self.current_session_state}, redirigiendo a apertura")
            return {
                'type': 'ir.actions.act_url',
                'url': f'/logistic_operations/cash_opening?session_id={self.current_session_id.id}',
                'target': 'self',
            }

        # Escenario 3: Sesión ya abierta -> Ir al frontend
        elif self.current_session_state == 'opened':
            _logger.info(f"logistic_operations: Sesión ya abierta, redirigiendo al frontend")
            return {
                'type': 'ir.actions.act_url',
                'url': f'/logistic_operations/ui?session_id={self.current_session_id.id}',
                'target': 'self',
            }

        else:
            _logger.error(f"logistic_operations: Estado de sesión no válido: {self.current_session_state}")
            from odoo.exceptions import UserError
            raise UserError(_("Estado de sesión no válido: %s") % self.current_session_state)
