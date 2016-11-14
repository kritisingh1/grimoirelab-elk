#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#
# Copyright (C) 2015 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#   Alvaro del Castillo San Felix <acs@bitergia.com>
#

import json
import logging

from dateutil import parser

from grimoire.elk.enrich import Enrich, metadata

class ConfluenceEnrich(Enrich):

    def get_elastic_mappings(self):

        mapping = """
        {
            "properties": {
                "title_analyzed": {
                  "type": "string",
                  "index":"analyzed"
                  }
           }
        } """

        return {"items":mapping}


    def get_identities(self, item):
        """ Return the identities from an item """
        identities = []

        version = item['data']['version']

        user = self.get_sh_identity(version)
        identities.append(user)
        return identities

    def get_sh_identity(self, version):
        identity = {}
        identity['username'] = None
        identity['email'] = None
        identity['name'] = None
        if 'by' in version:
            if 'username' in version['by']:
                identity['username'] = version['by']['username']
            identity['name'] = version['by']['displayName']
        return identity

    def get_item_sh(self, item):
        """ Add sorting hat enrichment fields for the author of the item """

        eitem = {}  # Item enriched
        identity  = self.get_sh_identity(item['data']['version'])
        update = parser.parse(item[self.get_field_date()])
        eitem = self.get_item_sh_fields(identity, update)

        return eitem

    def get_review_sh(self, revision, item):
        """ Add sorting hat enrichment fields for the author of the revision """

        identity  = self.get_sh_identity(revision)
        erevision = self.get_item_sh_fields(identity, item)

        return erevision

    @metadata
    def get_rich_item(self, item):
        eitem = {}

        # metadata fields to copy
        copy_fields = ["metadata__updated_on","metadata__timestamp","ocean-unique-id","origin"]
        for f in copy_fields:
            if f in item:
                eitem[f] = item[f]
            else:
                eitem[f] = None
        # The real data
        page = item['data']

        # data fields to copy
        copy_fields = ["type", "id", "status", "title"]
        for f in copy_fields:
            if f in page:
                eitem[f] = page[f]
            else:
                eitem[f] = None
        # Fields which names are translated
        map_fields = {"title": "title_analyzed"}
        for fn in map_fields:
            eitem[map_fields[fn]] = page[fn]


        version = page['version']

        if 'username' in version['by']:
            eitem['author_name'] = version['by']['username']
        else:
            eitem['author_name'] = version['by']['displayName']

        eitem['message'] = None
        if 'message' in version:
            eitem['message'] = version['message']
        eitem['version'] = version['number']
        eitem['date'] = version['when']
        eitem['url'] =  page['_links']['base'] + page['_links']['webui']

        # Specific enrichment
        if page['type'] == 'page':
            if page['version']['number'] == 1:
                eitem['type'] = 'new_page'
        eitem['is_'+eitem['type']] = 1


        if self.sortinghat:
            eitem.update(self.get_item_sh(item))

        return eitem
