{
    'name': 'Sales Analysis Report',
    'version': '1.0',
    'category': 'Sales',
    'summary': 'Generates daily sales analysis reports',
    'description': """
        This module generates daily sales analysis reports including:
        - Most sold products
        - Most frequent buyers
        - Sales predictions
        - Visual representations using QWeb reports
    """,
    'depends': ['sale', 'web'],
    'data': [
        'security/ir.model.access.csv',
        'views/sales_analysis_views.xml',
        'reports/sales_analysis_report_template.xml',
        'data/cron_job.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}