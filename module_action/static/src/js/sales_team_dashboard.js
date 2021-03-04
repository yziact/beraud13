odoo.define('module_action.sales_team_dashboard', function (require) {
"use strict";

var SalesTeamDashboardView = require('sales_team.dashboard');
var Model = require('web.Model');
var session = require('web.session');
var client = require('web.web_client')
var formats = require('web.formats');
var core = require('web.core');
var KanbanView = require('web_kanban.KanbanView');

SalesTeamDashboardView.include({

    fetch_data: function() {
        return new Model('crm.lead')
            .call('retrieve_action_dashboard', []);
    },

    on_dashboard_action_clicked: function(ev){
        ev.preventDefault();

        var $action = $(ev.currentTarget);
        var action_name = $action.attr('name');
        var action_extra = $action.data('extra');
        var additional_context = {};

        // TODO: find a better way to add defaults to search view
        if (action_name === 'calendar.action_calendar_event') {
            additional_context.search_default_mymeetings = 1;
        } else if (action_name === 'module_action.crm_lead_action_activities') {
            if (action_extra === 'today') {
                additional_context.search_default_today = 1;
            } else if (action_extra === 'this_week') {
                additional_context.search_default_this_week = 1;
            } else if (action_extra === 'overdue') {
                additional_context.search_default_overdue = 1;
            }
        } else if (action_name === 'crm.action_your_pipeline') {
            if (action_extra === 'overdue') {
                additional_context['search_default_overdue'] = 1;
            } else if (action_extra === 'overdue_opp') {
                additional_context['search_default_overdue_opp'] = 1;
            }
        } else if (action_name === 'crm.crm_opportunity_report_action_graph') {
            additional_context.search_default_won = 1;
        }

        this.do_action(action_name, {additional_context: additional_context});
    },

});
core.view_registry.add('yziact_dashboard_inherit', SalesTeamDashboardView);

return SalesTeamDashboardView
});
