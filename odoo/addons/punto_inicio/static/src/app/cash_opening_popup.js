/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";

/**
 * Cash Opening Popup para Punto de Inicio
 * ========================================
 *
 * Componente independiente que maneja la apertura de caja.
 * Muestra un popup donde el usuario ingresa:
 * - Monto inicial de efectivo
 * - Notas/observaciones
 */
export class CashOpeningPopup extends Component {
    static template = "punto_inicio.CashOpeningPopup";
    static components = { Dialog };
    static props = {
        session_id: Number,
        close: Function,
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.state = useState({
            cashAmount: 0,
            notes: "",
            loading: false,
        });
    }

    /**
     * Confirma la apertura de caja y abre la sesión
     */
    async confirm() {
        this.state.loading = true;

        try {
            // Llamar al backend para abrir la sesión con el monto inicial
            await this.orm.call(
                "pos.session",
                "set_cashbox_opening",
                [this.props.session_id],
                {
                    cashbox_start: this.state.cashAmount,
                    notes: this.state.notes,
                }
            );

            // Abrir la sesión
            await this.orm.call(
                "pos.session",
                "action_pos_session_open",
                [this.props.session_id]
            );

            // Mostrar notificación de éxito
            this.notification.add(
                "Sesión iniciada correctamente",
                { type: "success" }
            );

            // Redirigir al frontend de Punto de Inicio
            window.location = `/punto_inicio/ui?session_id=${this.props.session_id}`;

        } catch (error) {
            console.error("Error al abrir sesión:", error);
            this.notification.add(
                "Error al abrir la sesión: " + error.message,
                { type: "danger" }
            );
            this.state.loading = false;
        }
    }

    /**
     * Cancela la apertura de caja
     */
    cancel() {
        this.props.close();
    }

    /**
     * Actualiza el monto de efectivo
     */
    onCashAmountChange(ev) {
        this.state.cashAmount = parseFloat(ev.target.value) || 0;
    }

    /**
     * Actualiza las notas
     */
    onNotesChange(ev) {
        this.state.notes = ev.target.value;
    }
}