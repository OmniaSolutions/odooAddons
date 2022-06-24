
var showtmpMessage = function(elementName){
	document.getElementById(elementName).style.display='block';
setTimeout(function() {
        document.getElementById(elementName).style.display="none";
        reset_value();
    }, 1000);  // 5 seconds
};

var reset_value = function(){
  var el = document.getElementById("input_workorder_id");
  el.value = "";
  el.focus();
}
var getValue = function(){
	var val = document.getElementById("input_workorder_id").value;
	$.ajax({
	  type: 'POST',
	  url: "/mrp_omnia/workorder_simple_post/?workorder_id="+val,
	  data: JSON.stringify(val),
	  success: function(data){
		  showtmpMessage("ok_done");
		  update_tables();
	  },
	  error: function(){
		  showtmpMessage("error");
		  
	  },
	})
}

var replace_element = function(from_name, to_element){
	var Obj = document.getElementById(from_name); //any element to be fully replaced
	if(Obj.outerHTML) { //if outerHTML is supported
	    Obj.outerHTML=to_element; ///it's simple replacement of whole element with contents of str var
	}
	else { //if outerHTML is not supported, there is a weird but crossbrowsered trick
	    var tmpObj=document.createElement("div");
	    tmpObj.innerHTML=to_element;
	    ObjParent=Obj.parentNode; //Okey, element should be parented
	    ObjParent.replaceChild(tmpObj,Obj); //here we placing our temporary data instead of our target, so we can find it then and replace it into whatever we want to replace to
	    ObjParent.innerHTML=ObjParent.innerHTML.replace('<div></div>', to_element);
	}
}

var update_table_active_workorder = function(){
	$.ajax({
		  type: 'GET',
		  url: "/mrp_omnia/active_workorder_simple",
		  success: function(data){
			  replace_element("active_workorder_table", data)
		  },
		  error: function(){
			  replace_element("active_workorder_table",'<table id="active_workorder_table"><tr><td>Errore</td></tr></table>')
		  },
		})  	
};

var update_table_ready_workorder = function(){
	$.ajax({
		  type: 'GET',
		  url: "/mrp_omnia/ready_workorder_simple",
		  success: function(data){
			  replace_element("ready_workorder_table", data)
		  },
		  error: function(){
			  replace_element("ready_workorder_table",'<table id="ready_workorder_table"><tr><td>Errore</td></tr></table>')
			  
			  
		  },
		})  	
};

var update_tables = function(){
	update_table_active_workorder();
	update_table_ready_workorder();	
}
var get_workcenter = function(){
	$.ajax({
		  type: 'GET',
		  url: "/mrp_omnia/workcenter_name",
		  success: function(data){
			  replace_element("workcenter_name", '<div id="workcenter_name">' + data + '</div>')
		  },
		  error: function(){
			  replace_element("workcenter_name",'<div id="workcenter_name">Error</div>')
		  },
		}) 
}
var on_load_body = function(){
	get_workcenter();
	update_tables();
	setInterval(update_tables , 10000);
}
