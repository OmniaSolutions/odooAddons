<html>
<head>
    <style type="text/css">
        ${css}
    </style>
</head>
<body >
	%for employee in get_employees(data['form']['emp_ids']) :
		<br/>
		<br/>
		<center><h2>Attendance Errors</h2></center>
		<h4>${employee.name}
		<br/>
		<br/>
		<table class="list_table" width="100%" align="center">
    		<thead>
    			<tr>
	    			<th style="text-align:left;" width="25%">${_("Operation")}</th>
	    			<th style="text-align:center;" width="15%">${_("Date Signed")}</th>
	    			<th style="text-align:center;" width="15%">${_("Date Recorded")}</th>
	    			<th style="text-align:center;" width="20%">${_("Delay")}</th>
	    			<th style="text-align:center;" width="25%">${_("Min Delay")}</th>
    			</tr>
    		</thead>
			%for att in (lst(employee.id,data['form']['init_date'], data['form']['end_date'], data['form']['max_delay'])):
    			<tbody>
            	<tr>
	                <td style="text-align:left;">
	                	${att['action'] or '' |entity}
					 </td>
            		<td style="text-align:center;">
            			${formatLang(att['date'],date_time=True) or '' |entity} 
            		</td>
            		<td style="text-align:center;">
            			${formatLang(att['create_date'],date_time=True) or '' |entity} 
            		</td>
            		<td style="text-align:center;">
            			${att['delay'] or '' |entity} 
            		</td>
            		<td style="text-align:center;">
            			${att['delay2'] or '' |entity} 
            		</td>
            	</tr>
            	</tbody>			
			%endfor
			<table class="list_table" width="100%" style="border-top:2px solid black">
    			<thead>
    				<tr>
    					%for t in total(employee.id,data['form']['init_date'], data['form']['end_date'], data['form']['max_delay']):
    						<td style="text-align:left;" width="25%"><b>${_("Total period:")}</b></td>
    						<td style="text-align:center;" width="15%"></td>
    						<td style="text-align:center;" width="15%"></td>
	    					<td style="text-align:center;" width="20%">${t['total']}</td>
	    					<td style="text-align:center;" width="25%">${t['total2']}</td>
	    				%endfor
    				</tr>
    			</thead>
			</table>
		</table>
		<br/><br/>
		${_("(*) A positive delay means that the employee worked less than recorded.")}<br/>
		${_("(*) A negative delay means that the employee worked more than encoded.")}
		<p style="page-break-after:always"></p>
	%endfor
</body>
</html>