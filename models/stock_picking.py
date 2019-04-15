# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import Warning
import time


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    barcode = fields.Char(string='Barcode')

    @api.onchange('barcode')
    def barcode_scanning(self):
        match = False
        product_obj = self.env['product.product']
        product_id = product_obj.search([('barcode', '=', self.barcode)])
        if self.barcode and not product_id:
        #    self.barcode = None
            raise Warning('Ningun producto coincide con el codigo escaneado')
        if self.barcode and self.move_lines:
            for line in self.move_lines:
                if line.product_id.barcode == self.barcode:
                    line.quantity_done += 1
        #            self.barcode = None
                    match = True
        if self.barcode and not match:
        #    self.barcode = None
            if product_id:
                raise Warning('este producto no esta disponible en la orden'
                              'Puedes agregar este producto en "add product" y escaneas nuevamente')


class StockPickingOperation(models.Model):
    _inherit = 'stock.move'

    barcode = fields.Char(string='Barcode')
    talla = fields.Char('Talla', related='product_id.default_talla')
    color = fields.Char('Color', related='product_id.default_color')

    @api.onchange('barcode')
    def _onchange_barcode_scan(self):
        product_rec = self.env['product.product']
        if self.barcode:
            product = product_rec.search([('barcode', '=', self.barcode)])
            self.product_id = product.id
            self.talla = product.default_talla
            self.color = product.default_color
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

#class StockPickingOperation(models.Model):
#    _inherit = 'stock.move'
#
#
#    @api.onchange('x_barcode')
#    def _onchange_barcode_scan(self):
#        barcode = self.x_barcode
#        product_rec = self.env['product.product']
#        #if barcode:
#        #    product_id = product_rec.search([('barcode', '=', barcode)])
#        #    self.product_id = product_id.id
#        self.log_scanner = ""
#        flag = False
#        product_id = product_rec.search([('barcode', '=', barcode)])
#        if barcode and not product_id:
#            self.log_scanner = "Elemento desconocido!!!!!!!!"
#            self.x_barcode = ""
#        if barcode and product_id:
#            new_lines = self.env['list.productcode']
#            real_lines = self.env['stock.move']
#            size = len(self.productcodes_ids)
#            if barcode and size > 0:
#                for line in self.productcodes_ids:
#                    if line.product_id.barcode == barcode:
#                        line.qty += 1
#                        self.x_barcode = ""
#                if self.temp_barcode == "":
#                        self.log_scanner = "Se agregó cantidad"
#                else:
#                    new_line = new_lines.new({
#                        'product_id': product_id.id,
#                        'qty': 1,
#                    })
#                #    move = self.env['stock.move'].({
#                #        'product_id': product_id.id,
#                #        'product_uom': product_id.uom_id.id,
#                #        'product_uom_qty': 1,
#                #    })
#                #    new_lines += new_line
#            else:
#                self.log_scanner = "Se guardó el primer elemento"
#                new_line = new_lines.new({
#                    'product_id': product_id.id,
#                    'qty': 1,
#                })
#                new_lines += new_line
#                #real_line = real_lines.({
#                #    'product_id': product_id.id,
#                #    'product_uom_qty': 1,
#                #    'quantity_done': 1,
#                #})
#                #real_line._action_confirm()
#                #real_line._action_assign()
#
#                #real_line._action_done()
#            self.productcodes_ids += new_lines
#            #move_lines += real_line
#            self.x_barcode = ""


class StockPickingBarCode(models.Model):
    _inherit = 'stock.picking'

    temp_barcode = fields.Char("Barcode Tempo", required=False)
    productcodes_ids = fields.One2many('list.productcode', 'picking_id', string='Productos')
    picking_checked = fields.Boolean("Ready Picking", default=True)
    log_scanner = fields.Char("log escaner", readonly=True)

#    @api.multi
#    @api.depends('productcodes_ids.bool_barcode','productcodes_ids.qty')
#    def _get_picking_checked(self):
#        for picking in self:
#            if len(picking.productcodes_ids) >= 1 and all(p.bool_barcode for p in picking.productcodes_ids):
#                move_products = picking.move_lines.mapped('product_id')
#                products = picking.productcodes_ids.mapped('product_id')
#                if move_products == products:
#                    picking.picking_checked = True
#
#        if self.barcode and self.move_lines:
#            for line in self.move_lines:
#                if line.product_id.barcode == self.barcode:
#                    line.quantity_done += 1
#                    self.barcode = None
#                    match = True


    @api.onchange('temp_barcode')
    def onchange_temp_barcode(self):
        self.log_scanner = ""
        flag = False
        barcode = self.temp_barcode
        location = self.location_id
        location_dest = self.location_dest_id
        product_rec = self.env['product.product']
        product_id = product_rec.search([('barcode', '=', barcode)])
        if barcode and not product_id:
            self.log_scanner = "Elemento desconocido!!!!!!!!"
            self.temp_barcode = ""
        if barcode and product_id:
            new_lines = self.env['list.productcode']
            picking_lines = {}
            real_lines = self.env['stock.move']
            size = len(self.productcodes_ids)
            if barcode and size > 0:
                for line in self.productcodes_ids:
                    if line.product_id.barcode == barcode:
                        line.qty += 1
                        self.temp_barcode = ""
                for line in self.move_lines:
                    if line.product_id.barcode == barcode:
                        line.quantity_done += 1
                if self.temp_barcode == "":
                        self.log_scanner = "se agrego cantidad"
                else:
                    self.log_scanner = "Como no coincide con ningun elemento de la lista, agregamos nuevo "
                    new_line = new_lines.new({
                        'product_id': product_id.id,
                        'qty': 1,
                    })
                    new_lines += new_line
            else:
                #elemento nuevo en la lista
                self.log_scanner = "se creó primer elemento"
                new_line = new_lines.new({
                    'product_id': product_id.id,
                    'qty': 1,
                })
                new_lines += new_line
#no borrar , para efectos del test necesito comentar este pedazo.
            #    real_line = real_lines.new({
            #        'name': self.name,
            #        'product_id': product_id.id,
            #        'quantity_done': 1,
            #        'product_uom': 1,
            #        'date_expected': self.scheduled_date,
            #    })
            #    real_lines += real_line

            self.productcodes_ids += new_lines
            #self.move_lines += real_lines
            self.temp_barcode = ""

    @api.multi
    def generate_moves(self):
        picking_obj = self.env['stock.move']
        product_rec = self.env['product.product']
        stock_q = self.env['stock.quant']
        location = self.location_id
        location_dest = self.location_dest_id
        for line in self.productcodes_ids:
            new_line = picking_obj.create({
                'name': 'Nuevo Moove : ' + line.product_id.display_name,
                'barcode': line.barcode,
                'quantity_done': line.qty,
                'product_id': line.product_id.id,
                'product_uom': 1,
                'location_id': location.id,
                'location_dest_id': location_dest.id,
                'is_locked': True,

                })
            new_line._action_confirm()
            new_line._action_assign()
            new_line.move_line_ids.write({'qty_done': line.qty})
            new_line._action_done()
            picking_obj |= new_line
            #picking_obj.move_line_ids.write({'qty_done': line.qty})
            self.move_lines |= picking_obj
        self.log_scanner = "se guardaron los movimientos ok"
        return self.move_lines


#move.move_line_ids.write({'qty_done': qty}) # This s a stock.move.line record. You could also do it manually
#move._action_done()


class ListProductcode(models.Model):
    _name = 'list.productcode'

    barcode = fields.Char('Codigo de Barras', related='product_id.barcode')
    default_code = fields.Char('Referencia', related='product_id.default_code')
    product_id = fields.Many2one('product.product', string='Producto')
    talla = fields.Char('Talla', related='product_id.default_talla')
    color = fields.Char('Color', related='product_id.default_color')
    qty = fields.Float("Cantidad", default=1)
    picking_id = fields.Many2one('stock.picking', "Picking", ondelete='cascade')
    bool_barcode = fields.Boolean("Barcode Checked", default=True)

    #@api.multi
    #@api.depends('qty')
    #def _get_bool_barcode(self):
    #    for record in self:
    #        move = record.picking_id.move_lines.filtered(lambda r: r.product_id.id == record.product_id.id)
    #        record.bool_barcode = record.qty == move.product_uom_qty and True or False

class productProduct(models.Model):
    _inherit = 'product.template'

    default_talla = fields.Char('Talla')
    default_color = fields.Char('Color')

class automatedInventory(models.Model):
    _inherit = 'stock.inventory'

    inventory_barcode = fields.Char("Barcode Inventario", required=False)
    talla = fields.Char('Talla', related='product_id.default_talla')
    color = fields.Char('Color', related='product_id.default_color')
    log_scanner = fields.Char("log escaner", readonly=True)

    @api.onchange('inventory_barcode')
    def onchange_inventory_barcode(self):
        self.log_scanner = ""
        flag = False
        barcode = self.inventory_barcode
        location = self.location_id
        filtro = self.filter
        product_rec = self.env['product.product']
        product_id = product_rec.search([('barcode', '=', barcode)])
        if barcode and not product_id:
            self.log_scanner = "Elemento desconocido!!!!!!!!"
            self.inventory_barcode = ""
        if barcode and product_id:
            new_lines = self.env['stock.inventory.line']
            picking_lines = {}
            real_lines = self.env['stock.move']
            size = len(self.line_ids)
            if barcode and size > 0:
                for line in self.line_ids:
                    if line.product_id.barcode == barcode:
                        line.product_qty += 1
                        self.inventory_barcode = ""
                if self.inventory_barcode == "":
                        self.log_scanner = "se agrego cantidad"
                else:
                    self.log_scanner = "Como no coincide con ningun elemento de la lista, agregamos nuevo "
                    new_line = new_lines.new({
                        'product_id': product_id.id,
                        'product_uom_id': 1,
                        'location_id': location.id,
                        'product_qty': 1,
                    })
                    new_lines |= new_line
            else:
                #elemento nuevo en la lista
                self.log_scanner = "se creó primer elemento"
                new_line = new_lines.create({
                    'product_id': product_id.id,
                    'product_uom_id': 1,
                    'location_id': location.id,
                    'product_qty': 1,
                })
                new_lines |= new_line
#no borrar , para efectos del test necesito comentar este pedazo.
            #    real_line = real_lines.new({
            #        'name': self.name,
            #        'product_id': product_id.id,
            #        'quantity_done': 1,
            #        'product_uom': 1,
            #        'date_expected': self.scheduled_date,
            #    })
            #    real_lines += real_line

            self.line_ids |= new_lines
            #self.move_lines += real_lines
            self.inventory_barcode = ""

class StockPickingOperation(models.Model):
    _inherit = 'stock.quant'

    talla = fields.Char('Talla', related='product_id.default_talla')
    color = fields.Char('Color', related='product_id.default_color')


class inventoryLineAPE(models.Model):
    _inherit = 'stock.inventory.line'

    talla = fields.Char('Talla', related='product_id.default_talla')
    color = fields.Char('Color', related='product_id.default_color')
