/** @odoo-module **/

import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { Component, onMounted, useState } from "@odoo/owl";

export class WorkorderMachineList extends Component {
//    static template = "omnia_workorder_machine.template_workorder_machine";
    setup() {
        console.log(' Indide component called ......')
        this.state = useState({ workorders: [] });
        onMounted(() => {
            this.filterWorkorders();
            this.updateUserName();
        });
    }

    download(data, filename, type) {
        const file = new Blob([data], { type: type });
        if (window.navigator.msSaveOrOpenBlob) {
            window.navigator.msSaveOrOpenBlob(file, filename);
        } else {
            const a = document.createElement("a");
            const url = URL.createObjectURL(file);
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            setTimeout(() => {
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }, 0);
        }
    }

    async printLabel(button) {
        const closestTr = button.currentTarget.closest('tr');
        const internal_ref = closestTr.getElementsByClassName('internal_ref')[0].textContent;
        const route = `/web/print_label/${internal_ref}`;

        try {
            const response = await fetch(route);
            const blob = await response.blob();
            this.download(blob, 'label.pdf', 'application/pdf');
        } catch (err) {
            console.error('Error printing label', err);
        }
    }

    async startWork(button) {
        const closestTr = button.currentTarget.closest('tr');
        const wo_id = closestTr.getElementsByClassName('wo_id')[0].textContent;
        await rpc('/web/workorder_start/', 'call', { wo_id });
        this.filterWorkorders();
    }

    async pauseWork(button) {
        const closestTr = button.currentTarget.closest('tr');
        const wo_id = closestTr.getElementsByClassName('wo_id')[0].textContent;
        await rpc('/web/workorder_pause/', 'call', { wo_id });
        this.filterWorkorders();
    }

    async resumeWork(button) {
        const closestTr = button.currentTarget.closest('tr');
        const wo_id = closestTr.getElementsByClassName('wo_id')[0].textContent;
        await rpc('/web/workorder_resume/', 'call', { wo_id });
        this.filterWorkorders();
    }

    async stopWork(button) {
        const closestTr = button.currentTarget.closest('tr');
        const wo_id = closestTr.getElementsByClassName('wo_id')[0].textContent;
        const n_pieces = closestTr.getElementsByClassName('n_pieces')[0].valueAsNumber;
        const n_scrap = closestTr.getElementsByClassName('n_scrap')[0].valueAsNumber;
        await rpc('/web/workorder_record/', 'call', { wo_id, n_pieces, n_scrap });
        this.filterWorkorders();
    }

    filterRes() {
        console.log(".................filterres this", this)
        const woInput = document.getElementById('input_search_workorder_id');
        const wcInput = document.getElementById('input_search_worcenter_id');
        const wo_id = woInput?.valueAsNumber || 0;
        const wc_id = wcInput?.valueAsNumber || 0;

        const route = `/web/workorder_machine/${wc_id}/${wo_id}`;
        rpc(route, 'call', {}).then(data => this.updateWorkorderTable(data));
    }

    async showWorkordersByUser() {
        const user_id = document.getElementById('input_user_id')?.valueAsNumber;
        if (!user_id) return;
        const route = `/web/render_workorder_by_user/${user_id}`;
        const data = await rpc(route, 'call', {});
        this.updateWorkorderTable(data);
    }

    async updateUserName() {
        const user_id = document.getElementById('input_user_id')?.valueAsNumber;
        if (!user_id) return;
        const route = `/web/get_user_name/${user_id}`;
        const name = await rpc(route, 'call', {});
        const p_user_name = document.getElementById('user_name');
        if (p_user_name) p_user_name.innerHTML = name;
    }

    updateWorkorderTable(data) {
        const tableToReplace = document.getElementById('to_replace');
        if (!tableToReplace) return;
        tableToReplace.innerHTML = data;

        // Attach events
        [...document.getElementsByClassName('print_label')].forEach(btn => btn.onclick = e => this.printLabel(e));
        [...document.getElementsByClassName('start_work')].forEach(btn => btn.onclick = e => this.startWork(e));
        [...document.getElementsByClassName('pause_work')].forEach(btn => btn.onclick = e => this.pauseWork(e));
        [...document.getElementsByClassName('resume_work')].forEach(btn => btn.onclick = e => this.resumeWork(e));
        [...document.getElementsByClassName('stop_work')].forEach(btn => btn.onclick = e => this.stopWork(e));

        // Update row states
        [...document.getElementsByClassName('wo_state')].forEach(td => this.stateChanged(td));
    }

    stateChanged(tdElem) {
        const closestTr = tdElem.closest('tr');
        const el_user_working = closestTr.getElementsByClassName('wo_isuserworking')[0];
        const el_start_work = closestTr.getElementsByClassName('start_work')[0];
        const el_pause_work = closestTr.getElementsByClassName('pause_work')[0];
        const el_resume_work = closestTr.getElementsByClassName('resume_work')[0];
        const el_stop_work = closestTr.getElementsByClassName('stop_work')[0];

        const state = tdElem.textContent;
        const userWorking = el_user_working?.textContent === 'True';

        if (['draft', 'ready'].includes(state)) {
            el_start_work.style.display = 'block';
            el_pause_work.style.display = 'none';
            el_resume_work.style.display = 'none';
            el_stop_work.style.display = 'none';
        } else if (state === 'startworking') {
            el_start_work.style.display = 'none';
            el_pause_work.style.display = 'block';
            el_resume_work.style.display = 'none';
            el_stop_work.style.display = 'block';
        } else if (state === 'progress' && userWorking) {
            el_start_work.style.display = 'none';
            el_pause_work.style.display = 'block';
            el_resume_work.style.display = 'none';
            el_stop_work.style.display = 'block';
        } else if (['pause', 'progress'].includes(state) && !userWorking) {
            el_start_work.style.display = 'none';
            el_pause_work.style.display = 'none';
            el_resume_work.style.display = 'block';
            el_stop_work.style.display = 'none';
        } else {
            el_start_work.style.display = 'none';
            el_pause_work.style.display = 'none';
            el_resume_work.style.display = 'none';
            el_stop_work.style.display = 'none';
        }
    }

    initEvents() {
        window.onload = () => {
            document.getElementById('button_search')?.addEventListener('click', () => this.filterRes());
            document.getElementById('show_workorders_by_user')?.addEventListener('click', () => this.showWorkordersByUser());
            const userInput = document.getElementById('input_user_id');
            if (userInput) {
                userInput.onchange = () => {
                    this.showWorkordersByUser();
                    this.updateUserName();
                };
            }

            document.getElementById('button_search')?.addEventListener('keyup', e => {
                if (e.key === 'Enter') this.filterRes();
            });
        };
    }
}

