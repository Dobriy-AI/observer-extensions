# Observer Extensions

Open-source extensions for Semantic Observer, enabled separately for each project.

The library starts with two working extensions:

| Extension | Purpose |
| --- | --- |
| [Data quality](extensions/data-quality/extension.json) | Report typed resources missing labels or direct source references. |
| [Graph inventory](extensions/graph-inventory/extension.json) | Count distinct resources by recorded RDF class. |

Both expose a project page, HTTP operations, MCP tools and RDF reports. They read the selected project's authorised graph and write only their own reports. They do not replace source facts, merge identities or access another project's data.

## Install

In your project, open **Extensions**, choose an extension and select **Add to project**. Project administrators control installation, report visibility and runner access. Reports are private to administrators by default. Making reports visible to project readers follows the project's own public/private access policy.

Open the extension and choose **Run checks**. Each accepted report records its input revision, extension version, manifest digest and exact queries. An unchanged idempotency key returns the same run. Limits are one active run and 30 reports per extension per project per day. Checks must return no more than 200 record types. Oversized results fail explicitly rather than saving a partial report.

Disabling an extension revokes runner credentials and removes its reports from the exposed project dataset. Uninstalling also removes the installation. Historical reports and audit records remain retained but are not exposed by that installation. No other contributor's graph statements are removed.

## Run from an agent or script

Create a credential under the extension's **Settings → Runner access**. It is shown once, expires after 30 days, and grants only this project and extension. A new credential replaces the previous one.

```sh
export OBSERVER_BASE_URL=https://your-project.semantic.observer
export OBSERVER_EXTENSION=graph-inventory
# Set OBSERVER_EXTENSION_TOKEN through your secret manager.
python3 examples/run.py
```

The script reads the installation context and runs its checks through the supported API. Use `--submit` to calculate a report through project-scoped reads and submit it for review. The administrator verifies and publishes it. Observer recomputes the declared checks before acceptance and rejects stale inputs or mismatched results.

MCP is available at the project's `/mcp` endpoint using the same Bearer credential. This installation adds `graph_inventory__report` and `graph_inventory__run`. Data quality uses `data_quality__report` and `data_quality__run`. Read-only users see only permitted report tools. Permission is checked again on every invocation. Runner credentials cannot configure installations or approve submitted contributions.

## Develop

The first runtime is declarative: a reviewed manifest declares bounded, read-only SPARQL checks. Observer provides the interface, execution, provenance, API and MCP adapters. Arbitrary JavaScript, Python, HTML, container images and remote services are not executed by this release.

1. Copy an example manifest and choose a unique ID and namespace.
2. Define checks with `?entity` and `?type`. The host supplies the pinned project graph and aggregation.
3. Add tests, including unrelated project data and empty results.
4. Open a pull request with the manifest, licence and evidence of validation.

Admission is reviewed. A PR does not automatically execute or deploy code. Accepted manifests are pinned into an Observer release. Installation records pin their version and digest. If capabilities change, the installed version cannot run until the installation has been reviewed and replaced.

The [module template](https://github.com/semantisch/semantic-observer-module-template) separately demonstrates evidence-backed entity proposals. Its ORCID example is not an approved report extension and cannot be submitted to the report endpoint. Other contribution schemas and isolated custom interfaces require additional host contracts.

## API contract

The project resolves from its host or the authenticated credential. A body-supplied project ID never changes access.

| Method and path | Access |
| --- | --- |
| `GET /api/v1/extensions` | Public catalogue |
| `GET /api/v1/extensions/{id}/manifest` | Public manifest |
| `GET /api/v1/extensions/{id}/context` | Administrator or scoped runner |
| `POST /api/v1/extensions/{id}/query` | Administrator or scoped runner, read-only project SPARQL |
| `POST /api/v1/extensions/{id}/run` | Administrator or scoped runner |
| `POST /api/v1/extensions/{id}/contributions` | Submit a report, never approve it |
| `GET /api/v1/extensions/{id}/reports` | Authorised project readers when enabled |
| `POST /api/v1/extensions/{id}/reports/{reportId}/accept` | Project administrator |
| `GET /api/v1/extensions/{id}/reports/{reportId}.ttl` | Authorised RDF export |

Run and contribution requests require `Idempotency-Key` with 8–100 alphanumeric, hyphen or underscore characters. Reusing a key for different input is rejected. Installation/settings/token changes require an administrator session and a matching Origin header. Read tokens cannot write.

Contribution body:

```json
{
  "inputRevision": "https://example.org/project/snapshots/revision",
  "result": {
    "checks": [
      {"id": "record-types", "rows": [{"type": "https://example.org/Device", "count": 2}]}
    ]
  }
}
```

Validation is enforced by the host. Entity or source URI prefixes do not establish project membership. An entity may be shared across projects while its evidence and extension results remain restricted.

## Validation

```sh
python3 -m unittest discover -s tests -v
```

Observer's integration tests additionally use PostgreSQL and an RDF engine to exercise installations, project isolation, graph publication, false reports, MCP, revocation and retained audit history.

Code is MIT licensed. Data retains its source and project licensing. Installing an extension does not relicense imported data.
