# -*- coding: utf-8 -*-
# * Copyright (C) 2012-2015 Croissance Commune
# * Authors:
#       * Arezki Feth <f.a@majerti.fr>;
#       * Miotte Julien <j.m@majerti.fr>;
#       * TJEBBES Gaston <g.t@majerti.fr>
#
# This file is part of Autonomie : Progiciel de gestion de CAE.
#
#    Autonomie is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Autonomie is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Autonomie.  If not, see <http://www.gnu.org/licenses/>.
"""
Competence evaluation module

1- Choose a deadline (if manager choose also a contractor)
2- Fill the displayed grid
3- Display a printable version
"""
import logging
import colander
from pyramid.httpexceptions import HTTPFound

from autonomie.models.user import (
    get_users_options,
)
from autonomie.models.competence import (
    CompetenceDeadline,
    CompetenceScale,
    CompetenceOption,
    CompetenceGrid,
    CompetenceGridItem,
    CompetenceGridSubItem,
)
from autonomie.resources import competence_js
from autonomie.forms.competence import CompetenceGridQuerySchema
from autonomie.views import (
    BaseView,
)


logger = logging.getLogger(__name__)


def get_competence_grid(request, contractor_id, deadline_id):
    """
    Return a competence grid record for the given user and deadline
    """
    query = CompetenceGrid.query()
    query = query.filter_by(
        contractor_id=contractor_id,
        deadline_id=deadline_id,
    )

    grid = query.first()
    options = CompetenceOption.query()

    if grid is None:
        grid = CompetenceGrid(
            contractor_id=contractor_id,
            deadline_id=deadline_id,
        )

        request.dbsession.add(grid)

    for option in options:
        grid.ensure_item(option)

    return grid


def competence_index_view(request):
    """
    Index view to go to a competence grid
    """
    competence_js.need()
    user_options = get_users_options(roles=['contractor'])
    deadlines = CompetenceDeadline.query().all()
    if 'deadline' in request.POST or 'reference' in request.POST:
        logger.debug(request.POST)
        schema = CompetenceGridQuerySchema.bind(request=request)
        try:
            appstruct = schema.deserialize(request.POST)
        except colander.Invalid:
            logger.exception(u"Erreur dans le routage de la page de \
compétences : POSSIBLE BREAK IN ATTEMPT")
        else:
            # On récupère l'id du user pour l'évaluation
            contractor_id = appstruct['contractor_id']

            # On redirige vers la page appropriée
            if 'deadline' in appstruct:
                deadline_id = appstruct['deadline']
                grid = get_competence_grid(
                    request,
                    contractor_id,
                    deadline_id
                )
                url = request.route_path("competence_grid", id=grid.id)
                return HTTPFound(url)

            else:
                # TODO: Build the view for the radar
                pass

    return {
        'title': u'Évaluation des compétences',
        'user_options': user_options,
        'deadlines': deadlines,
    }


def competence_grid_view(context, request):
    """
    The competence grid base view
    """
    # loadurl : The url to load the options
    # context_url : The url to load datas about the context in json format
    competence_js.need()
    loadurl = request.route_path(
        'competence_grid',
        id=context.id,
        _query=dict(action='options'),
    )
    contexturl = request.current_route_path()

    title = u"Évaluation des compétences de {0} pour la période {1}".format(
        context.contractor.label, context.deadline.label
    )

    return {
        'title': title,
        "loadurl": loadurl,
        "contexturl": contexturl
    }


def competence_form_options(context, request):
    """
    Returns datas used to build the competence form page
    """
    return dict(
        grid=context,
        grid_edit_url=request.route_path(
            'competence_grid',
            id=context.id,
            _query=dict(action='edit')
        ),
        entry_root_url=request.route_path(
            'competence_grid_items',
            id=context.id,
        ),
        deadlines=CompetenceDeadline.query().all(),
        scales=CompetenceScale.query().all(),
    )


class RestCompetenceGrid(BaseView):
    """
    Json api for competence grid handling
    """

    def get(self):
        return {
            'grid': self.context,
            'competences': self.context.items,
        }


class RestCompetenceGridItem(BaseView):
    """
    """
    pass


def includeme(config):
    """
    Pyramid's inclusion mechanism
    """
    config.add_route('competences', '/competences')
    config.add_route(
        'competence_grid',
        '/competences/{id}',
        traverse='/competences/{id}',
    )

    config.add_route(
        'competence_grid_items',
        '/competences/{id}/items',
        traverse='/competences/{id}',
    )

    config.add_route(
        'competence_grid_item',
        '/competences/{id}/items/{iid:\d+}',
        traverse='/competence_items/{iid}',
    )

    config.add_route(
        'competence_grid_subitems',
        '/competences/{id}/items/{iid:\d+}/subitems',
        traverse='/competence_items/{iid}',
    )

    config.add_route(
        'competence_grid_subitem',
        '/competences/{id}/items/{iid:\d+}/subitems/{sid:\d+}',
        traverse='/competence_subitems/{sid}',
    )

    config.add_view(
        competence_index_view,
        route_name='competences',
        renderer='/accompagnement/competences.mako',
        permission='edit',
    )
    config.add_view(
        competence_grid_view,
        route_name='competence_grid',
        renderer='/accompagnement/competence.mako',
        permission='edit',
    )
    for attr in ('get', ):
        config.add_view(
            RestCompetenceGrid,
            attr=attr,
            route_name='competence_grid',
            renderer='json',
            permission='edit',
            xhr=True,
            request_method=attr.upper(),
        )

    config.add_view(
        competence_form_options,
        route_name='competence_grid',
        renderer='json',
        xhr=True,
        request_method='GET',
        request_param="action=options",
        permission='edit',
    )