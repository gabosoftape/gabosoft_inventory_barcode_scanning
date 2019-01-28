# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import Warning


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    barcode = fields.Char(string='Barcode')
    aux_barcode = fields.Char(string='Barcode Automated box value.')

    @api.onchange('barcode')
    def barcode_scanning(self):
        match = False
        product_obj = self.env['product.product']
        product_id = product_obj.search([('barcode', '=', self.barcode)])
        if self.barcode and not product_id:
            self.barcode = None
            raise Warning('Ningun producto coincide con el codigo escaneado')
        if self.barcode and self.move_lines:
            for line in self.move_lines:
                if line.product_id.barcode == self.barcode:
                    line.quantity_done += 1
                    self.barcode = None
                    match = True
        if self.barcode and not match:
            self.barcode = None
            if product_id:
                raise Warning('este producto no esta disponible en la orden'
                              'Puedes agregar este producto en "add product" y escaneas nuevamente')


class StockPickingOperation(models.Model):
    _inherit = 'stock.move'

    barcode = fields.Char(string='Barcode')
    aux_barcode = fields.Char(string='Campo auxiliar barcode box')

    @api.onchange('barcode')
    def _onchange_barcode_scan(self):
        product_rec = self.env['product.product']
        if self.barcode:
            product = product_rec.search([('barcode', '=', self.barcode)])
            self.product_id = product.id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
