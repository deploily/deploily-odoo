# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models

# Expense states that shouldn't count towards the project total.
# hr.expense state selection: draft, reported, submitted, approved, done, refused
EXCLUDED_EXPENSE_STATES = ("refused",)


class ProjectProject(models.Model):
    _inherit = "project.project"

    expense_count = fields.Integer(
        compute="_compute_expense_data",
        string="# Expenses",
    )
    expense_total = fields.Monetary(
        compute="_compute_expense_data",
        string="Expenses Total",
        currency_field="expense_currency_id",
    )
    # hr.expense.total_amount is expressed in the expense's company currency,
    # so we mirror that here to display the Monetary widget correctly.
    expense_currency_id = fields.Many2one(
        "res.currency",
        compute="_compute_expense_data",
        string="Expense Currency",
    )

    @api.depends("hr_expense_ids", "hr_expense_ids.total_amount", "hr_expense_ids.state")
    def _compute_expense_data(self):
        for project in self:
            expenses = project.hr_expense_ids.filtered(
                lambda e: e.state not in EXCLUDED_EXPENSE_STATES
            )
            project.expense_count = len(expenses)
            project.expense_total = sum(expenses.mapped("total_amount"))
            project.expense_currency_id = (
                expenses[:1].company_currency_id or project.company_id.currency_id
            )

    def action_open_project_expenses(self):
        self.ensure_one()
        expenses = self.hr_expense_ids.filtered(
            lambda e: e.state not in EXCLUDED_EXPENSE_STATES
        )
        action = {
            "name": self.env._("Expenses"),
            "type": "ir.actions.act_window",
            "res_model": "hr.expense",
            "view_mode": "list,form",
            "domain": [("id", "in", expenses.ids)],
            "context": {
                "default_project_id": self.id,
                "search_default_project_id": self.id,
            },
        }
        return action
