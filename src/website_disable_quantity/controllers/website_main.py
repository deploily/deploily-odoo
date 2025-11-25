import logging

from odoo import http
from odoo.addons.website.controllers.main import Website
from odoo.http import request, route
from odoo.exceptions import AccessError
from werkzeug.exceptions import NotFound
from odoo import fields, http, tools, _
from odoo.http import request, SessionExpiredException
from odoo.addons.website.controllers.main import QueryURL
_logger = logging.getLogger(__name__)




class Website(Website):

    @http.route(["/"], auth="public")
    def index(self, data={}, **kw):
        super(Website, self).index(**kw)
        channel_categories = request.env['channel.category'].search([])
        return http.request.render("website.homepage", {"channel_categories":channel_categories})
    
    