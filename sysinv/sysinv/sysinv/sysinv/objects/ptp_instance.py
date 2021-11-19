########################################################################
#
# Copyright (c) 2021 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
########################################################################

from sysinv.db import api as db_api
from sysinv.objects import base
from sysinv.objects import utils
from sysinv.objects import ptp_paramowner


class PtpInstance(ptp_paramowner.PtpParameterOwner):

    dbapi = db_api.get_instance()

    fields = dict({
            'name': utils.str_or_none,
            'service': utils.str_or_none
             }, **ptp_paramowner.PtpParameterOwner.fields)

    _foreign_fields = {}

    @base.remotable_classmethod
    def get_by_uuid(cls, context, uuid):
        return cls.dbapi.ptp_instance_get(uuid)
