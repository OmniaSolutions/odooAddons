odoo.define('omniasolutions_custom_widget.FieldSelectionExtention', function (require) {
"use strict";
var core = require('web.core');
var Model = require('web.Model');
var form_widgets = require('web.form_widgets');
var _t = core._t;
var qweb = core.qweb;


var FieldSelectionExtention = core.form_widget_registry.get('selection').extend({
    init: function (field_manager, node) {
		this._super(field_manager, node);
		//this.records_orderer = new instance.web.DropMisordered();
	},

    render_value: function() {
        var values = this.get("values");
        values =  [[false, this.node.attrs.placeholder || '']].concat(values);
        var found = _.find(values, function(el) { return el[0] === this.get("value"); }, this);
        if (! found) {
            found = [this.get("value"), _t('Unknown')];
            values = [found].concat(values);
        }
        var selfff = this;
        selfff.found = found;
        if (! this.get("effective_readonly")) {
        	var resArray = selfff.get_selected_val(selfff);
        	if (resArray.length == 2){
            	//selfff.selectedOption = resArray[0];
            	//var selectionTarget = resArray[1];
            	//selfff.attach_onchange(selectionTarget,selfff);
            	var parent = this.getParent();
            	var groupart = parent.get_field_value('x_groupart');
            	new Model(this.view.model).call("get_selection_vals",[groupart]).then(function(values2){
    	            //selfff.$().html(qweb.render("FieldSelectionSelect", {widget: selfff, values: values2}));
            		qweb.add_template('/web/static/src/xml/base.xml');
            		var selHtml = qweb.render("FieldSelection", {widget: selfff, values: values2});
    	            selfff.$().html(selHtml);
    	            selfff.$("select").val(JSON.stringify(found[0]));
    	        });
        	}
        } else {
        	var parent = this.getParent();
        	var current_id = parent.get_field_value('id');
        	new Model(this.view.model).call("get_val_fromdb_name",[selfff.found[0], current_id]).then(function(toDisplay){
        		selfff.$el.text(toDisplay);
        		selfff.$el.val(toDisplay);
	        });
        }
    },

    get_selected_val : function () {
    	var elements = $('.omniasolutions_'+this.name);
    	if (elements.length == 2){
    		var customEl = elements[1];
    		var elemType = customEl.tagName;
    		if (elemType == 'SPAN'){
    			c1 = customEl.children[0];
    			if (c1 != undefined){
        			if (c1.tagName == 'SELECT'){
        				var selOptions = c1.selectedOptions;
        				if (selOptions.length == 1){
        					var selectedVal = selOptions[0].value;
        					return [selectedVal,c1]
        				}
        			}
    			}
    		}
    	}
    	return ['','']
    },
    
    attach_onchange: function(elem,selfff) {
    	if (elem != undefined){
        	elem.onchange = function(){
        		var resArray = selfff.get_selected_val();
        		if (resArray.length == 2){
        			// To clear children options
	            	selfff.$("select")[0].options.length = 0;
		        	new Model(selfff.view.model).call("get_selection_vals",[resArray[0]]).then(function(values3){
		        		// To set first value as empty
		        		selfff.$("select").append($('<option>', {		
					    	value: '',
					    	text: ''
							}));
		        		// Set avaible options due to selected val
			            for (i=0; i< values3.length; i++){
					        selfff.$("select").append($('<option>', {
					    	value: values3[i][0],
					    	text: values3[i][1]
							}));
						}
					});
		        	// To set as default empty index
	        		selfff.$("select")[0].options.selectedIndex = 0;
        		}
    		}
    	}
    },
    
    store_dom_value: function () {
        if (!this.get('effective_readonly') && this.$('select').length) {
            var val = this.$('select').val();
            if (val != null){
	            if (val.charAt(0) == '"'){
	            	val = JSON.parse(val); 
	            }
            }
            else{
            	val = JSON.parse(false);
            }
            this.internal_set_value(val);
        }
    },
});

core.form_widget_registry.add('selection_field_extention', FieldSelectionExtention);

return {
	FieldSelectionExtention: FieldSelectionExtention,
};

});