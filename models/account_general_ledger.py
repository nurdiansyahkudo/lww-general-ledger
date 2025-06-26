from odoo import models, fields, api
from odoo.tools import get_lang, SQL

class GeneralLedgerCustomHandler(models.AbstractModel):
    _inherit = 'account.general.ledger.report.handler'

    def _get_aml_values(self, report, options, expanded_account_ids, offset=0, limit=None):
        aml_results_per_account_id, has_more = super()._get_aml_values(report, options, expanded_account_ids, offset=offset, limit=limit)

        for account_id, aml_results in aml_results_per_account_id.items():
            for aml_key, aml_values in aml_results.items():
                for column_group_key, column_values in aml_values.items():
                    if isinstance(column_values, dict):
                        move_id = column_values.get('move_id')
                        purchase_order = ''

                        if move_id:
                            move = self.env['account.move'].browse(move_id)
                            if move.ref:
                                # Ambil teks sebelum tanda "-"
                                stock_picking_name = move.ref.split('-')[0].strip()

                                # Cari stock.picking berdasarkan name
                                picking = self.env['stock.picking'].search([
                                    ('name', '=', stock_picking_name)
                                ], limit=1)

                                purchase_order = " "  # default value

                                if picking and picking.group_id:
                                    group_name = picking.group_id.name

                                    # Cek apakah group_name adalah nama dari purchase.order
                                    purchase = self.env['purchase.order'].search([('name', '=', group_name)], limit=1)
                                    if purchase:
                                        purchase_order = group_name
                                    else:
                                        # Kalau bukan purchase.order, asumsikan dia sale.order
                                        sale = self.env['sale.order'].search([('name', '=', group_name)], limit=1)
                                        if sale:
                                            purchase_order = picking.project_id.name

                        column_values['purchase_order'] = purchase_order

        return aml_results_per_account_id, has_more
    
    def _get_query_amls(self, report, options, expanded_account_ids, offset=0, limit=None) -> SQL:
      additional_domain = [('account_id', 'in', expanded_account_ids)] if expanded_account_ids is not None else None
      queries = []
      journal_name = self.env['account.journal']._field_to_sql('journal', 'name')
      for column_group_key, group_options in report._split_options_per_column_group(options).items():
          query = report._get_report_query(group_options, domain=additional_domain, date_scope='strict_range')
          account_alias = query.join(lhs_alias='account_move_line', lhs_column='account_id', rhs_table='account_account', rhs_column='id', link='account_id')
          account_code = self.env['account.account']._field_to_sql(account_alias, 'code', query)
          account_name = self.env['account.account']._field_to_sql(account_alias, 'name')
          account_type = self.env['account.account']._field_to_sql(account_alias, 'account_type')

          query = SQL(
              '''
              SELECT
                  account_move_line.id,
                  account_move_line.date,
                  account_move_line.date_maturity,
                  account_move_line.name,
                  account_move_line.ref,
                  account_move_line.company_id,
                  account_move_line.account_id,
                  account_move_line.payment_id,
                  account_move_line.partner_id,
                  account_move_line.currency_id,
                  account_move_line.amount_currency,
                  account_move_line.move_id,
                  COALESCE(account_move_line.invoice_date, account_move_line.date) AS invoice_date,
                  account_move_line.date                  AS date,
                  %(debit_select)s                        AS debit,
                  %(credit_select)s                       AS credit,
                  %(balance_select)s                      AS balance,
                  move.name                               AS move_name,
                  company.currency_id                     AS company_currency_id,
                  partner.name                            AS partner_name,
                  move.move_type                          AS move_type,
                  %(account_code)s                        AS account_code,
                  %(account_name)s                        AS account_name,
                  %(account_type)s                        AS account_type,
                  journal.code                            AS journal_code,
                  %(journal_name)s                        AS journal_name,
                  full_rec.id                             AS full_rec_name,
                  procurement_group.name                  AS purchase_order,
                  project_project.name                    AS project_name,
                  %(column_group_key)s                    AS column_group_key
              FROM %(table_references)s
              JOIN account_move move                      ON move.id = account_move_line.move_id
              LEFT JOIN stock_picking ON stock_picking.name = move.ref OR stock_picking.origin = move.name OR stock_picking.origin = move.ref
              LEFT JOIN procurement_group ON stock_picking.group_id = procurement_group.id
              LEFT JOIN project_project ON stock_picking.project_id = project_project.id
              %(currency_table_join)s
              LEFT JOIN res_company company               ON company.id = account_move_line.company_id
              LEFT JOIN res_partner partner               ON partner.id = account_move_line.partner_id
              LEFT JOIN account_journal journal           ON journal.id = account_move_line.journal_id
              LEFT JOIN account_full_reconcile full_rec   ON full_rec.id = account_move_line.full_reconcile_id
              WHERE %(search_condition)s
              ORDER BY account_move_line.date, account_move_line.move_name, account_move_line.id
              ''',
              account_code=account_code,
              account_name=account_name,
              account_type=account_type,
              journal_name=journal_name,
              column_group_key=column_group_key,
              table_references=query.from_clause,
              currency_table_join=report._currency_table_aml_join(group_options),
              debit_select=report._currency_table_apply_rate(SQL("account_move_line.debit")),
              credit_select=report._currency_table_apply_rate(SQL("account_move_line.credit")),
              balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance")),
              search_condition=query.where_clause,
          )
          queries.append(query)

      full_query = SQL(" UNION ALL ").join(SQL("(%s)", query) for query in queries)

      if offset:
          full_query = SQL('%s OFFSET %s ', full_query, offset)
      if limit:
          full_query = SQL('%s LIMIT %s ', full_query, limit)

      return full_query

    def _dynamic_lines_generator(self, report, options, all_column_groups_expression_totals, warnings=None):
        lines = super()._dynamic_lines_generator(report, options, all_column_groups_expression_totals, warnings)

        # Modifikasi lines untuk menambahkan kolom purchase_order pada baris detail
        # Biasanya kolom purchase_order sudah diisi di _get_aml_values dan akan otomatis muncul jika expression_label sesuai

        return lines
