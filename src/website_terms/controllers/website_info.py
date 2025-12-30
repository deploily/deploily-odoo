 
import werkzeug.urls
import werkzeug.utils
import werkzeug.wrappers
import zipfile

from hashlib import md5
from io import BytesIO
from itertools import islice
from lxml import etree, html
from textwrap import shorten
from werkzeug.exceptions import NotFound
from xml.etree import ElementTree as ET

import odoo

from odoo import http, models, fields, _
from odoo.exceptions import AccessError, UserError
from odoo.http import request, SessionExpiredException
from odoo.osv import expression
from odoo.tools import OrderedSet, escape_psql, html_escape as escape, py_to_js_locale
from odoo.addons.base.models.ir_http import EXTENSION_TO_WEB_MIMETYPES
from odoo.addons.base.models.ir_qweb import QWebException
from odoo.addons.portal.controllers.portal import pager as portal_pager
from odoo.addons.portal.controllers.web import Home
from odoo.addons.web.controllers.binary import Binary
from odoo.addons.web.controllers.session import Session
from odoo.addons.website.tools import get_base_domain
from odoo.tools.json import scriptsafe as json
from odoo.addons.website.controllers.main import Website



class DeploilyWebsite(Website):

    def sitemap_website_info(env, rule, qs):
        website = env['website'].get_current_website()
        if not (
            website.viewref('website.website_info', False).active
            and website.viewref('website.show_website_info', False).active
        ):
            # avoid 404 or blank page in sitemap
            return False

        if not qs or qs.lower() in '/website/info':
            yield {'loc': '/website/info'}
    @http.route('/website/info', type='http', auth="public", website=True, sitemap=sitemap_website_info, readonly=True)
    def website_info(self, **kwargs):
                return request.not_found()

