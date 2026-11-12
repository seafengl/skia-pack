#! /usr/bin/env python3

import common, json, os, re, sys, urllib.error, urllib.request

def tag_url(repo, version):
  return 'https://api.github.com/repos/' + repo + '/releases/tags/' + version

def releases_url(repo):
  return 'https://api.github.com/repos/' + repo + '/releases'

def main():
  os.chdir(os.path.join(os.path.dirname(__file__), os.pardir, 'skia'))
  version = common.version()
  build_type = common.build_type()
  machine = common.machine()
  target = common.target()
  classifier = common.classifier()
  os.chdir(os.pardir)

  zip = 'Skia-' + version + '-' + target + '-' + build_type + '-' + machine + classifier + '.zip'
  if not os.path.exists(zip):
    print('Can\'t find "' + zip + '"')
    return 1

  repo = common.github_repository()
  headers = common.github_headers()

  try:
    resp = urllib.request.urlopen(urllib.request.Request(tag_url(repo, version), headers=headers)).read()
  except urllib.error.HTTPError as e:
    if 404 != e.code:
      print('Can not look up release "' + version + '" in ' + repo + ': ' + str(e.code))
      print(e.read().decode('utf-8', errors='replace'))
      return 1
    data = '{"tag_name":"' + version + '","name":"' + version + '"}'
    try:
      resp = urllib.request.urlopen(urllib.request.Request(releases_url(repo), data=data.encode('utf-8'), headers=headers)).read()
    except urllib.error.HTTPError as e:
      print('Can not create release "' + version + '" in ' + repo + ': ' + str(e.code))
      print(e.read().decode('utf-8', errors='replace'))
      return 1
  upload_url = re.match('https://.*/assets', json.loads(resp.decode('utf-8'))['upload_url']).group(0)

  print('Uploading', zip, 'to ' + repo)
  headers['Content-Type'] = 'application/zip'
  headers['Content-Length'] = os.path.getsize(zip)
  try:
    with open(zip, 'rb') as data:
      urllib.request.urlopen(urllib.request.Request(upload_url + '?name=' + zip, data=data, headers=headers))
  except urllib.error.HTTPError as e:
    body = e.read().decode('utf-8', errors='replace')
    # Re-running a workflow for an already published build is not an error
    if 422 == e.code and 'already_exists' in body:
      print('> Asset "' + zip + '" already exists, skipping')
      return 0
    print('Can not upload "' + zip + '" to ' + repo + ': ' + str(e.code))
    print(body)
    return 1

  print('> Uploaded "' + zip + '" to ' + repo)
  return 0

if __name__ == '__main__':
  sys.exit(main())
