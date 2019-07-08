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
            self.barcode = None
            raise Warning('No product is available for this barcode')
        if self.barcode and self.move_ids_without_package:
            for line in self.move_ids_without_package:
                if line.product_id.barcode == self.barcode:
                    line.quantity_done += 1
                    self.barcode = None
                    match = True
        if self.barcode and not match:
            self.barcode = None
            if product_id:
                raise Warning('This product is not available in the order.'
                              'You can add this product by clicking the "Add an item" and scan')


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
    old_ref = fields.Char('Referencia Anterior', related='product_id.old_code')

