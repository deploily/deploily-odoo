odoo.define('maintenance_planning.QtyAvailableForMaintWidget', function (require) {
    "use strict";
    
    
    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;

    var Widget = require('web.Widget');
    var widget_registry = require('web.widget_registry');

    var QtyAvailableForMaintWidget = Widget.extend({
        template: 'maintenance_planning.QtyAvailableForMaint',
        events: _.extend({}, Widget.prototype.events, {
            'click .fa-area-chart': '_onClickButton',
        }),

        /**
         * @override
         * @param {Widget|null} parent
         * @param {Object} params
         */
        init: function (parent, params) {
            // console.log("data : " + JSON.stringify(params.data));
            // console.log("fields : " + JSON.stringify(params.fields));
            this.data = params.data;
            this.fields = params.fields;
            this._super(parent);
            },
    
        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {
                self._setPopOver();
            });
        },

        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------
        /**
         * Set a bootstrap popover on the current QtyAtDate widget that display available
         * quantity.
         */
        _setPopOver() {
            const $content = this._getContent();
            if (!$content) {
                return;
            }
            const options = {
                content: $content,
                html: true,
                placement: 'left',
                title: _t('Availability'),
                trigger: 'focus',
                delay: {'show': 0, 'hide': 100 },
            };
            this.$el.popover(options);
        },
        
        _getContent() { 
            const $content = $(QWeb.render('maintenance_planning.QtyDetailPopOver', {
                data: this.data,
            }));
            return $content;
        },

        //--------------------------------------------------------------------------
        // Handlers
        //--------------------------------------------------------------------------
        _onClickButton: function () {
            // We add the property special click on the widget link.
            // This hack allows us to trigger the popover (see _setPopOver) without
            // triggering the _onRowClicked that opens the order line form view.
            this.$el.find('.fa-area-chart').prop('special_click', true);
        },
    });
    
    widget_registry.add('qty_available_for_maint_widget', QtyAvailableForMaintWidget);
    
    return QtyAvailableForMaintWidget;
    });