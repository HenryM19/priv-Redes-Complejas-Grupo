/* ==========================================================================
 * THEME.JS — Lógica compartida de la presentación Intrinsic→IA
 *
 * Funcionalidad:
 *   1. Gestión del modo claro/oscuro con persistencia en localStorage
 *      (el atributo data-theme se fija en <head> antes del primer render
 *      para evitar parpadeo; aquí solo se gestiona el cambio).
 *   2. Inyección de la barra de navegación (anterior / contador / siguiente
 *      / botón de tema) a partir de window.SLIDE definido en cada página.
 *   3. Navegación con teclado: ← → (slides), Espacio/AvPág, Inicio, T (tema).
 * ========================================================================== */

(function () {
    'use strict';

    var KEY  = 'ic-theme';                       // clave de persistencia
    var root = document.documentElement;
    var S    = window.SLIDE || {};               // {index, total, prev, next}

    /**
     * getTheme — Lee el tema actual del documento.
     * @returns {string} 'dark' | 'light'
     */
    function getTheme() {
        return root.dataset.theme === 'light' ? 'light' : 'dark';
    }

    /**
     * setTheme — Aplica un tema y lo persiste.
     * @param {string} t - 'dark' o 'light'
     * @returns {void}
     */
    function setTheme(t) {
        root.dataset.theme = t;
        try { localStorage.setItem(KEY, t); } catch (e) { /* file:// sin storage */ }
        updateToggle();
    }

    /**
     * toggleTheme — Alterna entre modo claro y oscuro.
     * @returns {void}
     */
    function toggleTheme() {
        setTheme(getTheme() === 'dark' ? 'light' : 'dark');
    }

    /**
     * updateToggle — Refresca el icono/etiqueta del botón según el tema.
     *                Muestra el modo al que se cambiará al hacer clic.
     * @returns {void}
     */
    function updateToggle() {
        var btn = document.querySelector('.theme-toggle');
        if (!btn) return;
        var dark = getTheme() === 'dark';
        btn.textContent = dark ? '☀ Claro' : '● Oscuro';
        btn.title = dark ? 'Cambiar a modo claro (T)' : 'Cambiar a modo oscuro (T)';
    }

    /**
     * buildNav — Construye e inyecta la barra de navegación inferior.
     * @returns {void}
     */
    function buildNav() {
        var nav = document.createElement('div');
        nav.className = 'nav-controls';

        if (S.prev) {
            var a = document.createElement('a');
            a.href = S.prev; a.textContent = '← Anterior';
            nav.appendChild(a);
        }
        if (S.index && S.total) {
            var ctr = document.createElement('span');
            ctr.className = 'slide-ctr';
            ctr.textContent = S.index + ' / ' + S.total;
            nav.appendChild(ctr);
        }
        if (S.next) {
            var b = document.createElement('a');
            b.href = S.next;
            b.textContent = (S.index === S.total) ? '⟲ Inicio' : 'Siguiente →';
            nav.appendChild(b);
        }

        var btn = document.createElement('button');
        btn.className = 'theme-toggle';
        btn.addEventListener('click', toggleTheme);
        nav.appendChild(btn);

        document.body.appendChild(nav);
        updateToggle();
    }

    /**
     * onKey — Manejador de navegación con teclado.
     * @param {KeyboardEvent} e
     * @returns {void}
     */
    function onKey(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        switch (e.key) {
            case 'ArrowRight':
            case 'PageDown':
            case ' ':
                if (S.next) location.href = S.next;
                break;
            case 'ArrowLeft':
            case 'PageUp':
                if (S.prev) location.href = S.prev;
                break;
            case 'Home':
                location.href = '01_portada.html';
                break;
            case 't':
            case 'T':
                toggleTheme();
                break;
        }
    }

    /* ---------- main: inicialización al cargar el DOM ---------- */
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', buildNav);
    } else {
        buildNav();
    }
    document.addEventListener('keydown', onKey);
})();
