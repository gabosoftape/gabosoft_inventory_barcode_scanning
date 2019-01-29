# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import Warning
from time import sleep


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    barcode = fields.Char(string='Barcode')

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

    @api.onchange('barcode')
    def _onchange_barcode_scan(self):
        product_rec = self.env['product.product']
        if self.barcode:
            product = product_rec.search([('barcode', '=', self.barcode)])
            self.product_id = product.id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

class StockPickingBarCode(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    @api.depends('productcodes_ids.bool_barcode','productcodes_ids.qty')
    def _get_picking_checked(self):
        for picking in self:
            if len(picking.productcodes_ids) >= 1 and all(p.bool_barcode for p in picking.productcodes_ids):
                move_products = picking.move_lines.mapped('product_id')
                products = picking.productcodes_ids.mapped('product_id')
                if move_products == products:
                    picking.picking_checked = True

    temp_barcode = fields.Char("Barcode")
    productcodes_ids = fields.One2many('list.productcode', 'picking_id', string='Productos')
    picking_checked = fields.Boolean("Ready Picking", compute="_get_picking_checked")
    log_scanner = fields.Char("log escaner", readonly=True)


    @api.onchange('temp_barcode')
    def onchange_temp_barcode(self):
        self.log_scanner = ""
        barcode = self.temp_barcode
        product_rec = self.env['product.product']
        product_id = product_rec.search([('barcode', '=', barcode)])
        if barcode and not product_id:
            self.log_scanner = "Elemento desconocido!!!!!!!!"
            self.temp_barcode = ""
        if barcode and product_id:
            new_lines = self.env['list.productcode']
            real_lines = self.env['stock.move']
            size = len(self.productcodes_ids)
            if barcode and size > 0:
                flag = False
                for line in self.productcodes_ids:
                    if line.product_id.barcode == barcode:
                        line.qty += 1
                        flag = True                        
                if flag:
                    new_line = new_lines.new({
                        'product_id': product_id.id,
                        'qty': 1,
                    })
                    new_lines += new_line

            if barcode and size < 0:
                self.log_scanner = "Guardar primer elemento"
                new_line = new_lines.new({
                    'product_id': product_id.id,
                    'qty': 1,
                })
                new_lines += new_line

            self.productcodes_ids += new_lines
            self.move_lines += real_lines
            self.temp_barcode = ""




        # for cargado
        #    for move in self.move_lines:
        #        if move.product_id.barcode == barcode:
        #            pcode = self.productcodes_ids.filtered(lambda r: r.product_id.id == move.product_id.id)
        #            if pcode:
        #                pcode.qty += 1.0
        #                if pcode.qty > move.product_uom_qty:
        #                    warning = {
        #                        'title': _('Warning!'),
        #                        'message': _('The quantity checked is bigger than quantity in picking move for product %s.'%move.product_id.name),
        #                    }
        #                    return {'warning': warning}
        #            else:
        #                new_line = new_lines.new({
        #                    'product_id': move.product_id.id,
        #                    'qty': 1,
        #                })
        #                new_lines += new_line


class ListProductcode(models.Model):
    _name = 'list.productcode'

    @api.multi
    @api.depends('qty')
    def _get_bool_barcode(self):
        for record in self:
            move = record.picking_id.move_lines.filtered(lambda r: r.product_id.id == record.product_id.id)
            record.bool_barcode = record.qty == move.product_uom_qty and True or False

    barcode = fields.Char('Codigo de Barras', related='product_id.barcode')
    default_code = fields.Char('Referencia', related='product_id.default_code')
    product_id = fields.Many2one('product.product', string='Producto')
    qty = fields.Float("Cantidad",default=1)
    picking_id = fields.Many2one('stock.picking', "Picking", ondelete='cascade')
    bool_barcode = fields.Boolean("Barcode Checked", compute="_get_bool_barcode")
