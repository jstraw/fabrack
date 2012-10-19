#!/usr/bin/env/python

import os
import os.path
import pickle
import re
import sys

import novaclient.v1_1.client as novaclient
import openstack.compute
from fabric.api import env

us_authurl_v1_0 = "https://auth.api.rackspacecloud.com/v1.0"
uk_authurl_v1_0 = "https://lon.auth.api.rackspacecloud.com/v1.0"

us_authurl_v1_1 = "https://auth.api.rackspacecloud.com/v1.1"
uk_authurl_v1_1 = "https://lon.auth.api.rackspacecloud.com/v1.1"

us_authurl_v2_0 = "https://auth.api.rackspacecloud.com/v2.0/tokens"
uk_authurl_v2_0 = "https://lon.auth.api.rackspacecloud.com/v2.0/tokens"

def create_server_list(user, apikey, account_id, region=None, path=os.path.expanduser('~/.fabrackservers')):
  """Creates a full list of Rackspace Cloud Servers"""
  if region == 'uk':
    auth = (uk_authurl_v1_0, uk_authurl_v2_0)
    next_gen_dc = ['lon']
  else:
    auth = (us_authurl_v1_0, us_authurl_v2_0)
    next_gen_dc = ['ord', 'dfw']
  servers = []
  first_gen = openstack.compute.Client(username=user, apikey=apikey, 
        auth_url=auth[1], service_type='compute')
  for server in first_gen.servers.list():
    servers.append({ 'name': server.name, 'addresses': server.addresses, 
        'generation': 1 })

  for r in next_gen_dc:
    next_gen = novaclient.Client(user, apikey, account_id, auth_url=auth[2], 
                 region_name=r, service_name='cloudServersOpenStack')
    for server in next_gen.servers.list():
      servers.append({ 'name': server.name, 'addresses': server.addresses, 
          'generation': 2 })
  with open(path, 'w') as fh:
    pickle.dump(servers, fh)
  return servers

def get_server_list(path=os.path.expanduser('~/.fabrackservers')):
  with open(path, 'r') as fh:
    servers = pickle.load(fh)
  return servers

def make_roles(rdict, path=None): 
  """Setup Fabric to create role definitions so @role('something') works"""
  if path:
    servers = get_server_list(path)
  else:
    servers = get_server_list()
  ip_type = env.public_ip is True and "public" or "private"
  for key in rdict.keys():
    env.roledefs[key] = []
  env.roledefs['all'] = []
  for server in servers:
    for (key, value) in rdict.iteritems():
      if value in server['name']:
        env.roledefs[key].append(server['addresses'][ip_type][0])
        env.roledefs['all'].append(server['addresses'][ip_type][0])
