"""Project-scoped extension runner. Credentials stay in the environment."""
import argparse
import json
import os
import uuid
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.parse import urlparse

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Use the canonical project URL. Credential redirects are disabled.')

PREFIXES = """PREFIX schema: <https://schema.org/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX dct: <http://purl.org/dc/terms/>
PREFIX prov: <http://www.w3.org/ns/prov#>
"""

def query(check, revision):
    if not revision.startswith(('https://', 'http://')) or any(c in revision for c in '<>"{}|^`\\ \r\n\t'):
        raise ValueError('Invalid pinned graph identifier')
    return PREFIXES + ('SELECT ?type (COUNT(DISTINCT ?entity) AS ?count) WHERE { GRAPH <' + revision + '> { ' + check['where'] + ' } } GROUP BY ?type ORDER BY DESC(?count) ?type LIMIT 201')

def main():
    args = argparse.ArgumentParser()
    args.add_argument('--submit', action='store_true')
    options = args.parse_args()
    base = os.environ['OBSERVER_BASE_URL'].rstrip('/')
    if urlparse(base).scheme != 'https' and urlparse(base).hostname not in ('127.0.0.1', 'localhost'):
        raise ValueError('Use HTTPS for remote projects')
    extension = os.environ.get('OBSERVER_EXTENSION', 'graph-inventory')
    if not extension or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in extension):
        raise ValueError('Invalid extension ID')
    token = os.environ['OBSERVER_EXTENSION_TOKEN']
    endpoint = base + '/api/v1/extensions/' + extension
    key = str(uuid.uuid4())
    def request(path, data=None):
        headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json', 'Idempotency-Key': key}
        req = Request(endpoint + path, data=None if data is None else json.dumps(data).encode(), headers=headers)
        with build_opener(NoRedirect()).open(req, timeout=60) as response:
            return json.load(response)
    context = request('/context')
    if options.submit:
        checks = []
        for check in context['manifest']['checks']:
            result = request('/query', {'query': query(check, context['inputRevision'])})
            rows = [{'type': r['type']['value'], 'count': int(r['count']['value'])} for r in result['results']['bindings']]
            if len(rows) > 200:
                raise ValueError('Too many record types. No partial report will be submitted.')
            checks.append({'id': check['id'], 'rows': rows})
        result = request('/contributions', {'inputRevision': context['inputRevision'], 'result': {'checks': checks}})
    else:
        result = request('/run', {})
    print(json.dumps({'id': result['report']['id'], 'status': result['report']['status']}, indent=2))

if __name__ == '__main__':
    main()
