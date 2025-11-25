import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ChannelCategory(models.Model):
    _name = "channel.category"
    _order = "sequence asc, id desc"
    _description = "Channel Category"
    _rec_name = "name"

    name = fields.Char("Nom", required=True)
    channels = fields.One2many(
        "slide.channel",
        "category_id",
        string="Courses",
    )
    image=fields.Image("Image")
    description = fields.Html("Description")
    sequence = fields.Integer("Sequence", default=10)


class SlideChannel(models.Model):
    _inherit = "slide.channel"

    category_id = fields.Many2one("channel.category", string="Category")

