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
        var route = '/web/print_label/' + internal_ref[0].textContent;

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
        var wo_id = closestTr.getElementsByClassName('wo_id');
        var route = '/web/workorder_start/';
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
        var closestTr = button.closest('tr');
        var wo_id = closestTr.getElementsByClassName('wo_id');
        var route = '/web/workorder_pause/';
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
        var closestTr = button.closest('tr');
        var wo_id = closestTr.getElementsByClassName('wo_id');
        var route = '/web/workorder_resume/';
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
        var closestTr = button.closest('tr');
        var wo_id = closestTr.getElementsByClassName('wo_id');
        var n_pieces_to_produce = closestTr.getElementsByClassName('n_pieces_to_produce');
        var n_pieces = closestTr.getElementsByClassName('n_pieces');
        var pieces = n_pieces[0].valueAsNumber;
        var pieces_to_produce = parseFloat(n_pieces_to_produce[0].textContent);
        if (pieces != pieces_to_produce) {
        	alert("You have to produce the same number of pieces to produce!");
        	return;
        }
        var route = '/web/workorder_stop/';
		ajax.jsonRpc(route, 'call', {
			'wo_id' : wo_id[0].textContent,
			'n_pieces': pieces,
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
    	if ($.inArray(tdElem.textContent, ['draft', 'ready']) != -1) {
    		el_start_work[0].style.display = 'block';
    		el_pause_work[0].style.display = 'none';
    		el_resume_work[0].style.display = 'none';
    		el_stop_work[0].style.display = 'none';
    	}
    	else if ($.inArray(tdElem.textContent, ["startworking"]) != -1){
    		el_start_work[0].style.display = 'none';
    		el_pause_work[0].style.display = 'block';
    		el_resume_work[0].style.display = 'none';
    		el_stop_work[0].style.display = 'block';
    	}
    	else if ($.inArray(tdElem.textContent, ['progress']) != -1 & el_user_working[0].textContent == 'True'){
    		el_start_work[0].style.display = 'none';
    		el_pause_work[0].style.display = 'block';
    		el_resume_work[0].style.display = 'none';
    		el_stop_work[0].style.display = 'block';
    	}
    	else if ($.inArray(tdElem.textContent, ['pause', 'progress']) != -1 & el_user_working[0].textContent == 'False'){
    		el_start_work[0].style.display = 'none';
    		el_pause_work[0].style.display = 'none';
    		el_resume_work[0].style.display = 'block';
    		el_stop_work[0].style.display = 'none';
    	}
    	else {
    		el_start_work[0].style.display = 'none';
    		el_pause_work[0].style.display = 'none';
    		el_resume_work[0].style.display = 'none';
    		el_stop_work[0].style.display = 'none';
    	}
    	
    }

    function filter_res (button){
		console.log("clicked button")
        wo_id = document.getElementById('input_search_workorder_id');
		var wo_id = wo_id.valueAsNumber;
        wc_id = document.getElementById('input_search_worcenter_id');
		var wc_id = wc_id.valueAsNumber;
		var table_to_replace = document.getElementById('to_replace');
		console.log("getted value")
        if (isNaN(wo_id)){
    		wo_id = 0
    	}
        if (isNaN(wc_id)){
        	wc_id = 0
    	}
		var route = '/web/workorder_machine/' + wc_id + '/' + wo_id;

		ajax.jsonRpc(route, 'call', {
			
		}).then(function (data) {
			var doc = document.getElementById('to_replace');
			table_to_replace.innerHTML = data;
		    var print_label_list = document.getElementsByClassName('print_label');
		    var i0;
		    for (i0 = 0; i0 < print_label_list.length; i0++){
		    	print_label_list[i0].onclick = print_label;
		   }
		    var td_list = document.getElementsByClassName('wo_state');
		    var i;
		    for (i = 0; i < td_list.length; i++){
		   		state_changed(td_list[i]);
		   }
		    // Start work
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
		    // Stop Work
		    var i4;
		    var stop_work_butt_list = document.getElementsByClassName('stop_work')
		    for (i4 = 0; i4 < stop_work_butt_list.length; i4++){
		    	stop_work_butt_list[i4].onclick = stop_work1
		   }
	    });
	};

    window.onload = function() {
    console.log("omnia_workorder_machine.workorder_machine_list loaded")
    var _t = core._t;
    console.log("Start getting button")
    var button_search = document.getElementById('button_search');
    button_search.addEventListener("click", function() {
    	filter_res(button_search);
	}, false)
    };

	document.addEventListener('DOMContentLoaded', function() {
		var input = document.getElementById("button_search");
			input.addEventListener("keyup", function(event) {
		    event.preventDefault();
		    if (event.keyCode === 13) {
		        document.getElementById("button_search").click();
		    }
		});
		
	}, false);
});
