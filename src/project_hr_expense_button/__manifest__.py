{
    "name": "Project HR Expense Button",
    "version": "18.0.1.0.0",
    "author": "SARL Transformatek",
    "license": "AGPL-3",
    "category": "Project",
    "summary": "Adds a stat button on the project form showing total linked expenses",
    "depends": [
        "project_hr_expense_analytic",  # OCA module: gives us hr_expense_ids / project_id link
    ],
    "data": [
        "views/project_project_views.xml",
    ],
    "installable": True,
}
