# Copyright 2014-2023 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    subscription_ids = fields.One2many(
        comodel_name="contract.line",
        inverse_name="partner_id",
        domain=[("publication", "=", True)],
        string="Subscription contract lines",
    )
    distribution_list_ids = fields.One2many(
        comodel_name="publication.distribution.list",
        inverse_name="partner_id",
        string="Publications received",
    )