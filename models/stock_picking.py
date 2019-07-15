# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.exceptions import Warning
import time


class StockPickingBarCode(models.Model):
    _inherit = 'stock.picking'

    temp_barcode = fields.Char("Barcode Tempo", required=False)
    picking_checked = fields.Boolean("Ready Picking", default=True)
    log_scanner = fields.Char("log escaner", readonly=True)
    talla = fields.Char('Talla', related='product_id.default_talla')
    color = fields.Char('Color', related='product_id.default_color')
    default_code = fields.Char('Cod Ref', related='product_id.default_code')

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
            real_lines = self.env['stock.move']
            size = len(self.move_lines)
            if barcode and size > 0:
                for line in self.move_lines:
                    if line.product_id.barcode == barcode:
                        line.quantity_done += 1
                        line.product_qty += 1
                        self.temp_barcode = ""
                if self.temp_barcode == "":
                        self.log_scanner = "se agrego cantidad"
                else:
                    self.log_scanner = "Como no coincide con ningun elemento de la lista, agregamos nuevo "
                    real_line = real_lines.new({
                        'name': self.name,
                        'product_id': product_id.id,
                        'quantity_done': 1,
                        'product_uom': 1,
                        'date_expected': self.scheduled_date,
                        'state': 'draft',
                    })
                    real_lines += real_line
            else:
# elemento nuevo en la lista
                self.log_scanner = "se creó primer elemento"
#               new_line = new_lines.new({
#                 'product_id': product_id.id,
#                 'qty': 1,
#           })
#           new_lines += new_line
# no borrar , para efectos del test necesito comentar este pedazo.
                real_line = real_lines.new({
                    'name': self.name,
                    'product_id': product_id.id,
                    'quantity_done': 1,
                    'product_uom': 1,
                    'date_expected': self.scheduled_date,
                    'state': 'draft',
                })
                real_lines += real_line
            #self.productcodes_ids += new_lines
            self.move_lines |= real_lines
            self.temp_barcode = ""

    @api.multi
    def generate_moves(self):
        picking_obj = self.env['stock.move']
        product_rec = self.env['product.product']
        stock_q = self.env['stock.quant']
        location = self.location_id
        location_dest = self.location_dest_id
        for line in self.move_lines:
            new_line = picking_obj.create({
                'name': 'Nuevo Moove : ' + line.product_id.display_name,
                'barcode': line.barcode,
                'quantity_done': line.qty,
                'product_id': line.product_id,
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

class StockPickingOperation(models.Model):
    _inherit = 'stock.move'

    barcode = fields.Char(string='Barcode')
    talla = fields.Char('Talla', related='product_id.default_talla')
    color = fields.Char('Color', related='product_id.default_color')
    default_code = fields.Char('Cod Ref', related='product_id.default_code')
    

    @api.onchange('barcode')
    def _onchange_barcode_scan(self):
        product_rec = self.env['product.product']
        if self.barcode:
            product = product_rec.search([('barcode', '=', self.barcode)])
            self.product_id = product.id
            self.talla = product.default_talla
            self.color = product.default_color


class StockPicking(models.Model):
    _inherit = 'stock.move.line'

    barcode = fields.Char(string='Codigo de barras')
    talla = fields.Char('Talla', related='product_id.default_talla')
    color = fields.Char('Color', related='product_id.default_color')
    default_code = fields.Char('Cod Ref', related='product_id.default_code')

    @api.onchange('barcode')
    def barcode_scanning(self):
        match = False
        product_obj = self.env['product.product']
        product_id = product_obj.search([('barcode', '=', self.barcode)])
        if self.barcode:
            self.lots_visible = self.product_id.tracking != 'none'
            if not self.product_uom_id or self.product_uom_id.category_id != self.product_id.uom_id.category_id:
                if self.move_id.product_uom:
                    self.product_uom_id = self.move_id.product_uom.id
                else:
                    self.product_uom_id = self.product_id.uom_id.id
            res = {'domain': {'product_uom_id': [('category_id', '=', self.product_uom_id.category_id.id)]}}
        else:
            res = {'domain': {'product_uom_id': []}}
        return res

class productTemplate(models.Model):
    _inherit = 'product.template'

    default_talla = fields.Char('Talla')
    default_color = fields.Char('Color')
    old_code = fields.Char('Referencia Anterior')

class productProduct(models.Model):
    _inherit = 'product.product'

    old_code = fields.Char('Referencia Anterior')


class automatedInventory(models.Model):
    _inherit = 'stock.inventory'

    inventory_barcode = fields.Char("Barcode Inventario", required=False)
    log_scanner = fields.Char("log escaner", readonly=True)
    default_code = fields.Char('Cod Ref', related='product_id.default_code')

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
    default_code = fields.Char('Cod Ref', related='product_id.default_code')
    old_ref = fields.Char('Referencia Anterior', related='product_id.old_code')

