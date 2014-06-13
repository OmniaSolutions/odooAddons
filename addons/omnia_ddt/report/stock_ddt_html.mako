<html>
 <head>
        <meta content="text/html; charset=UTF-8" http-equiv="content-type"/>
        <script>
            function subst() {
            var vars={};
            var x=document.location.search.substring(1).split('&');
            for(var i in x) {var z=x[i].split('=',2);vars[z[0]] = unescape(z[1]);}
            var x=['frompage','topage','page','webpage','section','subsection','subsubsection'];
            for(var i in x) {
            var y = document.getElementsByClassName(x[i]);
            for(var j=0; j<y.length; ++j) y[j].textContent = vars[x[i]];
                }
            }
        </script>
<style>

p{
	
}
p.customer{
   	font:0.4cm arial,sans-serif;
   }
p.suTesto{
	font: 0.35cm arial,sans-serif;
}
p.suTesto.su{
	position:relative;
	vertical-align: top;
}
p.giuTesto{
	font: 0.3cm arial,sans-serif;

}
div{
	/*border: 0.5mm solid; activate for debugging porpouse*/
}
div.giuTesto{
	font: bold arial,sans-serif;
	text-align: center;
	font-size: 0.4cm;
	height: 4mm;
}
div.giuTesto.left{
	text-align: left;
	
}

div.myDiv{
	width: 30cm;
    height: 41cm;
}


div.customer_details{
	position:absolute;
	top:3cm;
	left:19.2cm;
    width: 11cm;
    height: 6.5cm;
}
div.body{
	position:absolute;
	top:10cm;
	width: 30cm;
}
div.body_footer{

}
div.body_footer2{

}
div.lower_char{
	margin-right:0.2cm;
    font:0.4cm arial,sans-serif;
    text-align: right;
    
}

table{
	border-collapse:collapse;
	width:100%;
	height: 100%;
}

table.customer_details{
	border-collapse:collapse;
	width:100%;
	height: 100%;
}
table.invoice_body{
	min-height:20cm;
	table-layout:fixed;
    height: 20cm;
    width:100%;
    border-collapse:collapse;
    border-top:    0.5mm solid; 
    border-bottom: 0.5mm solid;   
}
td.header_border{
	border:0.5mm solid;
	height: 10mm;
}
th.fattura_table_header{
    height:0.8cm;
    border:1px solid black;
    border-collapse:collapse;
    background-color:#E8E8FF;
    font-weight:bold;
}

td.header_border{
	border:0.5mm solid;
}
td.fattura_table{
	border-collapse:collapse;
	border:0.5mm solid;
	vertical-align:top;
	border-top:0px;
	border-bottom:0px;
	text-align: center;
}
td.fattura_table.left{
	text-align:left;
}
body
{
	background-repeat:no-repeat;
	background-position:center;
	background-attachment:fixed;
	background-size:10cm 10cm;

}
</style>
<head/>
    <body onload="subst()">
    <!-----  PROVIDE LINE BREAK FOR TEXT  ----->
<%
    def carriage_returns(text):
        return text.replace('\n', '<br />')
%>
    %for order in objects :

    <div class="myDiv" >
    	
		<%
		delivery_address=root_company=order.partner_id
		if order.delivery_address:
		    delivery_address=order.delivery_address
		else:    
		    if delivery_address.parent_id:
		        root_company=delivery_address.parent_id
		%>
		<div class="customer_details">
        	<table class="customer_details">
            	<tr>
                	<td class="header_border">
                  	<b><h>Spettabile:</h></b><br>
                    <p class="customer">
                    <b>${root_company.name |entity}</b><br/>
                    %if root_company.street :
   						${root_company.street or ''|entity}<br>  
					%endif
					%if root_company.street2 :
   						${root_company.street2 or ''|entity}<br>  
					%endif
   					%if root_company.zip :
   						${root_company.zip or ''|entity}
					%endif 
					%if root_company.city :
   						${root_company.city or ''|entity}
					%endif  
					%if root_company.state_id :
					   	(${root_company.state_id.name or ''|entity}) 
					%endif 
					<br> 
					%if root_company.country_id.code :
  						%if root_company.country_id.code != 'CH':
     						${root_company.country_id.code} - ${order.partner_id.country_id.name}<br/>
  						%endif  
					%endif
					</p>
					</td>
				</tr>
				<tr>
					<td class="header_border">
					<b><h>Destinatario:</h></b><br>
					<p class="customer">
					%if order.delivery_address:
						<b>${delivery_address.name |entity}</b><br>  
					%endif
					%if delivery_address.street :
					   ${delivery_address.street or ''|entity}<br>  
					%endif
					%if delivery_address.street2 :
					   ${delivery_address.street2 or ''|entity}<br>  
					%endif
					   %if delivery_address.zip :
					   ${delivery_address.zip or ''|entity}
					%endif 
					%if delivery_address.city :
					   ${delivery_address.city or ''|entity}  
					%endif 
					%if delivery_address.state_id :
					   	(${delivery_address.state_id.name or ''|entity})
					%endif
					<br>  
					%if delivery_address.country_id.code :
					  %if delivery_address.country_id.code != 'CH':
					     ${delivery_address.country_id.code} - ${order.partner_id.country_id.name}<br/>
					  %endif  
					%endif
					</p>
					</td>
				</tr>
			</table>
		</div>	
		<!-- Body -->
		<div class="body">
        <!-- heder corpo fattura -->
        <div style="height:16mm;">
        <table class="customer_details" >
             <colgroup>
	             	<col width="40%">
					<col width="23%">
					<col width="17%">
					<col width="10%"> 
					<col width="10%">     
	          </colgroup>
              <tr >
                <td class="header_border">
                	<h1 style="font-size:8mm; line-height: 0mm; vertical-align: top; position: relative;top: 3mm;">Documento di trasporto</h1>
                    <p  style="line-height: 0mm; vertical-align: top; font-size: 4mm">(D.P.R. 472 del 14-08-1996 - D.P.R. 696 del 21-12-1996)</p>
                </td>
                <td  class="header_border">
                    <p class="suTesto su">Causale di trasporto</p>
                    <div class="giuTesto left">
					%if order.transportation_reason_id :
   						${order.transportation_reason_id.name or ''}
					%endif
					</div>
                </td>
                <td  class="header_border">
                    <p class="suTesto su">Data del documento</p>
                    <div class="giuTesto">
					%if order.ddt_date :
   						${order.ddt_date or ''|entity}
					%endif
					</div>
                </td>
                <td class="header_border">
                    <p class="suTesto su">N&deg; Documento</p>
                    <div class="giuTesto">
                    %if order.ddt_number :
   						${order.ddt_number or ''|entity}
					%endif
					</div>
                </td>
                <td  class="header_border"  >
                    <p>Pag ${loop.index+1} / ${len(objects)}</p>
                </td>
               </tr>              
        </table>
		</div>
<!-- corpo ordine -->
        <table class="customer_details">
             <colgroup>
	             	<col width="12%">
					<col width="16%">
					<col width="28%">
					<col width="44%">   
	          </colgroup>
              <tr>

                <td class="header_border" style="border-top: 0mm;"  >
                    <p class="suTesto">Partita IVA o Codice Fiscale</p>
                    <div class="giuTesto">
                    %if order.partner_id.vat:
   						${order.partner_id.vat or ''}
					%endif
					</div>
                </td>
                <td class="header_border"  style="border-top: 0mm;" >
                    <p class="suTesto">Agente</p>
                    <div class="giuTesto">
					</div>
                </td>
                <td class="header_border" style="border-top: 0mm;"  >
                    <p class="suTesto">Annotazioni</p>
                    <div class="giuTesto">
                    %if order.note_ddt:
   						${order.note_ddt or ' '}
					%endif
					</div>
                </td>
                </tr>    
        </table>

        <table class="invoice_body">
	        <colgroup>
	             	<col width="12%">
					<col width="68%">
					<col width="10%">
					<col width="10%">    
	        </colgroup>
            <tr>

                <th class="fattura_table_header">Cod Art.<br/>/commessa</th>
                <th class="fattura_table_header">Descrizione</th>
                <th class="fattura_table_header">U.M.</th>
                <th class="fattura_table_header">Q.t&agrave;</th>
                
            </tr>
            <!-- +++++ qui ci devo mettere il loop per scrivere le info -->
            <tr>
                <td class="fattura_table"></td>
                <td class="fattura_table"></td>
                <td class="fattura_table"></td>
                <td class="fattura_table"></td>
            </tr>
<!-- loop dorder line -->
			%for move_line in order.move_lines:
	            <tr>
	                <td class="fattura_table left">${move_line.product_id.default_code or ""}</td>
	                <td class="fattura_table left">${move_line.product_id.name or ""}</td>
	                <td class="fattura_table">${move_line.product_uom.name or ""}</td>
	                <td class="fattura_table">${move_line.product_qty.name or ""}</td>
	            </tr>
	        %endfor
	        <tr  style="min-height:515px; height:515px">
                <td class="fattura_table"></td>
                <td class="fattura_table"></td>
                <td class="fattura_table"></td>
                <td class="fattura_table"></td>
            </tr>
        </table> 
        <br/>
        <div class="body_footer">
        <table class="customer_details">
        	 <colgroup>
        	 		<col width="43%">
	             	<col width="15%">
					<col width="17%">
					<col width="5%">
					<col width="20%">    
	        </colgroup>
            <tr>
            	<td class="header_border">
                    <p class="suTesto su">Aspetto esteriore dei beni</p>
                    <div class="giuTesto">
                    %if order.goods_description_id:
                    	${order.goods_description_id.name or ''}
                    %endif
					</div>
                </td>
                <td class="header_border" >
                    <p class="suTesto su">Volume[dm3]</p>
                    <div class="giuTesto">
                    %if order.volume:
                    	${order.volume or ''}
                    %endif
					</div>
                </td>
                <td class="header_border" >
                    <p class="suTesto su">Peso[Kg]</p>
                    <div class="giuTesto">
                    %if order.weight:
                    	${order.weight or ''}
                    %endif
					</div>
                </td>
                <td class="header_border" >
                    <p class="suTesto su">N. Colli</p>
                    <div class="giuTesto">
                    %if order.number_of_packages:
                    	${order.number_of_packages or ''}
                    %endif
					</div>
                </td>
                <td class="header_border" >
                </td>
            </tr>
       </table>
	</div>
	<div class="body_footer2">
		<div style="height: 4mm;"></div>
       	<table class="header_noBorder">
            <tr>
                <td class="header_border">
                    <p class="suTesto su">Porto</p>
                    <div class="giuTesto">
                    %if order.carriage_condition_id:
                    	${order.carriage_condition_id.name or ''}
                    %endif
					</div>
                </td>
                <td class="header_border" width="15%">
                    <p class="suTesto su">Trasporto a cura del</p>
                    <div class="giuTesto">
                    	${order.ddt_reason or ''}
					</div>
                </td>
                <td class="header_border" width="15%">
                    <p class="suTesto su">Data Ora del Ritiro</p>
                    <div class="giuTesto">
					</div>
                </td>
                <td class="header_border" width="17%">
					
                </td>
                <td class="header_border" width="25%">
                    <p class="suTesto su">Firma del Conducente</p>
                    <div class="giuTesto">
					</div>
                </td>
            </tr>
       </table>
       <table class="header_noBorder" >     
            <tr>
                <td class="header_border" style="border-top: 0mm;" >
                    <p class="suTesto su">Vettore</p>
                    <div class="giuTesto">
					</div>
                </td>
                <td class="header_border" style="border-top: 0mm;" width="17%">
                    <p class="suTesto su">Data Ora Ritiro</p>
                    <div class="giuTesto">
					</div>
                </td>
                 <td class="header_border" style="border-top: 0mm;" width="25%">
                    <p class="suTesto su">Firma</p>
                    <div class="giuTesto">
					</div>
                </td>
            </tr>
       </table>
       <table class="header_noBorder">
            <tr>
                <td class="header_border" style="border-top: 0mm;" >
                    <p class="suTesto su">Vettore</p>
                    <div class="giuTesto">
					</div>
                </td>
                <td class="header_border" style="border-top: 0mm;" width="17%">
                    <p class="suTesto su">Data Ora Ritiro</p>
                    <div class="giuTesto">
					</div>
                </td>
                 <td class="header_border" style="border-top: 0mm;" width="25%">
                    <p class="suTesto su">Firma</p>
                    <div class="giuTesto">
					</div>
                </td>
            </tr>
        </table>
        <table class="header_noBorder">
            <tr>
				<td class="header_border" style="border-top: 0mm;" width="75%">
                </td>
                <td class="header_border" style="border-top: 0mm;" width="25%">
                    <p class="suTesto su">Firma del Destinatario</p>
                    <div class="giuTesto">
					</div>
                </td>
            </tr>
        </table> 
        </div>       
		</div> 
		</div>
		<p style="page-break-after:always"></p> 
	%endfor      
    </body>
</html>