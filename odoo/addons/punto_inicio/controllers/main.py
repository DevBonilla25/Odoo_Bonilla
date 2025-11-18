# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request


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
        Muestra la página de apertura de caja.

        Esta página contiene el popup para ingresar el monto inicial
        de efectivo y las notas de apertura.

        Parámetros:
            session_id (int): ID de la sesión a abrir

        Retorna:
            Renderiza la página HTML con el popup de apertura
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

        # Renderizar la página de apertura
        return request.render('punto_inicio.cash_opening_page', {
            'session': session,
            'config': session.config_id,
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