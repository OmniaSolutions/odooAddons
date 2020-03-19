odoo.define('omniasolutions_custom_widget.FieldSelectionExtention', function (require) {
    'use strict';
	var AbstractField = require('web.AbstractField');
	var field_registry = require('web.field_registry');
	var relational_fields = require('web.relational_fields');

	var FieldSelectionExtention = relational_fields.FieldSelection.extend({
		
    supportedFieldTypes: ['char'],
    events: _.extend({}, AbstractField.prototype.events, {
        'click': '_onClick',
		'change': '_onChange',
    }),

    init: function (parent, name, record, options) {
		console.log('init');
        this._super.apply(this, arguments);
		var possible_values;
		self.possible_values = this.get_possible_values();
		console.log(self.possible_values)
    },

/* On click recompute values to show */
    /**
     * @private
     * @param {MouseEvent} event
     */
    _onClick: function (event) {
		console.log('_onClick');
		var self = this;
		var currentval;
		currentval = this.get_selected_val();
		if (currentval in this.possible_values) {
        	this.values = this.possible_values[currentval];
			}
		else {
			this.values = [[false, '']]
		}
		this._render();
    },

/* Call python to get all possible selection values and calls render to reload selection values */
	get_possible_values : function () {
		var prom;
		var self = this;
		prom = self._rpc({
                        model: self.model,
                        method: 'get_val_fromdb_name',
						args: [self.record.id],
                        kwargs: {},
                    });
		Promise.resolve(prom).then(function (results) {
                    self.possible_values = results;
					console.log(self.possible_values)
					self._render();
                });
		return [['false', '']];

	},

/* Get value from field with specific class */
    get_selected_val : function () {
    	var elements = $('.omniasolutions_'+this.name);
    	if (elements.length == 1){
    		var customEl = elements[0];
    		var elemType = customEl.tagName;
			if (elemType == 'SPAN'){
				return customEl.textContent;
			}
			if (elemType == 'SELECT'){
				var selOptions = customEl.selectedOptions;
				if (selOptions.length == 1){
					return selOptions[0].innerText;
				}
			}
    	}
    	return ['','']
    },

/* Render take value from field with specific class and compute possible selection values */
    _render: function () {
		console.log('_render');
		if (this.possible_values != undefined){
			var currentval;
			currentval = this.get_selected_val();
			if (currentval in this.possible_values) {
	        	this.values = this.possible_values[currentval];
				}
			else {
				this.values = [[false, '']]
			}
		}
        this._super.apply(this, arguments);
    },

/* Render readonly is called when you are not in edit mode, simply display text value */
    _renderReadonly: function () {
		console.log('_renderReadonly');
        this._super.apply(this, arguments);
		for (var i = 0; i < this.values.length; i++) {
		    if (this.values[i][0] == this.value){
				this.$el.empty().text(this._formatValue(this.values[i][1]));
				return;
		}
		}
    },

});

	field_registry.add('selection_field_extention', FieldSelectionExtention);
	
return {
    FieldSelectionExtention: FieldSelectionExtention
};
    
});


