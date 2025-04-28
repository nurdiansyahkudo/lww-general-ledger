{
    'name': 'Custom General Ledger Extension',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Add Purchase Order column to General Ledger report',
    'depends': ['account_reports', 'account'],
    'data': [
        'data/general_ledger_extension.xml',
    ],
    'installable': True,
    'auto_install': False,
}
