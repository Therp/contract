# Copyright 2014-2023 Therp BV <https://therp.nl>.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# pylint: disable=no-member,too-few-public-methods,missing-docstring
# pylint: disable=protected-access
from odoo import api, fields, models


LINE_ANALYSIS_STATEMENT = """\
SELECT
    cl.id -- ,
    -- pt.id, pt.name, pt.default_code, pt.publication,
    -- cl.partner_id, cl.contract_id, cl.publication
 FROM contract_line cl
 JOIN product_product pp ON cl.product_id = pp.id
 JOIN product_template pt ON pp.product_tmpl_id = pt.id
 WHERE cl.publication <> pt.publication
"""


class ContractLine(models.Model):
    _inherit = "contract.line"

    partner_id = fields.Many2one(
        related="contract_id.partner_id", store=True, readonly=True
    )
    publication = fields.Boolean(
        string="Subscription product line",
        related="product_id.product_tmpl_id.publication",
        store=True,
    )

    @api.multi
    def action_distribution_list(self):
        self.ensure_one()
        action = self.env.ref("publication.action_distribution_list").read()[0]
        action["context"] = {
            "default_product_id": self.product_id.id,
            "default_contract_partner_id": self.partner_id.id,
        }
        action["domain"] = [
            ("contract_partner_id", "=", self.partner_id.id),
            ("product_id", "=", self.product_id.id),
        ]
        action["view_mode"] = "form"
        action["target"] = "current"
        return action

    @api.model
    def create(self, vals):
        this = super().create(vals)
        self.env["publication.distribution.list"]._update_contract_partner_copies(
            this.product_id,
            this.contract_id.partner_id,
        )
        return this

    @api.multi
    def write(self, vals):
        old_values = (
            set(self.mapped(lambda x: (x.product_id, x.contract_id.partner_id)))
            if "product_id" in vals
            else []
        )
        result = super().write(vals)
        needs_update = set(["product_id", "quantity"]) & set(vals.keys())
        if needs_update:
            for this in self:
                self.env[
                    "publication.distribution.list"
                ]._update_contract_partner_copies(
                    this.product_id,
                    this.contract_id.partner_id,
                )
            for product, partner in old_values:
                self.env[
                    "publication.distribution.list"
                ]._update_contract_partner_copies(
                    product,
                    partner,
                )
        return result

    @api.multi
    def unlink(self):
        updates = set(
            self.mapped(lambda x: (x.product_id, x.contract_id.partner_id))
        )
        result = super().unlink()
        for product, partner in updates:
            self.env["publication.distribution.list"]._update_contract_partner_copies(
                product,
                partner,
            )
        return result

    @api.model
    def cron_compute_publication(self):
        """Recompute publication for all lines where needed.

        We use an SQL query to select the records that should be updated.
        """
        self.env.cr.execute(LINE_ANALYSIS_STATEMENT)
        data = self.env.cr.fetchall()
        line_ids = [rec[0] for rec in data]
        lines = self.browse(line_ids)
        for line in lines:
            line.write({"publication": line.product_id.publication})
