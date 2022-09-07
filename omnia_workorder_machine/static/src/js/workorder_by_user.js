odoo.define('omnia_workorder_machine.workorder_machine_list', function (require) {
    "use strict";
    var ajax = require('web.ajax');
    var core = require('web.core');
    var config = require('web.config');

    function download(data, filename, type) {
        var file = new Blob([data], {type: type});
        if (window.navigator.msSaveOrOpenBlob) // IE10+
            window.navigator.msSaveOrOpenBlob(file, filename);
        else { // Others
            var a = document.createElement("a"),
                    url = URL.createObjectURL(file);
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            setTimeout(function() {
                document.body.removeChild(a);
                window.URL.revokeObjectURL(url);  
            }, 0); 
        }
    }

    function print_label(button) {
    	console.log("Start printing label");
        var button = button.currentTarget;
        var closestTr = button.closest('tr');
        var internal_ref = closestTr.getElementsByClassName('internal_ref');
        var route = '/mrp_omnia/print_label/' + internal_ref[0].textContent;

        var xhr = new XMLHttpRequest();
        xhr.open('GET', route, true);
        xhr.responseType = 'blob';

        xhr.onload = function(e) {
          if (this.status == 200) {
        	  download(this.response, 'label.pdf', 'application/pdf')  
          }
        };

        xhr.send();
    }

    function start_work1 (button) {
        console.log("Start working");
        var button = button.currentTarget;
        var closestTr = button.closest('tr');
        closestTr.style.cursor ='wait';
        button.style.display = 'none';
        var wo_id = closestTr.getElementsByClassName('wo_id');
        var route = '/mrp_omnia/workorder_start/';
		ajax.jsonRpc(route, 'call', {
			'wo_id' : wo_id[0].textContent,
		}).then(function (data) {
			filter_res(null);
		   }
	    );
        console.log("end")
    }

    var start_work11 = start_work1;
    function pause_work1 (button) {
        console.log("Pause working");
        var button = button.currentTarget;
        button.style.display = 'none';
        var closestTr = button.closest('tr');
        closestTr.style.cursor ='wait';
        var wo_id = closestTr.getElementsByClassName('wo_id');
        var route = '/mrp_omnia/workorder_pause/';
		ajax.jsonRpc(route, 'call', {
			'wo_id' : wo_id[0].textContent,
		}).then(function (data) {
			filter_res(null);
		   }
	    );
        console.log("end")
    }

    function resume_work1 (button) {
        console.log("Pause working");
        var button = button.currentTarget;
        button.style.display = 'none';
        var closestTr = button.closest('tr');
        closestTr.style.cursor ='wait';
        var wo_id = closestTr.getElementsByClassName('wo_id');
        var route = '/mrp_omnia/workorder_resume/';
		ajax.jsonRpc(route, 'call', {
			'wo_id' : wo_id[0].textContent,
		}).then(function (data) {
			filter_res(null);
		   }
	    );
        console.log("end")
    }

    function stop_work1 (button) {
        console.log("Pause working");
        var button = button.currentTarget;
        button.style.display = 'none';
        var closestTr = button.closest('tr');
        closestTr.style.cursor ='wait';
        var wo_id = closestTr.getElementsByClassName('wo_id');
        var n_pieces_to_produce = closestTr.getElementsByClassName('n_pieces_to_produce');
        var n_pieces = closestTr.getElementsByClassName('n_pieces');
        var pieces = n_pieces[0].valueAsNumber;
        var pieces_to_produce = parseFloat(n_pieces_to_produce[0].textContent);
        var n_scrap_ui = closestTr.getElementsByClassName('n_scrap');
        var n_scrap = n_scrap_ui[0].valueAsNumber;
        var route = '/mrp_omnia/workorder_record/';
		ajax.jsonRpc(route, 'call', {
			'wo_id' : wo_id[0].textContent,
			'n_pieces': pieces,
			'n_scrap': n_scrap,
		}).then(function (data) {
			filter_res(null);
		   }
	    );
        console.log("end")
    }

    function state_changed(tdElem) {
    	var closestTr = tdElem.closest('tr');
    	var el_user_working = closestTr.getElementsByClassName('wo_isuserworking');
    	var el_start_work = closestTr.getElementsByClassName('start_work');
    	var el_pause_work = closestTr.getElementsByClassName('pause_work');
    	var el_resume_work = closestTr.getElementsByClassName('resume_work');
    	var el_stop_work = closestTr.getElementsByClassName('stop_work');
    	
    	var input_qty = closestTr.getElementsByClassName('n_pieces')[0];
    	var scrap_qty = closestTr.getElementsByClassName('n_scrap')[0];
    	
    	if ($.inArray(tdElem.textContent, ['draft', 'ready']) != -1) {
    		el_start_work[0].style.display = 'block';
    		el_pause_work[0].style.display = 'none';
    		el_resume_work[0].style.display = 'none';
    		el_stop_work[0].style.display = 'none';
    		input_qty.style.display = 'none';
    		scrap_qty.style.display = 'none';
    	}
    	else if ($.inArray(tdElem.textContent, ["startworking"]) != -1){
    		el_start_work[0].style.display = 'none';
    		el_pause_work[0].style.display = 'block';
    		el_resume_work[0].style.display = 'none';
    		el_stop_work[0].style.display = 'block';
    		input_qty.style.display = 'block';
    		scrap_qty.style.display = 'block';
    	}
    	else if ($.inArray(tdElem.textContent, ['progress']) != -1 & el_user_working[0].textContent == 'True'){
    		el_start_work[0].style.display = 'none';
    		el_pause_work[0].style.display = 'block';
    		el_resume_work[0].style.display = 'none';
    		el_stop_work[0].style.display = 'block';
    		input_qty.style.display = 'block';
    		scrap_qty.style.display = 'block';
    	}
    	else if ($.inArray(tdElem.textContent, ['pause', 'progress']) != -1 & el_user_working[0].textContent == 'False'){
    		el_start_work[0].style.display = 'none';
    		el_pause_work[0].style.display = 'none';
    		el_resume_work[0].style.display = 'block';
    		el_stop_work[0].style.display = 'none';
    		input_qty.style.display = 'block';
    		scrap_qty.style.display = 'block';
    	}
    	else {
    		el_start_work[0].style.display = 'none';
    		el_pause_work[0].style.display = 'none';
    		el_resume_work[0].style.display = 'none';
    		el_stop_work[0].style.display = 'none';
    		input_qty.style.display = 'block';
    		scrap_qty.style.display = 'block';
    	}
    	
    }
    
    function show_workorders_by_user(){
    	var user_id = document.getElementById('input_user_id').valueAsNumber;
		var route = '/mrp_omnia/render_workorder_by_user/' + user_id;
		ajax.jsonRpc(route, 'call', {}).then(function (data) {
			updete_workorder(data);
		});
    }
  
    function show_workorders_by_employee(){
    	var user_id = document.getElementById('input_employee_id').valueAsNumber;
		var route = '/mrp_omnia/render_workorder_by_employee/' + user_id;
		ajax.jsonRpc(route, 'call', {}).then(function (data) {
			updete_workorder(data);
		});
    }
  
  
    function filter_res (button){
		console.log("clicked button")
        wo_id = document.getElementById('input_search_workorder_id');
		if(wo_id){
			var wo_id = wo_id.valueAsNumber;
	        wc_id = document.getElementById('input_search_worcenter_id');
			var wc_id = wc_id.valueAsNumber;
			console.log("getted value")
	        if (isNaN(wo_id)){
	    		wo_id = 0
	    	}
	        if (isNaN(wc_id)){
	        	wc_id = 0
	    	}
			var route = '/mrp_omnia/workorder_machine/' + wc_id + '/' + wo_id;
	
			ajax.jsonRpc(route, 'call', {}).then(function (data) {
				updete_workorder(data);
			});
		}else{
			show_workorders_by_user();
			
		}
	};
	
	var updete_workorder = function (data) {
		var table_to_replace = document.getElementById('to_replace');
		table_to_replace.innerHTML = data;
	    var print_label_list = document.getElementsByClassName('print_label');
	    var i0;
	    for (i0 = 0; i0 < print_label_list.length; i0++){
	    	print_label_list[i0].onclick = print_label;
	    }
	    var td_list = document.getElementsByClassName('wo_state');
	    var i;
	    for (i = 0; i < td_list.length; i++){
	    	var td_el = td_list[i];
	    	console.log(td_el);
	    	if (td_el != undefined){
	    		state_changed(td_el);
	    	}
	    }
	    // Start workel
	    var i1;
	    var start_work_butt_list = document.getElementsByClassName('start_work')
	    for (i1 = 0; i1 < start_work_butt_list.length; i1++){
	    	start_work_butt_list[i1].onclick = start_work1
	    }
	    // Pause Work
	    var i2;
	    var pause_work_butt_list = document.getElementsByClassName('pause_work')
	    for (i2 = 0; i2 < pause_work_butt_list.length; i2++){
	    	pause_work_butt_list[i2].onclick = pause_work1
	    }
	    // Resume Work
	    var i3;
	    var resume_work_butt_list = document.getElementsByClassName('resume_work')
	    for (i3 = 0; i3 < resume_work_butt_list.length; i3++){
	    	resume_work_butt_list[i3].onclick = resume_work1
	    }
	    // Record Work
	    var i4;
	    var stop_work_butt_list = document.getElementsByClassName('stop_work')
	    for (i4 = 0; i4 < stop_work_butt_list.length; i4++){
	    	stop_work_butt_list[i4].onclick = stop_work1
	    }
    };

    var update_user_name = function(){
    	var user_id = document.getElementById('input_user_id')
    	var user_id_n = user_id.valueAsNumber
    	var route = '/mrp_omnia/get_user_name/' + user_id_n;
		ajax.jsonRpc(route, 'call', {}).then(function (data) {
			var p_user_name = document.getElementById('user_name');
			p_user_name.innerHTML = data
		});
    }

    var update_employee_name = function(){
    	var user_id = document.getElementById('input_employee_id')
    	var user_id_n = user_id.valueAsNumber
    	var route = '/mrp_omnia/get_employee_name/' + user_id_n;
		ajax.jsonRpc(route, 'call', {}).then(function (data) {
			var p_user_name = document.getElementById('user_name');
			p_user_name.innerHTML = data
		});
    }

    window.onload = function() {
	    console.log("omnia_workorder_machine.workorder_machine_list loaded")
	    var _t = core._t;
	    console.log("Start getting button")
	    var button_search = document.getElementById('button_search');
	    if(button_search){
		    button_search.addEventListener("click", function() {
		    	filter_res(button_search);
			}, false)
	    };
		var show_workorders_by_user_id = document.getElementById('show_workorders_by_user');
	    if(show_workorders_by_user_id){
			show_workorders_by_user_id.addEventListener("click", function() {
		    	show_workorders_by_user(show_workorders_by_user_id);
			}, false)
	    }
	    var user_id = document.getElementById('input_user_id');
        if(user_id){
	    user_id.onchange = function(){
	    	show_workorders_by_user();
	    	update_user_name();
	    };
		}
	    var employee_id = document.getElementById('input_employee_id');
        if(employee_id){
	    employee_id.onchange = function(){
	    	show_workorders_by_employee();
	    	update_employee_name();
	    };
		}
    };

	document.addEventListener('DOMContentLoaded', function() {
		var input = document.getElementById("button_search");
		if (input){
			input.addEventListener("keyup", function(event) {
			    event.preventDefault();
			    if (event.keyCode === 13) {
			        document.getElementById("button_search").click();
			    }
			});
		}
	}, false);
});
