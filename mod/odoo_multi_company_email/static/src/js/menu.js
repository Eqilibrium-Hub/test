odoo.define('odoo_multi_company_email.SwitchCompanyMenu', function (require) {
    "use strict";

    const { SwitchCompanyMenu } = require("@web/webclient/switch_company_menu/switch_company_menu");
    const { patch } = require('web.utils');
    const { session } =  require("@web/session");
    const rpc  = require('web.rpc');

    function onSwitchCompanyClick(companyId) {
        var self = this;
        return rpc.query({
            model: 'res.users',
            method: 'on_switch_company_click',
            args: [session.uid, companyId],
        })
    }

    patch(SwitchCompanyMenu.prototype, 'odoo_multi_company_email.SwitchCompanyMenu', {

        logIntoCompany(companyId) {             
            if (companyId){
                onSwitchCompanyClick(companyId);
            }
            this._super(...arguments);         
        }
    });

});