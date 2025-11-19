# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Operaciones Logísticas',
    'version': '1.0.0',
    'category': 'Sales/Point of Sale',
    'sequence': 41,
    'summary': 'Módulo Operaciones Logísticas - Réplica del POS con tablas compartidas',
    'description': """
Operaciones Logísticas - Módulo basado en Point of Sale
=================================================

Este módulo extiende y reutiliza las tablas del módulo Point of Sale (POS)
sin crear nuevas tablas de base de datos.

Características principales:
-----------------------------
* Reutiliza todos los modelos existentes del POS (pos.order, pos.session, pos.config, etc.)
* Agrega campos identificadores para distinguir registros de "Operaciones Logísticas" vs "POS normal"
* Interfaz replicada del POS con menús y vistas propias
* Permite operaciones independientes sin duplicar datos
* Filtrado automático de registros según el módulo de origen

Campos agregados a los modelos POS:
------------------------------------
* x_is_logistic_operations: Campo booleano que marca si el registro proviene de Operaciones Logísticas
* x_source_module: Campo de selección que indica el módulo de origen ('pos' o 'logistic_operations')

Uso:
----
1. Instalar este módulo (depende de point_of_sale)
2. Acceder al menú "Operaciones Logísticas"
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
        'security/logistic_operations_security.xml',
        'security/ir.model.access.csv',

        # Datos - secuencias y configuraciones
        'data/logistic_operations_data.xml',

        # Vistas - heredan y modifican las vistas del POS
        'views/logistic_operations_config_view.xml',
        'views/logistic_operations_session_view.xml',
        'views/logistic_operations_order_view.xml',
        'views/logistic_operations_menu.xml',

        # Assets y templates del frontend
        'views/logistic_operations_assets.xml',
        'views/logistic_operations_templates.xml',

        # Exclusión de datos LSO en Point of Sale - DEBE CARGARSE AL FINAL
        'views/lso_exclusion_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'logistic_operations/static/src/app/cash_opening_popup.js',
            'logistic_operations/static/src/app/logistic_operations_app.js',
            'logistic_operations/static/src/xml/cash_opening_popup.xml',
            'logistic_operations/static/src/xml/logistic_operations_app.xml',
            'logistic_operations/static/src/scss/logistic_operations.scss',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,  # Este módulo aparece como aplicación en el menú de Apps
    'auto_install': False,
    'license': 'LGPL-3',
}
