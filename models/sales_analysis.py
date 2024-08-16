from odoo import models, fields, api
from datetime import datetime, timedelta
import json

class SalesAnalysisReport(models.Model):
    _name = 'sales.analysis.report'
    _description = 'Sales Analysis Report'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    date = fields.Date(string='Report Date', default=fields.Date.today)
    sales_prediction = fields.Float(string='Sales Prediction')
    top_products_ids = fields.One2many('sales.analysis.top.product', 'report_id', string='Top Products')
    top_customers_ids = fields.One2many('sales.analysis.top.customer', 'report_id', string='Top Customers')

    @api.depends('date')
    def _compute_name(self):
        for record in self:
            record.name = f"Sales Analysis Report - {record.date}"
    @api.model
    def generate_daily_report(self):
        today = fields.Date.today()
        last_month = today - timedelta(days=30)

        # Top products
        top_products = self.env['sale.order.line'].read_group(
            [('order_id.date_order', '>=', last_month)],
            ['product_id', 'product_uom_qty'],
            ['product_id'],
            orderby='product_uom_qty desc',
            limit=5
        )

        # Top customers
        top_customers = self.env['sale.order'].read_group(
            [('date_order', '>=', last_month)],
            ['partner_id', 'amount_total'],
            ['partner_id'],
            orderby='amount_total desc',
            limit=5
        )

        # Sales prediction (simple average of last 30 days)
        sales_last_month = self.env['sale.order'].search([('date_order', '>=', last_month)])
        total_sales = sum(sales_last_month.mapped('amount_total'))
        sales_prediction = total_sales / 30  # Average daily sales

        # Create the report
        report = self.create({
            'date': today,
            'sales_prediction': sales_prediction,
        })

        # Create related records for top products and customers
        for product in top_products:
            self.env['sales.analysis.top.product'].create({
                'report_id': report.id,
                'product_id': product['product_id'][0],
                'quantity': product['product_uom_qty'],
            })

        for customer in top_customers:
            self.env['sales.analysis.top.customer'].create({
                'report_id': report.id,
                'partner_id': customer['partner_id'][0],
                'total_amount': customer['amount_total'],
            })

        return report

    @api.model
    def create(self, vals):
        record = super(SalesAnalysisReport, self).create(vals)
        if not record.top_products_ids or not record.top_customers_ids:
            record.generate_report_data()
        return record
    

    def generate_report_data(self):
        for record in self:
            if not record.top_products_ids and not record.top_customers_ids:
                last_month = record.date - timedelta(days=30)
                
                # Generate top products
                top_products = self.env['sale.order.line'].read_group(
                    [('order_id.date_order', '>=', last_month)],
                    ['product_id', 'product_uom_qty'],
                    ['product_id'],
                    orderby='product_uom_qty desc',
                    limit=5
                )
                for product in top_products:
                    self.env['sales.analysis.top.product'].create({
                        'report_id': record.id,
                        'product_id': product['product_id'][0],
                        'quantity': product['product_uom_qty'],
                    })
                
                # Generate top customers
                top_customers = self.env['sale.order'].read_group(
                    [('date_order', '>=', last_month)],
                    ['partner_id', 'amount_total'],
                    ['partner_id'],
                    orderby='amount_total desc',
                    limit=5
                )
                for customer in top_customers:
                    self.env['sales.analysis.top.customer'].create({
                        'report_id': record.id,
                        'partner_id': customer['partner_id'][0],
                        'total_amount': customer['amount_total'],
                    })
        return True
    
    def get_report_data(self):
        return {
            'top_products': self.top_products_ids,
            'top_customers': self.top_customers_ids,
            'sales_prediction': self.sales_prediction,
            'date': self.date,
        }
    def action_view_top_products_graph(self):
        return {
            'name': 'Top Products',
            'res_model': 'sales.analysis.top.product',
            'view_mode': 'graph,tree',
            'type': 'ir.actions.act_window',
            'domain': [('report_id', '=', self.id)],
            'context': {
                'graph_measure': 'quantity',
                'graph_mode': 'bar',
                'graph_groupbys': ['product_id'],
            },
        }

    def action_view_top_customers_graph(self):
        return {
            'name': 'Top Customers',
            'res_model': 'sales.analysis.top.customer',
            'view_mode': 'graph,tree',
            'type': 'ir.actions.act_window',
            'domain': [('report_id', '=', self.id)],
            'context': {
                'graph_measure': 'total_amount',
                'graph_mode': 'bar',
                'graph_groupbys': ['partner_id'],
            },
        }

class SalesAnalysisTopProduct(models.Model):
    _name = 'sales.analysis.top.product'
    _description = 'Top Product in Sales Analysis'
    _order = 'quantity desc'

    report_id = fields.Many2one('sales.analysis.report', string='Report')
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Quantity Sold')

class SalesAnalysisTopCustomer(models.Model):
    _name = 'sales.analysis.top.customer'
    _description = 'Top Customer in Sales Analysis'
    _order = 'total_amount desc'

    report_id = fields.Many2one('sales.analysis.report', string='Report')
    partner_id = fields.Many2one('res.partner', string='Customer')
    total_amount = fields.Float(string='Total Amount')
