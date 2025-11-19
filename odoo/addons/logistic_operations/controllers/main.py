# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class LogisticOperationsController(http.Controller):
    """
    Controlador HTTP para Operaciones Logísticas
    ======================================

    Maneja las rutas del frontend de Operaciones Logísticas:
    - /logistic_operations/cash_opening: Página de apertura de caja
    - /logistic_operations/ui: Frontend principal de la aplicación
    """

    @http.route('/logistic_operations/cash_opening', type='http', auth='user')
    def cash_opening(self, session_id=None, **kwargs):
        """
        Muestra la página de apertura de sesión.

        Esta página contiene el formulario para ingresar el vehículo,
        el kilometraje inicial y las notas de apertura.

        Parámetros:
            session_id (int): ID de la sesión a abrir

        Retorna:
            Renderiza la página HTML con el formulario de apertura
        """
        if not session_id:
            return request.render('logistic_operations.error_page', {
                'error_title': 'Error',
                'error_message': 'No se proporcionó ID de sesión',
            })

        # Buscar la sesión
        session = request.env['pos.session'].browse(int(session_id))

        _logger.info(f"logistic_operations cash_opening: session_id={session_id}, exists={session.exists()}")

        if not session.exists():
            return request.render('logistic_operations.error_page', {
                'error_title': 'Sesión No Encontrada',
                'error_message': f'La sesión con ID {session_id} no existe',
            })

        _logger.info(f"logistic_operations: Sesión encontrada - ID: {session.id}, Nombre: {session.name}, Estado: {session.state}, Es LSO: {session.x_is_logistic_operations}")

        # Verificar que sea una sesión de Operaciones Logísticas
        if not session.x_is_logistic_operations:
            return request.render('logistic_operations.error_page', {
                'error_title': 'Sesión Inválida',
                'error_message': 'Esta sesión no pertenece a Operaciones Logísticas',
            })

        # Si ya está abierta, redirigir al frontend (evita que el usuario regrese al popup)
        if session.state == 'opened':
            _logger.info(f"logistic_operations: Sesión ya abierta, redirigiendo al frontend")
            return request.redirect(f'/logistic_operations/ui?session_id={session.id}')

        # Si la sesión está cerrada, mostrar error
        if session.state == 'closed':
            return request.render('logistic_operations.error_page', {
                'error_title': 'Sesión Cerrada',
                'error_message': 'Esta sesión ya está cerrada. No se puede abrir nuevamente.',
            })

        # Verificar que la sesión esté en un estado válido para apertura
        if session.state not in ['new_session', 'opening_control']:
            _logger.warning(f"logistic_operations: Estado de sesión inesperado: {session.state}")
            # Intentar renderizar de todas formas si es un estado válido

        # Obtener todos los vehículos activos
        vehicles = request.env['fleet.vehicle'].search([('active', '=', True)])
        _logger.info(f"logistic_operations: Vehículos encontrados: {len(vehicles)}")

        # Obtener el vehículo precargado (si existe)
        vehicle = session.x_vehicle_id or session.config_id.x_vehicle_id
        _logger.info(f"logistic_operations: Vehículo precargado: {vehicle.name if vehicle else 'None'}")

        # Renderizar la página de apertura
        _logger.info(f"logistic_operations: Renderizando página de apertura - Estado: {session.state}")
        return request.render('logistic_operations.cash_opening_page', {
            'session': session,
            'config': session.config_id,
            'vehicles': vehicles,
            'vehicle': vehicle,
        })

    @http.route('/logistic_operations/ui', type='http', auth='user')
    def logistic_operations_ui(self, session_id=None, **kwargs):
        """
        Muestra el frontend principal de Operaciones Logísticas.

        Esta es la interfaz donde los usuarios realizan las operaciones
        después de abrir la sesión.

        Parámetros:
            session_id (int): ID de la sesión activa

        Retorna:
            Renderiza la interfaz principal de Operaciones Logísticas
        """
        if not session_id:
            return request.render('logistic_operations.error_page', {
                'error_title': 'Error',
                'error_message': 'No se proporcionó ID de sesión',
            })

        # Buscar la sesión
        session = request.env['pos.session'].browse(int(session_id))

        if not session.exists():
            return request.render('logistic_operations.error_page', {
                'error_title': 'Sesión No Encontrada',
                'error_message': f'La sesión con ID {session_id} no existe',
            })

        # Verificar que sea una sesión de Operaciones Logísticas
        if not session.x_is_logistic_operations:
            return request.render('logistic_operations.error_page', {
                'error_title': 'Sesión Inválida',
                'error_message': 'Esta sesión no pertenece a Operaciones Logísticas',
            })

        # Si la sesión no está abierta, redirigir a la apertura
        if session.state in ['new_session', 'opening_control']:
            return request.redirect(f'/logistic_operations/cash_opening?session_id={session.id}')

        # Verificar que la sesión esté abierta
        if session.state == 'closed':
            return request.render('logistic_operations.error_page', {
                'error_title': 'Sesión Cerrada',
                'error_message': 'Esta sesión ya está cerrada',
            })

        # Renderizar el frontend principal
        return request.render('logistic_operations.logistic_operations_ui', {
            'session_id': session.id,
            'session': session,
            'config': session.config_id,
        })