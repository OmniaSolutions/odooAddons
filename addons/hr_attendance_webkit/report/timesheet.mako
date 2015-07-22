<html>
<head>
    <style type="text/css">
        ${css}
    </style>
</head>
<body >
		
% for emp_data in get_emp_ids(data):
		<br/><br/>
		<center><h2> Attendances by Week </h2></center>
		<br/><br/>
		<b>${_("Employee")} :</b>${get_emp_name(emp_data)}
		<br/><br/>
	%for day in range(len(get_week(data)[0])):
		<table class="list_table">
	 		<tr>
				<td style="background-color:FFFFFF;" width="30%">
				<%
					from dateutil.relativedelta import relativedelta
					first_date = ''
					last_date = ''
					first_date = get_week(data)[0][day].strftime('%Y-%m-%d')
					last_date = (get_week(data)[2][day] - relativedelta(days=1)).strftime('%Y-%m-%d')
				%>
				
					<b>${"From"} ${first_date} ${"to"} ${last_date}</b>
				</td>
				<td>
					${_("Mon")}
				</td>
				<td>
					${_("Tue")}
				</td>
				<td>
					${_("Wed")}
				</td>
				<td>
					${_("Thus")}
				</td>
				<td>
					${_("Fri")}
				</td>
				<td>
					${_("Sat")}
				</td>
				<td>
					${_("sun")}
				</td>
				<td>
					${_("Total")}
				</td>
	 		</tr>
			<tr>
			<td style="background-color:FFFFFF;" width="30%">
				${"Worked Hours"}
			</td>
			<% total=0.0 %>
			%for emp in range(7):
				<% 
					dayhr=0.0
					if emp in (get_attandance(emp_data, get_week(data)[0][day], get_week(data)[1][day])): 
					    
						dayhr = get_attandance(emp_data, get_week(data)[0][day], get_week(data)[1][day])[emp]
						total=total +dayhr
				%>
					<td style="background-color:FFFFFF;" width="9%">
							${hour2str(dayhr)}
					</td>
			%endfor
			<td style="background-color:FFFFFF;">
				${hour2str(total)}
			</td>
			</tr>
	 </table>
	 %endfor
<p style="page-break-after:always"></p>	
%endfor
</body>
</html>