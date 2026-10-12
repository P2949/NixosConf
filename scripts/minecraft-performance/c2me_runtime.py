"""Fail closed when the pinned C2ME executor policy is not effective."""

import re
import tomllib

VERSION = '0.4.2-alpha.0.90+26.3'
SHA256 = '69c89a014b12428e5c8b3cff1d00f78ec0141fce5f3997ab1a70ee8168999291'


def verify_startup(inventory, policy, log):
    mods = [mod for mod in inventory if mod['id'] == 'c2me']
    if not mods:
        return None
    if len(mods) != 1 or mods[0]['version'] != VERSION or mods[0]['sha256'] != SHA256:
        raise RuntimeError('FAIL_C2ME_ARTIFACT_IDENTITY')
    config = tomllib.loads(policy)
    if config.get('version') != 3 or config.get('globalExecutorParallelism') != 4:
        raise RuntimeError('FAIL_CONFIGURATION_NOT_APPLIED')
    effective = re.findall(r'Global Executor Parallelism: (\d+) configured,', log)
    if effective != ['4'] or 'Config version mismatch, resetting config' in log:
        raise RuntimeError('FAIL_CONFIGURATION_NOT_APPLIED')
    return {'mod_version': VERSION, 'artifact_sha256': SHA256,
            'effective_global_executor_parallelism': 4}
