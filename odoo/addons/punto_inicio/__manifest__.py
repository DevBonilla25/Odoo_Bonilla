# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Punto de Inicio',
    'version': '1.0.0',
    'category': 'Sales/Point of Sale',
    'sequence': 41,
    'summary': 'Módulo Punto de Inicio - Réplica del POS con tablas compartidas',
    'description': """
Punto de Inicio - Módulo basado en Point of Sale
=================================================

Este módulo extiende y reutiliza las tablas del módulo Point of Sale (POS)
sin crear nuevas tablas de base de datos.

Características principales:
-----------------------------
* Reutiliza todos los modelos existentes del POS (pos.order, pos.session, pos.config, etc.)
* Agrega campos identificadores para distinguir registros de "Punto de Inicio" vs "POS normal"
* Interfaz replicada del POS con menús y vistas propias
* Permite operaciones independientes sin duplicar datos
* Filtrado automático de registros según el módulo de origen

Campos agregados a los modelos POS:
------------------------------------
* x_is_punto_inicio: Campo booleano que marca si el registro proviene de Punto de Inicio
* x_source_module: Campo de selección que indica el módulo de origen ('pos' o 'punto_inicio')

Uso:
----
1. Instalar este módulo (depende de point_of_sale)
2. Acceder al menú "Punto de Inicio"
3. Las órdenes, sesiones y configuraciones creadas desde aquí se marcarán automáticamente
4. Los registros se comparten con POS pero pueden filtrarse según origen
    """,
    'author': 'Bonilla',
    'website': 'https://www.bonilla.com',
    'depends': [
        'point_of_sale',  # Dependencia crítica - reutilizamos sus modelos
        'fleet',          # Para integración con gestión de vehículos
    ],
    'data': [
        # Seguridad - debe cargarse primero
        'security/punto_inicio_security.xml',
        'security/ir.model.access.csv',

        # Datos - secuencias y configuraciones
        'data/punto_inicio_data.xml',

        # Vistas - heredan y modifican las vistas del POS
        'views/punto_inicio_config_view.xml',
        'views/punto_inicio_session_view.xml',
        'views/punto_inicio_order_view.xml',
        'views/punto_inicio_menu.xml',

        # Assets y templates del frontend
        'views/punto_inicio_assets.xml',
        'views/punto_inicio_templates.xml',

        # Exclusión de datos PI en Point of Sale - DEBE CARGARSE AL FINAL
        'views/pos_exclusion_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'punto_inicio/static/src/app/cash_opening_popup.js',
            'punto_inicio/static/src/app/punto_inicio_app.js',
            'punto_inicio/static/src/xml/cash_opening_popup.xml',
            'punto_inicio/static/src/xml/punto_inicio_app.xml',
            'punto_inicio/static/src/scss/punto_inicio.scss',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,  # Este módulo aparece como aplicación en el menú de Apps
    'auto_install': False,
    'license': 'LGPL-3',
}
