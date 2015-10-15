openerp.omniaSelectionWidget = function(instance) {
var _t = instance.web._t;
var QWeb = instance.web.qweb;

instance.web.form.FieldSelectionExtention = instance.web.form.FieldSelection.extend({
	//template: "FieldSelectionCustom",
    init: function (field_manager, node) {
		this._super(field_manager, node);
		this.records_orderer = new instance.web.DropMisordered();
	},
	display_data: function() {
		var self = this;
		//htmlTemplate = QWeb.render("FieldSelectionCustom", {widget: this});
		var $select = this.$el.find('select')
		$select.focus(function() {
	        $select.append($('<option>', {
	    	value: 1,
	    	text: 'My option'
			}));
	    });
	},
	initialize_content: function() {
		var self = this;
		self.display_data();
	    //return this._super();
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
        if (! this.get("effective_readonly")) {
        	this.$().html(QWeb.render("FieldSelectionSelect", {widget: this, values: []}));
        	this.$("select").val(JSON.stringify(found[0]));
        	var viewModel = this.view.model;
            this.$("select").focus(function() {
            	new instance.web.Model(self._model).call("get_selection_vals",[]).then(function(values2){
			        this.$("select").append($('<option>', {
			    	value: 1,
			    	text: 'My option'
					}));
				});
	        });

        } else {
            this.$el.text(found[1]);
        }
    },
    
	query_values: function() {
	    var self = this;
        var def;
    	new instance.web.Model(this.view.model).call("get_selection_vals",[]).then(function(values){
    		def = $.when(values);
	        self.records_orderer.add(def).then(function(values) {
	            if (! _.isEqual(values, self.get("values"))) {
	                self.set("values", values);
	            }
	        });
    	});
        

	},
});
instance.web.form.widgets = instance.web.form.widgets.extend({
    'selection_field_extention' : 'instance.web.form.FieldSelectionExtention',
});
};
