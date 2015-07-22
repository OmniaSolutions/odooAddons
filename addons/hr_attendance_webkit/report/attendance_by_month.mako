<html>
<head>
    <style type="text/css">
        ${css}
    </style>
</head>
<body >
        <br/>
		<center><h2> Attendances by Month </h2></center>
		<br/><br/><br/>
		<table class="list_table" width="100%">
			<tr>
				<td width="15%" style="font-size:18px;"><b>${data['form']['year']}</b></td>
				<%month =1%>
				%for month in range(lengthmonth(data['form']['year'],data['form']['month'])):
					<td width="2.5%" ><b>${get_day_name(data['form']['year'],data['form']['month'],month+1)}</b></td>
				%endfor
					<td><b>${_("Total")}</b></td>
			</tr>
			<tr>
				<td  style="font-size:12px;">${get_month_year(data['form']['year'],data['form']['month'])}</td>
				%for month in range(lengthmonth(data['form']['year'],data['form']['month'])):
					<td width="2.5%" >${month +1 }</td>
				%endfor
				<td ><b></b></td>
			</tr>
			%for emp_data in get_emp_ids(data):
				<tr>
					<td style="text-align:left;background-color:FFFFFF;color:169111;font-size:18px;">${get_emp_data(emp_data,data)[1][0]}</td>
				%for emp in range(len(get_emp_data(emp_data,data)[0])):
					<td td width="2.5%" style="text-align:right; background-color:FFFFFF;padding-right:3px;">${get_emp_data(emp_data,data)[0][emp]}</td>
				%endfor
					<td><b>${get_emp_data(emp_data,data)[2]}</b></td>
				</tr>
			%endfor
		</table>
</body>
</html>