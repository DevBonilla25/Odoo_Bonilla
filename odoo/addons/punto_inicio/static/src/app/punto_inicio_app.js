/** @odoo-module **/

import { Component, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

/**
 * Punto de Inicio - Frontend Principal
 * =====================================
 *
 * Aplicación principal del frontend de Punto de Inicio.
 * Esta es una interfaz básica independiente del POS.
 */
export class PuntoInicioApp extends Component {
    static template = "punto_inicio.PuntoInicioApp";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.action = useService("action");

        this.state = useState({
            session: null,
            loading: true,
            error: null,
        });

        // Cargar datos de la sesión al montar el componente
        onMounted(async () => {
            await this.loadSession();
        });
    }

    /**
     * Carga los datos de la sesión actual
     */
    async loadSession() {
        try {
            // Obtener session_id de la URL
            const urlParams = new URLSearchParams(window.location.search);
            const sessionId = parseInt(urlParams.get('session_id'));

            if (!sessionId) {
                throw new Error("No se proporcionó ID de sesión");
            }

            // Cargar datos de la sesión desde el backend
            const sessions = await this.orm.searchRead(
                "pos.session",
                [["id", "=", sessionId]],
                ["name", "config_id", "start_at", "state", "cash_register_balance_start"]
            );

            if (sessions.length === 0) {
                throw new Error("Sesión no encontrada");
            }

            this.state.session = sessions[0];
            this.state.loading = false;

        } catch (error) {
            console.error("Error al cargar sesión:", error);
            this.state.error = error.message;
            this.state.loading = false;

            this.notification.add(
                "Error al cargar la sesión: " + error.message,
                { type: "danger" }
            );
        }
    }

    /**
     * Cierra la sesión actual
     */
    async closeSession() {
        if (!confirm("¿Estás seguro de que deseas cerrar esta sesión?")) {
            return;
        }

        try {
            await this.orm.call(
                "pos.session",
                "action_pos_session_closing_control",
                [this.state.session.id]
            );

            this.notification.add(
                "Sesión cerrada correctamente",
                { type: "success" }
            );

            // Redirigir al dashboard
            window.location = "/web#action=punto_inicio.action_punto_inicio_dashboard";

        } catch (error) {
            console.error("Error al cerrar sesión:", error);
            this.notification.add(
                "Error al cerrar la sesión: " + error.message,
                { type: "danger" }
            );
        }
    }

    /**
     * Vuelve al dashboard sin cerrar la sesión
     */
    backToDashboard() {
        window.location = "/web#action=punto_inicio.action_punto_inicio_dashboard";
    }
}

// Registrar la aplicación como acción de cliente
registry.category("actions").add("punto_inicio.ui", PuntoInicioApp);