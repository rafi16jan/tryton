# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import PoolMeta, Pool
from trytond.model import ModelSQL, fields
from trytond.pyson import Eval

from trytond.modules.product import price_digits, round_price
from trytond.modules.company.model import CompanyValueMixin


class Template(metaclass=PoolMeta):
    __name__ = 'product.template'

    gross_price = fields.MultiValue(fields.Numeric(
            "Gross Price", digits=price_digits,
            states={
                'invisible': ~Eval('salable', False),
                },
            depends=['salable'],
            help="The price with default tax included."))
    gross_prices = fields.One2Many(
        'product.gross_price', 'template', "Gross Prices")

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field == 'gross_price':
            return pool.get('product.gross_price')
        return super(Template, cls).multivalue_model(field)

    @fields.depends('gross_price', 'account_category')
    def on_change_gross_price(self):
        pool = Pool()
        Tax = pool.get('account.tax')
        if self.gross_price is None or not self.account_category:
            return
        self.list_price = round_price(Tax.reverse_compute(
                self.gross_price,
                self.customer_taxes_used))


class Product(metaclass=PoolMeta):
    __name__ = 'product.product'


class GrossPrice(ModelSQL, CompanyValueMixin):
    "Product Gross Price"
    __name__ = 'product.gross_price'
    template = fields.Many2One(
        'product.template', "Template", ondelete='CASCADE', select=True)
    gross_price = fields.Numeric("Gross Price", digits=price_digits)
