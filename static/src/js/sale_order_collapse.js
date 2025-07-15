odoo.define('sale_order_chapters.collapse', function (require) {
    "use strict";

    var FormController = require('web.FormController');
    var core = require('web.core');
    var _t = core._t;

    FormController.include({
        /**
         * Maneja el evento de colapso/expansión de secciones
         */
        _onCollapseSection: function(ev) {
            ev.preventDefault();
            var $target = $(ev.currentTarget);
            var $row = $target.closest('tr');
            var sectionId = $row.data('section-id');
            
            if ($row.hasClass('section-collapsed')) {
                this._expandSection($row, sectionId);
            } else {
                this._collapseSection($row, sectionId);
            }
        },

        /**
         * Expande una sección específica
         */
        _expandSection: function($row, sectionId) {
            $row.removeClass('section-collapsed').addClass('section-expanded');
            $row.find('.collapse-icon').removeClass('fa-plus-square').addClass('fa-minus-square');
            
            // Mostrar todas las líneas de productos de esta sección
            this.$('tr[data-section-parent="' + sectionId + '"]').show();
            
            // Animación suave
            this.$('tr[data-section-parent="' + sectionId + '"]').fadeIn(300);
        },

        /**
         * Colapsa una sección específica
         */
        _collapseSection: function($row, sectionId) {
            $row.removeClass('section-expanded').addClass('section-collapsed');
            $row.find('.collapse-icon').removeClass('fa-minus-square').addClass('fa-plus-square');
            
            // Ocultar todas las líneas de productos de esta sección
            this.$('tr[data-section-parent="' + sectionId + '"]').fadeOut(300);
        },

        /**
         * Expande o colapsa todas las secciones
         */
        _onToggleAllSections: function(ev) {
            ev.preventDefault();
            var $sectionRows = this.$('tr.section-line');
            var expandedCount = $sectionRows.filter('.section-expanded').length;
            var totalSections = $sectionRows.length;
            
            if (expandedCount === totalSections) {
                // Si todas están expandidas, colapsar todas
                this._collapseAllSections();
            } else {
                // Si alguna está colapsada, expandir todas
                this._expandAllSections();
            }
        },

        /**
         * Expande todas las secciones
         */
        _expandAllSections: function() {
            var self = this;
            this.$('tr.section-line').each(function() {
                var $row = $(this);
                var sectionId = $row.data('section-id');
                if ($row.hasClass('section-collapsed')) {
                    self._expandSection($row, sectionId);
                }
            });
        },

        /**
         * Colapsa todas las secciones
         */
        _collapseAllSections: function() {
            var self = this;
            this.$('tr.section-line').each(function() {
                var $row = $(this);
                var sectionId = $row.data('section-id');
                if ($row.hasClass('section-expanded')) {
                    self._collapseSection($row, sectionId);
                }
            });
        },

        /**
         * Inicializa los eventos de colapso al cargar la vista
         */
        start: function() {
            var self = this;
            return this._super.apply(this, arguments).then(function() {
                // Agregar eventos de click para los iconos de colapso
                self.$el.on('click', '.collapse-icon', self._onCollapseSection.bind(self));
                
                // Inicializar estado por defecto (expandido)
                self.$('tr.section-line').addClass('section-expanded');
            });
        }
    });

    return FormController;
});