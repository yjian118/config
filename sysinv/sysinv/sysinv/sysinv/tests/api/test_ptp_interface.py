########################################################################
#
# Copyright (c) 2021 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
########################################################################

from six.moves import http_client
from sysinv.common import constants
from sysinv.tests.api import base
from sysinv.tests.db import base as dbbase
from sysinv.tests.db import utils as dbutils


class BasePtpInterfaceTestCase(base.FunctionalTest, dbbase.BaseHostTestCase):
    # Generic header passed in most API calls
    API_HEADERS = {'User-Agent': 'sysinv-test'}

    # Prefix for the URL
    API_PREFIX = '/ptp_interfaces'

    # Python table key for the list of results
    RESULT_KEY = 'ptp_interfaces'

    # Field that is known to exist for inputs and outputs
    COMMON_FIELD = 'ptp_instance_uuid'

    # Can perform API operations on this object at a sublevel of host
    HOST_PREFIX = '/ihosts'

    # Can perform API operations on this object at a sublevel of interfaces
    INTERFACE_PREFIX = '/iinterfaces'

    def setUp(self):
        super(BasePtpInterfaceTestCase, self).setUp()
        self.controller = self._create_test_host(constants.CONTROLLER)
        self.interface = dbutils.create_test_interface(
            ifname='ptp0',
            ifclass=constants.INTERFACE_CLASS_PLATFORM,
            forihostid=self.controller.id,
            ihost_uuid=self.controller.uuid)
        self.instance = dbutils.create_test_ptp_instance(
            name='testInstance',
            service=constants.PTP_INSTANCE_TYPE_PTP4L)

    def get_single_url(self, ptp_interface_uuid):
        return '%s/%s' % (self.API_PREFIX, ptp_interface_uuid)

    def get_host_scoped_url(self, host_uuid):
        return '%s/%s%s' % (self.HOST_PREFIX, host_uuid, self.API_PREFIX)

    def get_interface_scoped_url(self, interface_uuid):
        return '%s/%s%s' % (self.INTERFACE_PREFIX, interface_uuid,
                            self.API_PREFIX)

    def get_interface_url(self, interface_uuid):
        return '%s/%s' % (self.INTERFACE_PREFIX, interface_uuid)

    def get_post_object(self, ptp_instance_id, ptp_instance_uuid, name=None):
        return dbutils.get_test_ptp_interface(
            ptp_instance_id=ptp_instance_id,
            ptp_instance_uuid=ptp_instance_uuid,
            name=name)


class TestCreatePtpInterface(BasePtpInterfaceTestCase):

    def setUp(self):
        super(TestCreatePtpInterface, self).setUp()

    def _create_ptp_interface_success(self, name, ptp_instance_id, ptp_instance_uuid):
        ptp_interface_db = self.get_post_object(ptp_instance_id,
                                                ptp_instance_uuid,
                                                name)
        response = self.post_json(self.API_PREFIX, ptp_interface_db,
                                  headers=self.API_HEADERS)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(response.status_code, http_client.OK)
        self.assertEqual(response.json[self.COMMON_FIELD],
                         ptp_interface_db[self.COMMON_FIELD])

    def _create_ptp_interface_failed(self, name,
                                     ptp_instance_id, ptp_instance_uuid,
                                     status_code, error_message):
        ptp_interface_db = self.get_post_object(ptp_instance_id,
                                                ptp_instance_uuid,
                                                name)
        response = self.post_json(self.API_PREFIX, ptp_interface_db,
                                  headers=self.API_HEADERS,
                                  expect_errors=True)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(response.status_code, status_code)
        self.assertIn(error_message, response.json['error_message'])

    def test_create_ptp_interface_ok(self):
        self._create_ptp_interface_success('test',
                                           self.instance.id,
                                           self.instance.uuid)

    def test_create_ptp_interface_invalid_instance(self):
        fake_id = 0
        fake_uuid = '32dbb999-6c10-448d-aeca-964c50af6384'
        error_message = 'No PTP instance with id %s found' % fake_uuid
        self._create_ptp_interface_failed('test',
                                          fake_id,
                                          fake_uuid,
                                          status_code=http_client.NOT_FOUND,
                                          error_message=error_message)


class TestUpdatePtpInterface(BasePtpInterfaceTestCase):
    uuid = None

    def setUp(self):
        super(TestUpdatePtpInterface, self).setUp()
        ptp_interface = dbutils.create_test_ptp_interface(
            ptp_instance_id=self.instance.id,
            ptp_instance_uuid=self.instance.uuid)
        self.uuid = ptp_interface['uuid']

    def test_update_ptp_interface_add_parameter_ok(self):
        ptp_parameter_1 = dbutils.create_test_ptp_parameter(
            name='param1', value='value1')
        ptp_parameter_2 = dbutils.create_test_ptp_parameter(
            name='param2', value='value2')
        response = self.patch_json(self.get_single_url(self.uuid),
                                   [{'path': '/ptp_parameters/-',
                                     'value': ptp_parameter_1['uuid'],
                                     'op': 'add'},
                                    {'path': '/ptp_parameters/-',
                                     'value': ptp_parameter_2['uuid'],
                                     'op': 'add'}],
                                   headers=self.API_HEADERS)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status_code, http_client.OK)

    def test_update_ptp_interface_add_parameter_failed_no_interface(self):
        ptp_parameter = dbutils.create_test_ptp_parameter(name='name',
                                                          value='value')
        fake_uuid = 'f4c56ddf-aef3-46ed-b9aa-126a1faafd40'
        error_message = 'No PTP interface with id %s found.' % fake_uuid
        response = self.patch_json(self.get_single_url(fake_uuid),
                                   [{'path': '/ptp_parameters/-',
                                     'value': ptp_parameter['uuid'],
                                     'op': 'add'}],
                                   headers=self.API_HEADERS,
                                   expect_errors=True)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(response.status_code, http_client.NOT_FOUND)
        self.assertIn(error_message, response.json['error_message'])

    def test_update_ptp_interface_add_parameter_failed_no_param(self):
        fake_uuid = 'f4c56ddf-aef3-46ed-b9aa-126a1faafd40'
        error_message = 'No PTP parameter object found for %s' % fake_uuid
        response = self.patch_json(self.get_single_url(self.uuid),
                                   [{'path': '/ptp_parameters/-',
                                     'value': fake_uuid,
                                     'op': 'add'}],
                                   headers=self.API_HEADERS,
                                   expect_errors=True)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(response.status_code, http_client.BAD_REQUEST)
        self.assertIn(error_message, response.json['error_message'])

    def test_update_ptp_interface_delete_parameter_ok(self):
        ptp_parameter = dbutils.create_test_ptp_parameter(
            name='param1', value='value1')
        response = self.patch_json(self.get_single_url(self.uuid),
                                   [{'path': '/ptp_parameters/-',
                                     'value': ptp_parameter['uuid'],
                                     'op': 'add'}],
                                   headers=self.API_HEADERS)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status_code, http_client.OK)

        response = self.patch_json(self.get_single_url(self.uuid),
                                   [{'path': '/ptp_parameters/-',
                                     'value': ptp_parameter['uuid'],
                                     'op': 'remove'}],
                                   headers=self.API_HEADERS)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status_code, http_client.OK)


class TestInterfacePtpInterface(BasePtpInterfaceTestCase):
    def setUp(self):
        super(TestInterfacePtpInterface, self).setUp()

    def _assign_interface_ptp_interface_success(self):
        ptp_interface = dbutils.create_test_ptp_interface(
            ptp_instance_id=self.instance.id,
            ptp_instance_uuid=self.instance.uuid)
        ptp_interface_id = ptp_interface['id']
        response = self.patch_json(
            self.get_interface_url(self.interface.uuid),
            [{'path': '/ptp_interfaces/-',
              'value': ptp_interface_id,
              'op': 'add'}],
            headers=self.API_HEADERS)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status_code, http_client.OK)

        return ptp_interface_id

    def test_interface_ptp_interface_assign_ok(self):
        self._assign_interface_ptp_interface_success()

    def test_interface_ptp_interface_assign_failed(self):
        fake_id = 101
        error_message = 'No PTP interface object with id %s' % fake_id
        response = self.patch_json(
            self.get_interface_url(self.interface.uuid),
            [{'path': '/ptp_interfaces/-',
              'value': fake_id,
              'op': 'add'}],
            headers=self.API_HEADERS,
            expect_errors=True)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(response.status_code, http_client.BAD_REQUEST)
        self.assertIn(error_message, response.json['error_message'])

    def test_interface_ptp_interface_remove_ok(self):
        ptp_interface_id = self._assign_interface_ptp_interface_success()

        response = self.patch_json(
            self.get_interface_url(self.interface.uuid),
            [{'path': '/ptp_interfaces/-',
              'value': ptp_interface_id,
              'op': 'remove'}],
            headers=self.API_HEADERS)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status_code, http_client.OK)


class TestGetPtpInterface(BasePtpInterfaceTestCase):
    def setUp(self):
        super(TestGetPtpInterface, self).setUp()

    def test_get_ptp_interface_found(self):
        ptp_interface = dbutils.create_test_ptp_interface(
            ptp_instance_id=self.instance.id,
            ptp_instance_uuid=self.instance.uuid)
        response = self.get_json(self.get_single_url(ptp_interface['uuid']))
        self.assertIn(self.COMMON_FIELD, response)

    def test_get_ptp_interface_not_found(self):
        fake_uuid = 'f4c56ddf-aef3-46ed-b9aa-126a1faafd40'
        error_message = 'No PTP interface with id %s found' % fake_uuid

        response = self.get_json(self.get_single_url(fake_uuid),
                                 expect_errors=True)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(response.status_code, http_client.NOT_FOUND)
        self.assertIn(error_message, response.json['error_message'])


class TestListPtpInterface(BasePtpInterfaceTestCase):
    def setUp(self):
        super(TestListPtpInterface, self).setUp()
        self.worker = self._create_test_host(constants.WORKER)
        self._create_test_ptp_interfaces()

    def _create_test_ptp_interfaces(self):
        for i in range(5):
            ptp_interface = dbutils.create_test_ptp_interface(
                ptp_instance_id=self.instance.id,
                ptp_instance_uuid=self.instance.uuid)
            response = self.patch_json(
                self.get_interface_url(self.interface.uuid),
                [{'path': '/ptp_interfaces/-',
                  'value': ptp_interface['id'],
                  'op': 'add'}],
                headers=self.API_HEADERS)
            self.assertEqual(response.content_type, 'application/json')
            self.assertEqual(response.status_code, http_client.OK)

    def test_list_ptp_interface_all(self):
        response = self.get_json(self.API_PREFIX)
        for result in response[self.RESULT_KEY]:
            self.assertIn(self.COMMON_FIELD, result)

    def test_list_ptp_interface_empty(self):
        response = self.get_json(self.get_host_scoped_url(self.worker.uuid))
        self.assertEqual([], response[self.RESULT_KEY])

    def test_list_ptp_interface_host(self):
        response = self.get_json(
            self.get_host_scoped_url(self.controller.uuid))
        for result in response[self.RESULT_KEY]:
            self.assertIn(self.controller.hostname, result['hostnames'])

    def test_list_ptp_interface_interface(self):
        response = self.get_json(
            self.get_interface_scoped_url(self.interface.uuid))
        interface_name = '%s/%s' % (self.controller.hostname,
                                    self.interface.ifname)
        for result in response[self.RESULT_KEY]:
            self.assertIn(interface_name, result['interface_names'])


class TestDeletePtpInterface(BasePtpInterfaceTestCase):
    """ Tests deletion.
        Typically delete APIs return NO CONTENT.
        python2 and python3 libraries may return different
        content_type (None, or empty json) when NO_CONTENT returned.
    """
    ptp_interface = None
    uuid = None

    def setUp(self):
        super(TestDeletePtpInterface, self).setUp()
        self.ptp_interface = dbutils.create_test_ptp_interface(
            ptp_instance_id=self.instance.id,
            ptp_instance_uuid=self.instance.uuid)
        self.uuid = self.ptp_interface['uuid']

    def test_delete_ptp_interface_ok(self):
        response = self.delete(self.get_single_url(self.uuid),
                               headers=self.API_HEADERS)
        self.assertEqual(response.status_code, http_client.NO_CONTENT)

        # Check the PTP interface was indeed removed
        error_message = \
            'No PTP interface with id %s found' % self.uuid
        response = self.get_json(self.get_single_url(self.uuid),
                                 expect_errors=True)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(response.status_code, http_client.NOT_FOUND)
        self.assertIn(error_message, response.json['error_message'])

    def test_delete_ptp_interface_with_interface_failed(self):
        response = self.patch_json(
            self.get_interface_url(self.interface.uuid),
            [{'path': '/ptp_interfaces/-',
              'value': self.ptp_interface['id'],
              'op': 'add'}],
            headers=self.API_HEADERS)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status_code, http_client.OK)

        response = self.delete(self.get_single_url(self.uuid),
                               headers=self.API_HEADERS, expect_errors=True)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(response.status_code, http_client.BAD_REQUEST)
        self.assertIn('still associated with host interface',
                      response.json['error_message'])

    def test_delete_ptp_interface_with_parameters_failed(self):
        ptp_parameter = dbutils.create_test_ptp_parameter(
            name='fake-param', value='fake-value')
        response = self.patch_json(self.get_single_url(self.uuid),
                                   [{'path': '/ptp_parameters/-',
                                     'value': ptp_parameter['uuid'],
                                     'op': 'add'}],
                                   headers=self.API_HEADERS)
        self.assertEqual(response.content_type, 'application/json')
        self.assertEqual(response.status_code, http_client.OK)

        response = self.delete(self.get_single_url(self.uuid),
                               headers=self.API_HEADERS, expect_errors=True)
        self.assertEqual('application/json', response.content_type)
        self.assertEqual(response.status_code, http_client.BAD_REQUEST)
        self.assertIn('still associated with PTP parameter',
                      response.json['error_message'])
