import json
import odoo.addons.report.controllers.main as main
from odoo.http import Controller, route, request

class Extension(main.ReportController):

    @route(['/report/download'], type='http', auth="user")
    def report_download(self, data, token):
        no_json_data = json.loads(data)
        url, type = no_json_data[0], no_json_data[1]
        if type == 'qweb-pdf':
            base_url =  url.rsplit("/",1)[0]
            reportname = url.split('/report/pdf/')[1].split('?')[0]
            docids = None
            if '/' in reportname:
                reportname, docids = reportname.split('/')
            out_doc_ids = []
            for doc in docids.split(","):
                if doc.index("-")>0:
                    out_doc_ids.append(doc.split("-")[0])
                else:
                    out_doc_ids.append(doc)
            if out_doc_ids:
                new_url = "%s/%s" % (base_url, ",".join(out_doc_ids))
                data = json.dumps([new_url, no_json_data[1]])
        return super(Extension, self).report_download(data, token)