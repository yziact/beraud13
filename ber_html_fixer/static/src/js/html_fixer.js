odoo.define('ber_html_fixer.fixer_widget', function (require) {
"use strict";

var core = require('web.core');
var common = require('web.form_common');
var widgets = require('web.form_widgets');
var listview = require('web.ListView');

var list_widget_registry = core.list_widget_registry;

var Column = list_widget_registry.get('field')

var ColHtml = Column.extend({

    _format: function (row_data, options) {
        console.log("ColHtml format");
        var value = row_data[this.id].value;
        if (value) {
            // return "<h1> hello </h1>" + value;
            // return value.replace(/<p>/g, "rep");
            return $(value).text();
            // return $(value);
        }

        return this._super(row_data, options);
    },

});

list_widget_registry
    .add('field.html_fixer', ColHtml)

var FieldHtmlFixer = widgets.FieldChar.extend({

    /*
    init: function() {
        this._super.apply(this, arguments);
    },

    start: function() {
        var tmp = this._super();
        this.on("change:currency_info", this, this.update);
        return tmp;
    },

    initialize_content: function() {
        this._super();
        this.$el.addClass('o_form_field_derp_derp');
    },


    render_value: function() {
        this._super();
        if (this.get("effective_readonly") && this.clickable) {
            this.$el.attr('href', this.prefix + ':' + this.get('value'));
        }
    }, */

});

core.form_widget_registry
    .add('html_fixer', FieldHtmlFixer);

return {
    FieldHtmlFixer: FieldHtmlFixer,
}

});
