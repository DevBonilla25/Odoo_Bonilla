# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class PuntoInicioController(http.Controller):
    """
    Controlador HTTP para Punto de Inicio
    ======================================

    Maneja las rutas del frontend de Punto de Inicio:
    - /punto_inicio/cash_opening: Página de apertura de caja
    - /punto_inicio/ui: Frontend principal de la aplicación
    """

    @http.route('/punto_inicio/cash_opening', type='http', auth='user')
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
            return request.render('punto_inicio.error_page', {
                'error_title': 'Error',
                'error_message': 'No se proporcionó ID de sesión',
            })

        # Buscar la sesión
        session = request.env['pos.session'].browse(int(session_id))

        _logger.info(f"PUNTO_INICIO cash_opening: session_id={session_id}, exists={session.exists()}")

        if not session.exists():
            return request.render('punto_inicio.error_page', {
                'error_title': 'Sesión No Encontrada',
                'error_message': f'La sesión con ID {session_id} no existe',
            })

        _logger.info(f"PUNTO_INICIO: Sesión encontrada - ID: {session.id}, Nombre: {session.name}, Estado: {session.state}, Es PI: {session.x_is_punto_inicio}")

        # Verificar que sea una sesión de Punto de Inicio
        if not session.x_is_punto_inicio:
            return request.render('punto_inicio.error_page', {
                'error_title': 'Sesión Inválida',
                'error_message': 'Esta sesión no pertenece a Punto de Inicio',
            })

        # Si ya está abierta, redirigir al frontend (evita que el usuario regrese al popup)
        if session.state == 'opened':
            _logger.info(f"PUNTO_INICIO: Sesión ya abierta, redirigiendo al frontend")
            return request.redirect(f'/punto_inicio/ui?session_id={session.id}')

        # Si la sesión está cerrada, mostrar error
        if session.state == 'closed':
            return request.render('punto_inicio.error_page', {
                'error_title': 'Sesión Cerrada',
                'error_message': 'Esta sesión ya está cerrada. No se puede abrir nuevamente.',
            })

        # Verificar que la sesión esté en un estado válido para apertura
        if session.state not in ['new_session', 'opening_control']:
            _logger.warning(f"PUNTO_INICIO: Estado de sesión inesperado: {session.state}")
            # Intentar renderizar de todas formas si es un estado válido

        # Obtener todos los vehículos activos
        vehicles = request.env['fleet.vehicle'].search([('active', '=', True)])
        _logger.info(f"PUNTO_INICIO: Vehículos encontrados: {len(vehicles)}")

        # Obtener el vehículo precargado (si existe)
        vehicle = session.x_vehicle_id or session.config_id.x_vehicle_id
        _logger.info(f"PUNTO_INICIO: Vehículo precargado: {vehicle.name if vehicle else 'None'}")

        # Renderizar la página de apertura
        _logger.info(f"PUNTO_INICIO: Renderizando página de apertura - Estado: {session.state}")
        return request.render('punto_inicio.cash_opening_page', {
            'session': session,
            'config': session.config_id,
            'vehicles': vehicles,
            'vehicle': vehicle,
        })

    @http.route('/punto_inicio/ui', type='http', auth='user')
    def punto_inicio_ui(self, session_id=None, **kwargs):
        """
        Muestra el frontend principal de Punto de Inicio.

        Esta es la interfaz donde los usuarios realizan las operaciones
        después de abrir la sesión.

        Parámetros:
            session_id (int): ID de la sesión activa

        Retorna:
            Renderiza la interfaz principal de Punto de Inicio
        """
        if not session_id:
            return request.render('punto_inicio.error_page', {
                'error_title': 'Error',
                'error_message': 'No se proporcionó ID de sesión',
            })

        # Buscar la sesión
        session = request.env['pos.session'].browse(int(session_id))

        if not session.exists():
            return request.render('punto_inicio.error_page', {
                'error_title': 'Sesión No Encontrada',
                'error_message': f'La sesión con ID {session_id} no existe',
            })

        # Verificar que sea una sesión de Punto de Inicio
        if not session.x_is_punto_inicio:
            return request.render('punto_inicio.error_page', {
                'error_title': 'Sesión Inválida',
                'error_message': 'Esta sesión no pertenece a Punto de Inicio',
            })

        # Si la sesión no está abierta, redirigir a la apertura
        if session.state in ['new_session', 'opening_control']:
            return request.redirect(f'/punto_inicio/cash_opening?session_id={session.id}')

        # Verificar que la sesión esté abierta
        if session.state == 'closed':
            return request.render('punto_inicio.error_page', {
                'error_title': 'Sesión Cerrada',
                'error_message': 'Esta sesión ya está cerrada',
            })

        # Renderizar el frontend principal
        return request.render('punto_inicio.punto_inicio_ui', {
            'session_id': session.id,
            'session': session,
            'config': session.config_id,
        })