openerp.omniasolutions_custom_widget = function(instance) {
var _t = instance.web._t;
var QWeb = instance.web.qweb;

instance.web.form.FieldSelectionExtention = instance.web.form.FieldSelection.extend({
    init: function (field_manager, node) {
		this._super(field_manager, node);
		this.records_orderer = new instance.web.DropMisordered();
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
        	resArray = selfff.get_selected_val(selfff);
        	if (resArray.length == 2){
            	selfff.selectedOption = resArray[0];
            	selectionTarget = resArray[1];
            	selfff.attach_onchange(selectionTarget,selfff);
            	new instance.web.Model(this.view.model).call("get_selection_vals",[selfff.selectedOption]).then(function(values2){
    	            selfff.$().html(QWeb.render("FieldSelectionSelect", {widget: selfff, values: values2}));
    	            selfff.$("select").val(JSON.stringify(selfff.found[0]));
    	        });
        	}

        } else {
            this.$el.text(found[0]);
        }
    },

    get_selected_val : function () {
    	elements = $('.omniasolutions_x_mat_pop');
    	if (elements.length == 2){
    		customEl = elements[1];
    		elemType = customEl.tagName;
    		if (elemType == 'SPAN'){
    			c1 = customEl.children[0];
    			if (c1 != undefined){
        			if (c1.tagName == 'SELECT'){
        				selOptions = c1.selectedOptions;
        				if (selOptions.length == 1){
        					selectedVal = selOptions[0].value;
        					return [selectedVal,c1]
        				}
        			}
    			}
    		}
    	}
    },
    
    attach_onchange: function(elem,selfff) {
    	if (elem != undefined){
        	elem.onchange = function(){
        		resArray = selfff.get_selected_val();
        		if (resArray.length == 2){
	            	selfff.$("select")[0].options.length = 0;
		        	new instance.web.Model(selfff.view.model).call("get_selection_vals",[resArray[0]]).then(function(values3){
		        		selfff.$("select").append($('<option>', {
					    	value: '',
					    	text: ''
							}));
			            for (i=0; i< values3.length; i++){
					        selfff.$("select").append($('<option>', {
					    	value: values3[i][0],
					    	text: values3[i][1]
							}));
						}
					});
	        		selfff.$("select")[0].options.selectedIndex = 0;	//To set as default empty index
        		}
    		}
    	}

    },
    store_dom_value: function () {
        if (!this.get('effective_readonly') && this.$('select').length) {
            var val = this.$('select').val();
            this.internal_set_value(val);
        }
    },

});
instance.web.form.widgets = instance.web.form.widgets.extend({
    'selection_field_extention' : 'instance.web.form.FieldSelectionExtention',
});
};
