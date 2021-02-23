################################################################################
#
# README
#
# This function doesn't support port-range designation.
#
################################################################################

import boto3
from botocore.exceptions import ClientError
import socket

VAR_SGID = 'sg-089e981b7873c45f2'
VAR_HOSTNAMES = [
  ## please follow this format => 'url:port[:port]' 
  'apigateway.cn-north-1.amazonaws.com.cn:443',
  'execute-api.cn-north-1.amazonaws.com.cn:443',
  # 'google.com:443:80',
]

ec2 = boto3.client('ec2')

def lambda_handler(event, context):
  hostsExisted = getHostExisted(VAR_SGID)
  hostsResolved = resolveHosts()
  print(hostsExisted)
  print(hostsResolved)
  delObj, addObj = compareObj(hostsExisted, hostsResolved)
  print('delObj:', delObj)
  print('addObj:', addObj)
  modSGRules(VAR_SGID, delObj, 'Del')
  modSGRules(VAR_SGID, addObj, 'Add')
  
def resolveHosts():
  hostsResolved = {}
  for entry in VAR_HOSTNAMES:
    try:
      urlAndPorts = entry.split(':')
      url = urlAndPorts[0]
      ports = map(int, urlAndPorts[1:])
      res = socket.gethostbyname_ex(url)
      for port in ports:
        if port not in hostsResolved:
          hostsResolved[port] = {}
        hostsResolved[port][url] = res[2]
    except socket.gaierror:
      print('[Warn] No record for url: %s' % url)
  return hostsResolved

def getHostExisted(SGID):
  IpPermissions = getSGRules(SGID)
  hostExisted = {}
  for i in IpPermissions:
    for j in i['IpRanges']:
      if 'Description' in j and j['Description'].startswith('LAMBDA-MANAGED'):
        hostname = j['Description'].split(':')[1]
        ip = j['CidrIp'].split('/')[0]
        port = i['FromPort']
        if port not in hostExisted:
          hostExisted[port] = {}
        if hostname not in hostExisted[port]:
          hostExisted[port][hostname]=[]
        hostExisted[port][hostname].append(ip)
  return hostExisted

def getSGRules(SGID):
  try:
    response = ec2.describe_security_groups(GroupIds=[SGID])
  except ClientError as e:
    print(e)
  print(response)
  IpPermissions = response['SecurityGroups'][0]['IpPermissions']
  return IpPermissions
  
def compareObj(oldObj, curObj):
  delObj, addObj = {}, {}
  
  oldports, curports = set(oldObj.keys()), set(curObj.keys())
  delports = oldports.difference(curports)
  addports = curports.difference(oldports)
  modports = oldports.intersection(curports)
  
  for p in delports:
    delObj[p] = oldObj[p]
  for p in addports:
    addObj[p] = curObj[p]
  for p in modports:
    
    oldhosts, curhosts = set(oldObj[p].keys()), set(curObj[p].keys())
    delhosts = oldhosts.difference(curhosts)
    addhosts = curhosts.difference(oldhosts)
    modhosts = oldhosts.intersection(curhosts)
    
    if p not in delObj:
      delObj[p] = {}
    if p not in addObj:
      addObj[p] = {}
    for h in delhosts:
      delObj[p][h] = oldObj[p][h]
    for h in addhosts:
      addObj[p][h] = curObj[p][h]
    for h in modhosts:
      oldips = oldObj[p][h]
      curips = curObj[p][h]
      delObj[p][h] = list(set(oldips).difference(curips))
      addObj[p][h] = list(set(curips).difference(oldips))

  return delObj, addObj

def modSGRules(SGID, hostEntries, action = 'Add'):
  print('%s SG rules...' % action)
  IpPermissions = []
  for port, hosts in hostEntries.items():
    IpRanges = []
    for host, ips in hosts.items():
      for ip in ips:
        IpRanges.append({
          'CidrIp': '%s/32' % ip,
          'Description': 'LAMBDA-MANAGED:%s:DO-NOT-MODIFY' % host 
        })
    if IpRanges:
      IpPermissions.append({
        'IpProtocol': 'tcp',
        'FromPort': port,
        'ToPort': port,
        'IpRanges': IpRanges
      })
  print('%s IpPermissions:' % action, IpPermissions)
  if not IpPermissions:
    print('No entry for update')
  else:
    try:
      if action is 'Add':
        data = ec2.authorize_security_group_ingress(
          GroupId = SGID,
          IpPermissions = IpPermissions
        )
      elif action is 'Del' :
        data = ec2.revoke_security_group_ingress(
        GroupId = SGID,
        IpPermissions = IpPermissions
      )
      print('Ingress Successfully %s:%s' % (action, data))
    except ClientError as e:
      print(e)
