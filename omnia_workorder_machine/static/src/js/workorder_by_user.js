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

	function get_user_id(){
		var user_id_num = 0;
        var user_id = document.getElementById('input_user_id');
        if (user_id != null){
			user_id_num = user_id.valueAsNumber;
		}
		return user_id_num
	}

	function get_employee_id(){
		var user_id_num = 0;
        var user_id = document.getElementById('input_employee_id');
        if (user_id != null){
			user_id_num = user_id.valueAsNumber;
		} else{
    		var user_id = document.getElementById('input_search_employee_id')
    		if (user_id != null){
                user_id_num = user_id.getAttribute("odooid");
            }
        }
		if(user_id_num==0 || user_id_num==null){
            alert("Error !!!\nin order to proceed set the employee !!");
            throw new Error("Missing emploee !");
        }
		
		return user_id_num
	}

	function show_clock(){
        var clock = document.getElementById('waiting_clock');
        clock.style.visibility = 'visible';
	clock.style.display = 'block';
	clock.style.width = '80px';
	}


	function hide_clock(){
        var clock = document.getElementById('waiting_clock');
        clock.style.visibility = 'hidden';
	}

    function start_work1 (button) {
        console.log("Start working");
        var button = button.currentTarget;
        var closestTr = button.closest('tr');
        closestTr.style.cursor ='wait';
        button.style.display = 'none';
        var wo_id = closestTr.getElementsByClassName('wo_id');
        var route = '/mrp_omnia/workorder_start/';
        show_clock();
        var emploeey_id=0
        if(document.URL.search("workorder_by_user")<0){
            emploeey_id=get_employee_id()
        }
		ajax.jsonRpc(route, 'call', {
			'wo_id' : wo_id[0].textContent,
			'user_id': get_user_id(),
			'employee_id': emploeey_id,
		}).then(function (data) {
			hide_clock();
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
        show_clock();
        var emploeey_id=0
        if(document.URL.search("workorder_by_user")<0){
            emploeey_id=get_employee_id()
        }
		ajax.jsonRpc(route, 'call', {
			'wo_id' : wo_id[0].textContent,
			'user_id': get_user_id(),
			'employee_id': emploeey_id,
		}).then(function (data) {
			hide_clock();
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
        show_clock();
        var emploeey_id=0
        if(document.URL.search("workorder_by_user")<0){
            emploeey_id=get_employee_id()
        }
		ajax.jsonRpc(route, 'call', {
			'wo_id' : wo_id[0].textContent,
			'user_id': get_user_id(),
			'employee_id': emploeey_id,
		}).then(function (data) {
			hide_clock();
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
        show_clock();
        var emploeey_id=0
        if(document.URL.search("workorder_by_user")<0){
            emploeey_id=get_employee_id()
        }
    		ajax.jsonRpc(route, 'call', {
    			'wo_id' : wo_id[0].textContent,
    			'n_pieces': pieces,
    			'n_scrap': n_scrap,
    			'user_id': get_user_id(),
    			'employee_id': emploeey_id,
    		}).then(function (data) {
    			hide_clock();
    			filter_res(null);
    		   }
    	    ).catch (function (data) {
                alert("Errore Server " + data.message.data.message);
                hide_clock();
                filter_res(null);
            });
    	    
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
    	
    	// Start work
    	if ($.inArray(tdElem.textContent, ['ready']) != -1) {
    		el_start_work[0].style.display = 'block';
    		el_pause_work[0].style.display = 'none';
    		el_resume_work[0].style.display = 'none';
    		el_stop_work[0].style.display = 'none';
    		input_qty.style.display = 'none';
    		scrap_qty.style.display = 'none';
    	}
    	
    	// Pause work
    	else if ($.inArray(tdElem.textContent, ['progress']) != -1 & el_user_working[0].textContent == 'True'){
    		el_start_work[0].style.display = 'none';
    		el_pause_work[0].style.display = 'block';
    		el_resume_work[0].style.display = 'none';
    		el_stop_work[0].style.display = 'block';
    		input_qty.style.display = 'block';
    		scrap_qty.style.display = 'block';
    	}
    	
    	// Resume Work
    	else if ($.inArray(tdElem.textContent, ['pause', 'progress']) != -1 & el_user_working[0].textContent == 'False'){
    		el_start_work[0].style.display = 'none';
    		el_pause_work[0].style.display = 'none';
    		el_resume_work[0].style.display = 'block';
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
		show_clock();
		ajax.jsonRpc(route, 'call', {}).then(function (data) {
			hide_clock();
			updete_workorder(data);
		});
    }
    
    function update_wo_all(){
        var mo = document.getElementById('input_search_mo_id');
        if(mo){
            var mo_id = mo.getAttribute('odooid')
            if (mo_id==null || mo.value  === undefined){
                mo_id=0
            }
            var wc = document.getElementById('input_search_wc_id');
            var wc_id = wc.getAttribute('odooid')
            if (wc_id==0 || wc.value  === undefined){
                wc_id=0
            }
            var route = '/mrp_omnia/render_workorder_all/' + mo_id + "/" + wc_id;
            show_clock();
            ajax.jsonRpc(route, 'call', {}).then(function (data) {
                hide_clock();
                updete_workorder(data);
            });
        }
    }
  
    function show_workorders_by_employee(){
    	var user_id = document.getElementById('input_employee_id');
    	if(user_id){
    		var route = '/mrp_omnia/render_workorder_by_employee/' + user_id.valueAsNumber;
    		show_clock();
    		ajax.jsonRpc(route, 'call', {}).then(function (data) {
    			hide_clock();
    			updete_workorder(data);
    		});
		}
    }
  
  
    function filter_res(button) {
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
			var user_id = document.getElementById('input_user_id');
			if (user_id == null){
				show_workorders_by_employee();
			}
			else{
				show_workorders_by_user();
			}
		}
		update_wo_all();
	};
	
	var updete_workorder = function (data) {
		var t_body = document.getElementById('workorder_body');
		t_body.innerHTML = data;
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
    	if (user_id){
            if(user_id.value==''){
                return;
            }
        }
    	var user_id_n = user_id.valueAsNumber;
    	var route = '/mrp_omnia/get_employee_name/' + user_id_n;
		ajax.jsonRpc(route, 'call', {}).then(function (data) {
			var p_user_name = document.getElementById('user_name');
			p_user_name.innerHTML = data;
			update_wo_all();
		});
    }
    
    async function name_get_generic(object_name, name_like, depend_function_domain){
        var route = '/mrp_omnia/name_get_generic/' + object_name + '/' + name_like;
        if (depend_function_domain){
            var extra_domain = depend_function_domain()
            route += '/' + JSON.stringify(extra_domain);
        }
        return ajax.jsonRpc(route,
                           'call');
    }
    
    function autocomplete(inp,
                          odoo_object,
                          depend_function_domain,
                          update_table_function) {
      /*the autocomplete function takes two arguments,
      the text field element and an array of possible autocompleted values:*/
      var currentFocus;
      /*execute a function when someone writes in the text field:*/
      inp.addEventListener("input", function(e) {
          var self = this;
          var a, b, i, val = self.value;
          /*close any already open lists of autocompleted values*/
          closeAllLists();
          if (!val) {
                    inp.setAttribute("odooid",0);
                    if (update_table_function){
                        update_table_function(inp);
                        }
                    return false;
                    }
          currentFocus = -1;
          /*create a DIV element that will contain the items (values):*/
          name_get_generic(odoo_object, val, depend_function_domain).then(function(data){
              var arr = data['data'];
              a = document.createElement("DIV");
              a.setAttribute("id", self.id + "autocomplete-list");
              a.setAttribute("class", "autocomplete-items");
              /*append the DIV element as a child of the autocomplete container:*/
              self.parentNode.appendChild(a);
              /*for each item in the array...*/
              for (i = 0; i < arr.length; i++) {
                  /*create a DIV element for each matching element:*/
                  b = document.createElement("DIV");
                  /*make the matching letters bold:*/
                  b.innerHTML = "<strong>" + arr[i][1] + "</strong>";
                  /*insert a input field that will hold the current array item's value:*/
                  b.innerHTML += "<input type='hidden' value='" + arr[i][1] + "' odooid=" + arr[i][0] + ">";
                  /*execute a function when someone clicks on the item value (DIV element):*/
                  b.addEventListener("click", function(e) {
                      /*insert the value for the autocomplete text field:*/
                      inp.value = this.getElementsByTagName("input")[0].value;
                      inp.setAttribute("odooid", this.getElementsByTagName("input")[0].getAttribute('odooid'))
                      /*close the list of autocompleted values,
                      (or any other open lists of autocompleted values:*/
                      closeAllLists();        
                      if (update_table_function){
                        update_table_function(inp);
                      }
                  });
                  a.appendChild(b);
              }
          });
      });
      /*execute a function presses a key on the keyboard:*/
      inp.addEventListener("keydown", function(e) {
          var x = document.getElementById(this.id + "autocomplete-list");
          if (x) x = x.getElementsByTagName("div");
          if (e.keyCode == 40) {
            /*If the arrow DOWN key is pressed,
            increase the currentFocus variable:*/
            currentFocus++;
            /*and and make the current item more visible:*/
            addActive(x);
          } else if (e.keyCode == 38) { //up
            /*If the arrow UP key is pressed,
            decrease the currentFocus variable:*/
            currentFocus--;
            /*and and make the current item more visible:*/
            addActive(x);
          } else if (e.keyCode == 13) {
            /*If the ENTER key is pressed, prevent the form from being submitted,*/
            e.preventDefault();
            if (currentFocus > -1) {
              /*and simulate a click on the "active" item:*/
              if (x) x[currentFocus].click();
            }
          }
      });
      function addActive(x) {
        /*a function to classify an item as "active":*/
        if (!x) return false;
        /*start by removing the "active" class on all items:*/
        removeActive(x);
        if (currentFocus >= x.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = (x.length - 1);
        /*add class "autocomplete-active":*/
        x[currentFocus].classList.add("autocomplete-active");
      }
      function removeActive(x) {
        /*a function to remove the "active" class from all autocomplete items:*/
        for (var i = 0; i < x.length; i++) {
          x[i].classList.remove("autocomplete-active");
        }
      }
      function closeAllLists(elmnt) {
        /*close all autocomplete lists in the document,
        except the one passed as an argument:*/
        var x = document.getElementsByClassName("autocomplete-items");
        for (var i = 0; i < x.length; i++) {
          if (elmnt != x[i] && elmnt != inp) {
          x[i].parentNode.removeChild(x[i]);
        }
      }
    }
    /* execute a function when someone clicks in the document: */
    document.addEventListener("click", function (e) {
        closeAllLists(e.target);
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


        var wo_ma_search_submit = document.getElementById('wo_ma_search_submit');
        if(wo_ma_search_submit){
            wo_ma_search_submit.onchange = function(){
                render_workorder_all();
            };
        }
        
	    var employee_id = document.getElementById('input_search_employee_id');
         if(employee_id){
            autocomplete(employee_id, 'hr.employee');
            };

        var mo_wc = document.getElementById('input_search_wc_id');
         if(mo_wc){
            autocomplete(mo_wc, 'mrp.workcenter', null, update_wo_all);
            };

        var mo_id = document.getElementById('input_search_mo_id');
         if(mo_id){
            var extra_domain_function = function(){
                return ['state','in',['confirm','progress','planned']]
            } 
            autocomplete(mo_id, 'mrp.production', extra_domain_function, update_wo_all);
            };
        var search_bnt = document.getElementById('search_all');
        if(search_bnt){
            search_bnt.onclick=update_wo_all;
	       }
	    
	    var employee_id = document.getElementById('input_employee_id');
        if(employee_id){
        employee_id.onchange = function(){
            show_workorders_by_employee();
            update_employee_name();
        };}
    };

	document.addEventListener('DOMContentLoaded', function() {
        var user_id = document.getElementById('input_employee_id')
        if (user_id){
            user_id.addEventListener("change",update_employee_name);
        }
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
