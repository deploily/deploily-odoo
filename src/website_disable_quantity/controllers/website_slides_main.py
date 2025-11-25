import logging

from odoo import http
from odoo.addons.website_slides.controllers.main import WebsiteSlides
from odoo.http import request, route
from odoo.exceptions import AccessError
from werkzeug.exceptions import NotFound
from odoo import fields, http, tools, _
from odoo.http import request, SessionExpiredException
from odoo.addons.website.controllers.main import QueryURL
_logger = logging.getLogger(__name__)

class WebsiteSlides(WebsiteSlides):
    @http.route('/slides', type='http', auth="public", website=True, sitemap=True, readonly=True)
    def slides_channel_home(self, category_id=None, **post):
        """ Home page with optional category filter """

        domain = request.website.website_domain()

        # Add category filter:
        if category_id:
            try:
                category_id = int(category_id)
                domain += [('category_id', '=', category_id)]
            except:
                pass

        channels_all = tools.lazy(lambda: request.env['slide.channel'].search(domain))

        if not request.env.user._is_public():
            channels_my = tools.lazy(lambda: channels_all.filtered(
                lambda ch: ch.is_member
            ).sorted(
                lambda ch: 0 if ch.completed else ch.completion,
                reverse=True
            )[:3])
        else:
            channels_my = request.env['slide.channel']

        channels_popular = tools.lazy(lambda: channels_all.sorted('total_votes', reverse=True)[:3])
        channels_newest = tools.lazy(lambda: channels_all.sorted('create_date', reverse=True)[:3])

        achievements = tools.lazy(lambda: request.env['gamification.badge.user'].sudo().search([
            ('badge_id.is_published', '=', True)
        ], limit=5))

        if request.env.user._is_public():
            challenges = None
            challenges_done = None
        else:
            challenges = tools.lazy(lambda: request.env['gamification.challenge'].sudo().search([
                ('challenge_category', '=', 'slides'),
                ('reward_id.is_published', '=', True)
            ], order='id asc', limit=5))

            challenges_done = tools.lazy(lambda: request.env['gamification.badge.user'].sudo().search([
                ('challenge_id', 'in', challenges.ids),
                ('user_id', '=', request.env.user.id),
                ('badge_id.is_published', '=', True)
            ]).mapped('challenge_id'))

        users = tools.lazy(lambda: request.env['res.users'].sudo().search([
            ('karma', '>', 0),
            ('website_published', '=', True)
        ], limit=5, order='karma desc'))

        render_values = self._slide_render_context_base()
        render_values.update(self._prepare_user_values(**post))
        render_values.update({
            'channels_my': channels_my,
            'channels_popular': channels_popular,
            'channels_newest': channels_newest,
            'achievements': achievements,
            'users': users,
            'top3_users': tools.lazy(self._get_top3_users),
            'challenges': challenges,
            'challenges_done': challenges_done,
            'search_tags': request.env['slide.channel.tag'],
            'slide_query_url': QueryURL('/slides/all', ['tag']),
            'slugify_tags': self._slugify_tags,

            'selected_category_id': category_id,
        })

        return request.render('website_slides.courses_home', render_values)