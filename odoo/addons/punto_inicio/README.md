# Módulo Punto de Inicio para Odoo 17

## 📋 Descripción

**Punto de Inicio** es un módulo para Odoo 17 que replica la funcionalidad del **Point of Sale (POS)** oficial, pero **reutilizando las mismas tablas de base de datos** existentes.

### ✨ Características Principales

- ✅ **NO crea nuevas tablas**: Extiende los modelos existentes del POS
- ✅ **Interfaz idéntica**: Réplica fiel del POS para una curva de aprendizaje mínima
- ✅ **Campos identificadores**: Marca automáticamente todos los registros según su origen
- ✅ **Filtrado automático**: Las vistas muestran solo los registros relevantes
- ✅ **Preparado para el futuro**: Fácil de extender con funcionalidades específicas
- ✅ **Grupos de seguridad propios**: Control de acceso independiente del POS

---

## 🏗️ Arquitectura del Módulo

### Modelos Extendidos

El módulo extiende los siguientes modelos del POS sin crear nuevas tablas:

| Modelo Original | Archivo de Extensión | Campos Agregados |
|----------------|---------------------|------------------|
| `pos.config` | `models/pos_config.py` | `x_is_punto_inicio`, `x_source_module` |
| `pos.session` | `models/pos_session.py` | `x_is_punto_inicio`, `x_source_module`, `x_config_is_punto_inicio` |
| `pos.order` | `models/pos_order.py` | `x_is_punto_inicio`, `x_source_module`, `x_session_is_punto_inicio`, `x_config_is_punto_inicio` |
| `pos.payment` | `models/pos_payment.py` | `x_is_punto_inicio`, `x_source_module`, `x_order_is_punto_inicio` |

### Campos Identificadores

Todos los modelos extendidos incluyen estos campos:

#### `x_is_punto_inicio` (Boolean)
- **Propósito**: Campo principal para identificar registros de Punto de Inicio
- **Indexado**: Sí (para mejor rendimiento en búsquedas)
- **Valor por defecto**: `False`

#### `x_source_module` (Selection)
- **Propósito**: Identificador más descriptivo del módulo de origen
- **Opciones**:
  - `'pos'`: Point of Sale normal
  - `'punto_inicio'`: Punto de Inicio
- **Indexado**: Sí
- **Valor por defecto**: `'pos'`

#### Campos relacionados (computed/stored)
- `x_config_is_punto_inicio`: Indica si la configuración asociada es de PI
- `x_session_is_punto_inicio`: Indica si la sesión asociada es de PI
- `x_order_is_punto_inicio`: Indica si la orden asociada es de PI

---

## 🔄 Lógica de Marcado Automático

### Estrategia de Herencia en Cascada

Los registros se marcan automáticamente siguiendo esta jerarquía:

```
pos.config (x_is_punto_inicio = True)
    ↓ hereda
pos.session (automáticamente marcada)
    ↓ hereda
pos.order (automáticamente marcada)
    ↓ hereda
pos.payment (automáticamente marcada)
```

### Métodos `create()` Sobrescritos

Cada modelo sobrescribe el método `create()` para implementar el marcado:

#### 1. **pos.config** ([models/pos_config.py:52](odoo/addons/punto_inicio/models/pos_config.py#L52))
```python
@api.model
def create(self, vals):
    if self.env.context.get('default_x_is_punto_inicio'):
        vals['x_is_punto_inicio'] = True
        vals['x_source_module'] = 'punto_inicio'
    return super(PosConfig, self).create(vals)
```

#### 2. **pos.session** ([models/pos_session.py:69](odoo/addons/punto_inicio/models/pos_session.py#L69))
```python
@api.model
def create(self, vals):
    # Prioridad 1: Contexto explícito
    if self.env.context.get('default_x_is_punto_inicio'):
        vals['x_is_punto_inicio'] = True
        vals['x_source_module'] = 'punto_inicio'
    # Prioridad 2: Herencia de config_id
    elif 'config_id' in vals:
        config = self.env['pos.config'].browse(vals['config_id'])
        if config.x_is_punto_inicio:
            vals['x_is_punto_inicio'] = True
            vals['x_source_module'] = 'punto_inicio'
    return super(PosSession, self).create(vals)
```

#### 3. **pos.order** ([models/pos_order.py:99](odoo/addons/punto_inicio/models/pos_order.py#L99))
```python
@api.model
def create(self, vals):
    # Prioridad 1: Contexto
    if self.env.context.get('default_x_is_punto_inicio'):
        vals['x_is_punto_inicio'] = True
        vals['x_source_module'] = 'punto_inicio'
    # Prioridad 2: Herencia de session_id
    elif 'session_id' in vals:
        session = self.env['pos.session'].browse(vals['session_id'])
        if session.x_is_punto_inicio:
            vals['x_is_punto_inicio'] = True
            vals['x_source_module'] = 'punto_inicio'
    # Prioridad 3: Herencia de config_id
    elif 'config_id' in vals:
        config = self.env['pos.config'].browse(vals['config_id'])
        if config.x_is_punto_inicio:
            vals['x_is_punto_inicio'] = True
            vals['x_source_module'] = 'punto_inicio'
    return super(PosOrder, self).create(vals)
```

#### 4. **pos.payment** ([models/pos_payment.py:48](odoo/addons/punto_inicio/models/pos_payment.py#L48))
```python
@api.model
def create(self, vals):
    if 'pos_order_id' in vals:
        order = self.env['pos.order'].browse(vals['pos_order_id'])
        if order.x_is_punto_inicio:
            vals['x_is_punto_inicio'] = True
            vals['x_source_module'] = 'punto_inicio'
    return super(PosPayment, self).create(vals)
```

### Uso de Contextos en Acciones

Todas las acciones de Punto de Inicio incluyen el contexto apropiado:

```xml
<field name="context">{
    'default_x_is_punto_inicio': True,
    'default_x_source_module': 'punto_inicio',
}</field>
```

Esto garantiza que cualquier registro creado desde estas acciones se marque automáticamente.

---

## 🔒 Seguridad y Permisos

### Grupos de Seguridad

El módulo define dos grupos principales:

#### 1. `group_punto_inicio_user` ([security/punto_inicio_security.xml:28](odoo/addons/punto_inicio/security/punto_inicio_security.xml#L28))
- **Permisos**:
  - Abrir/cerrar sesiones
  - Crear órdenes
  - Ver sus propias sesiones y órdenes
- **Hereda**: `point_of_sale.group_pos_user`

#### 2. `group_punto_inicio_manager` ([security/punto_inicio_security.xml:45](odoo/addons/punto_inicio/security/punto_inicio_security.xml#L45))
- **Permisos**:
  - Todo lo del usuario
  - Configurar puntos de venta
  - Ver todas las sesiones/órdenes
  - Acceso a reportes
  - Cerrar sesiones de otros usuarios
- **Hereda**: `group_punto_inicio_user` + `point_of_sale.group_pos_manager`

### Control de Acceso a Modelos

Definido en [security/ir.model.access.csv](odoo/addons/punto_inicio/security/ir.model.access.csv):

| Modelo | Usuario | Manager |
|--------|---------|---------|
| `pos.config` | Leer/Escribir | Todos los permisos |
| `pos.session` | Leer/Escribir/Crear | Todos los permisos |
| `pos.order` | Leer/Escribir/Crear | Todos los permisos |
| `pos.payment` | Leer/Escribir/Crear | Todos los permisos |

### Reglas de Registro (Record Rules)

**IMPORTANTE**: Las reglas de registro están **comentadas** por defecto en [security/punto_inicio_security.xml](odoo/addons/punto_inicio/security/punto_inicio_security.xml).

Si quieres separación estricta entre POS y Punto de Inicio, descomenta las reglas en el archivo XML.

**Ventajas de activar las reglas**:
- Mayor seguridad y separación de datos
- Usuarios solo ven registros de "su" módulo

**Desventajas de activar las reglas**:
- Managers que necesitan ver ambos módulos necesitarían ambos grupos
- Mayor complejidad administrativa

---

## 📂 Estructura de Archivos

```
punto_inicio/
├── __init__.py                          # Importa models
├── __manifest__.py                      # Manifiesto del módulo
├── README.md                            # Este archivo
│
├── models/                              # Modelos extendidos
│   ├── __init__.py                      # Importa todos los modelos
│   ├── pos_config.py                    # Extensión de pos.config
│   ├── pos_session.py                   # Extensión de pos.session
│   ├── pos_order.py                     # Extensión de pos.order
│   └── pos_payment.py                   # Extensión de pos.payment
│
├── security/                            # Seguridad y permisos
│   ├── punto_inicio_security.xml        # Grupos y reglas
│   └── ir.model.access.csv              # Control de acceso a modelos
│
├── views/                               # Vistas y menús
│   ├── punto_inicio_config_view.xml     # Vistas de configuración
│   ├── punto_inicio_session_view.xml    # Vistas de sesión
│   ├── punto_inicio_order_view.xml      # Vistas de órdenes
│   └── punto_inicio_menu.xml            # Menús principales
│
└── static/                              # Recursos estáticos
    └── description/
        ├── index.html                   # Descripción del módulo
        └── icon.png                     # Ícono del módulo (a crear)
```

---

## 🚀 Instalación y Uso

### 1. Instalación

1. **Requisito previo**: Asegúrate de tener instalado el módulo `point_of_sale`

2. **Actualizar la lista de aplicaciones**:
   ```bash
   # Desde línea de comandos
   ./odoo-bin -u punto_inicio -d tu_base_de_datos

   # O desde la interfaz web:
   # Apps > Actualizar Lista de Aplicaciones
   ```

3. **Instalar el módulo**:
   - Ve a `Apps`
   - Busca "Punto de Inicio"
   - Haz clic en `Instalar`

### 2. Configuración Inicial

1. **Asignar permisos**:
   - Ve a `Ajustes > Usuarios y Compañías > Usuarios`
   - Selecciona un usuario
   - En la pestaña de `Permisos`, asigna:
     - `Usuario Punto de Inicio` (para usuarios normales)
     - `Manager Punto de Inicio` (para administradores)

2. **Crear primera configuración**:
   - Ve a `Punto de Inicio > Configuración > Puntos de Venta`
   - Haz clic en `Crear`
   - Configura igual que un POS normal (almacén, diario, métodos de pago, etc.)
   - Guarda

3. **Abrir sesión**:
   - Ve a `Punto de Inicio > Dashboard`
   - Selecciona tu configuración
   - Abre una nueva sesión
   - ¡Empieza a vender!

### 3. Uso Diario

El flujo de trabajo es **idéntico** al del Point of Sale normal:

1. **Abrir sesión**: `Punto de Inicio > Dashboard > Nueva Sesión`
2. **Procesar ventas**: Igual que en POS
3. **Cerrar sesión**: `Punto de Inicio > Sesiones > Cerrar Sesión`
4. **Ver órdenes**: `Punto de Inicio > Órdenes > Órdenes`
5. **Análisis**: `Punto de Inicio > Órdenes > Análisis de Órdenes`

---

## 🔍 Verificación del Marcado

### Desde la Interfaz

Para verificar que los registros se están marcando correctamente:

1. **Ver campo en formularios**:
   - Abre cualquier orden de Punto de Inicio
   - Ve a la pestaña/grupo "Información del Módulo"
   - Verifica que `x_is_punto_inicio = True`

2. **Usar filtros en búsqueda**:
   - En la vista de lista de órdenes
   - Usa el filtro "Órdenes Punto de Inicio"
   - Deberías ver solo tus órdenes

### Desde Base de Datos

```sql
-- Ver órdenes de Punto de Inicio
SELECT id, name, x_is_punto_inicio, x_source_module
FROM pos_order
WHERE x_is_punto_inicio = true;

-- Ver sesiones de Punto de Inicio
SELECT id, name, x_is_punto_inicio, x_source_module
FROM pos_session
WHERE x_is_punto_inicio = true;

-- Ver configuraciones de Punto de Inicio
SELECT id, name, x_is_punto_inicio, x_source_module
FROM pos_config
WHERE x_is_punto_inicio = true;
```

### Desde Python Shell

```python
# Iniciar shell de Odoo
./odoo-bin shell -d tu_base_de_datos

# En el shell:
# Ver órdenes de Punto de Inicio
pi_orders = env['pos.order'].search([('x_is_punto_inicio', '=', True)])
print(f"Total órdenes PI: {len(pi_orders)}")

# Ver sesiones de Punto de Inicio
pi_sessions = env['pos.session'].search([('x_is_punto_inicio', '=', True)])
print(f"Total sesiones PI: {len(pi_sessions)}")

# Ver estadísticas
stats = env['pos.order'].get_punto_inicio_stats()
print(stats)
```

---

## 🛠️ Extensión y Personalización

### Agregar Campos Personalizados

Si necesitas agregar más campos específicos:

```python
# En models/pos_order.py

class PosOrder(models.Model):
    _inherit = 'pos.order'

    # Tu campo personalizado
    x_campo_custom = fields.Char(
        string='Campo Custom',
        help="Descripción del campo"
    )
```

### Modificar Lógica de Marcado

Para cambiar cuándo/cómo se marcan los registros:

```python
# En models/pos_order.py

@api.model
def create(self, vals):
    # Tu lógica personalizada aquí
    # Por ejemplo, marcar solo si cumple ciertas condiciones

    if self.env.context.get('custom_condition'):
        vals['x_is_punto_inicio'] = True

    return super(PosOrder, self).create(vals)
```

### Crear Reportes Personalizados

```xml
<!-- En un nuevo archivo views/punto_inicio_reports.xml -->

<record id="action_punto_inicio_custom_report" model="ir.actions.act_window">
    <field name="name">Reporte Personalizado PI</field>
    <field name="res_model">pos.order</field>
    <field name="view_mode">pivot,graph,tree</field>
    <field name="domain">[('x_is_punto_inicio', '=', True)]</field>
    <field name="context">{
        'pivot_measures': ['amount_total'],
        'pivot_row_groupby': ['date_order:month'],
    }</field>
</record>
```

### Agregar Validaciones Específicas

```python
# En models/pos_order.py

from odoo.exceptions import ValidationError

@api.constrains('x_is_punto_inicio', 'partner_id')
def _check_punto_inicio_partner(self):
    for order in self:
        if order.x_is_punto_inicio and not order.partner_id:
            raise ValidationError(
                "Las órdenes de Punto de Inicio requieren un cliente"
            )
```

---

## 🐛 Troubleshooting

### Problema: Los registros no se marcan automáticamente

**Posibles causas**:
1. El contexto no se está pasando correctamente en las acciones
2. Los métodos `create()` fueron sobrescritos por otro módulo

**Solución**:
```python
# Verificar en shell
env['pos.order'].with_context(
    default_x_is_punto_inicio=True
).create({
    'session_id': session_id,
    # ... otros campos
})
```

### Problema: No veo el menú de Punto de Inicio

**Posibles causas**:
1. El usuario no tiene los permisos correctos
2. El módulo no se instaló correctamente

**Solución**:
1. Verificar grupos: `Ajustes > Usuarios > Permisos`
2. Reinstalar: `Apps > Punto de Inicio > Desinstalar > Instalar`

### Problema: Las vistas muestran registros del POS normal

**Posibles causas**:
1. El dominio en las acciones no está funcionando
2. Hay reglas de registro conflictivas

**Solución**:
```xml
<!-- Verificar el dominio en las acciones -->
<field name="domain">[('x_is_punto_inicio', '=', True)]</field>
```

---

## 📊 Diferencias vs Crear Tablas Nuevas

| Aspecto | Con Tablas Compartidas (Este Módulo) | Con Tablas Nuevas |
|---------|--------------------------------------|-------------------|
| **Complejidad** | Baja - Extiende modelos existentes | Alta - Duplica toda la lógica |
| **Tamaño BD** | Mínimo - Solo campos extra | Grande - Tablas completas duplicadas |
| **Mantenimiento** | Fácil - Hereda actualizaciones del POS | Difícil - Debe sincronizar cambios |
| **Reportes Unificados** | Fácil - Misma tabla | Difícil - Requiere UNION queries |
| **Migración Datos** | No necesaria | Compleja si se unifica después |
| **Aislamiento** | Lógico (filtros) | Físico (tablas separadas) |

---

## 📝 Notas Importantes

1. **Compatibilidad**: Este módulo está diseñado para **Odoo 17**. Para otras versiones, pueden necesitarse ajustes.

2. **Rendimiento**: Los campos `x_is_punto_inicio` están **indexados** para evitar impacto en el rendimiento.

3. **Migración**: Si en el futuro decides separar completamente los datos, puedes crear un script de migración basado en `x_is_punto_inicio`.

4. **Actualizaciones**: Al actualizar el módulo `point_of_sale`, este módulo heredará automáticamente las mejoras.

5. **Testing**: Antes de usar en producción, prueba exhaustivamente en un entorno de desarrollo.

---

## 🤝 Contribuciones

Si encuentras bugs o tienes sugerencias de mejora, por favor:

1. Documenta el problema detalladamente
2. Incluye pasos para reproducir
3. Proporciona logs si es posible

---

## 📄 Licencia

Este módulo está licenciado bajo **LGPL-3** (igual que Odoo).

---

## ✅ Checklist de Implementación Completada

- [x] Estructura de módulo creada
- [x] Archivo `__manifest__.py` con dependencias correctas
- [x] Modelos extendidos (pos.config, pos.session, pos.order, pos.payment)
- [x] Campos identificadores agregados (`x_is_punto_inicio`, `x_source_module`)
- [x] Lógica de marcado automático implementada en métodos `create()`
- [x] Grupos de seguridad definidos
- [x] Control de acceso a modelos configurado
- [x] Vistas heredadas y personalizadas
- [x] Menús y acciones con filtros automáticos
- [x] Documentación completa en código
- [x] README con instrucciones de instalación y uso
- [x] Archivo de descripción HTML para el módulo

---

## 🎯 Próximos Pasos (Opcional)

Si quieres extender el módulo, considera:

1. **Agregar Dashboard personalizado** con estadísticas específicas de PI
2. **Crear reportes propios** (ventas por hora, productos más vendidos, etc.)
3. **Implementar reglas de negocio específicas** (descuentos, promociones)
4. **Agregar campos calculados** (márgenes, rentabilidad, etc.)
5. **Integrar con otros módulos** (CRM, Inventario, Contabilidad)
6. **Personalizar la interfaz POS** (JavaScript/OWL components)

---

**¡El módulo está listo para usar!** 🚀
