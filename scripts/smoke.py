import json
import re
import time
from pathlib import Path

from genlayer_py import create_account, create_client
from genlayer_py.chains import studionet
from genlayer_py.contracts import actions as contract_actions


def calldata_compat(method=None, args=None, kwargs=None):
    result = {}
    if method is not None:
        result['method'] = method
    if args:
        result['args'] = args
    if kwargs:
        result['kwargs'] = kwargs
    return result


contract_actions.make_calldata_object = calldata_compat
ROOT = Path(__file__).parents[1]
ENV = (ROOT.parents[3] / 'accounts.env').read_text()
DEPLOYMENT = json.loads((ROOT / 'deployment.json').read_text())
ADDRESS = DEPLOYMENT['contractAddress']
COMMIT = DEPLOYMENT['sourceCommit']


def account(number):
    key = re.search(rf'^ACCOUNT_{number}_GENLAYER_PRIVATE_KEY\\s*=\\s*"?([^"\\r\\n]+)', ENV, re.M).group(1).strip()
    return create_account(account_private_key=key)


def client(number):
    return create_client(chain=studionet, account=account(number))


def write(number, name, args):
    active = client(number)
    tx = active.write_contract(address=ADDRESS, function_name=name, args=args)
    print(name + '_tx=' + str(tx), flush=True)
    receipt = active.wait_for_transaction_receipt(transaction_hash=tx, wait_until='finalized', retries=180, interval=5000, full_transaction=True)
    leaders = receipt.get('consensus_data', {}).get('leader_receipt') or []
    leaders = [leaders] if isinstance(leaders, dict) else leaders
    assert receipt.get('result_name') == 'MAJORITY_AGREE'
    assert any(item.get('execution_result') == 'SUCCESS' for item in leaders)
    return str(tx)

base = f'https://raw.githubusercontent.com/warnedwarn/finding-docket/{COMMIT}/evidence'
docket_id = 'FIND-' + str(int(time.time()))
transactions = {}
transactions['open'] = write(2, 'open_docket', [
    docket_id, 'Community hall closure',
    ['Immediate structural safety risk exists', 'No narrower temporary measure is adequate'],
    base + '/standard.md', base + '/decision.md', base + '/packet.md',
])
transactions['review'] = write(2, 'review_reasoning', [docket_id])
state = client(2).read_contract(address=ADDRESS, function_name='get_docket', args=[docket_id])
assert state['state'] == 'REASONED'
assert state['gap_indexes'] == []
proof = {'docketId': docket_id, 'transactions': transactions, 'state': state,
         'disclosure': 'The standard, decision, and packet are operator-authored technical fixtures.'}
(ROOT / 'evidence' / 'live-proof.json').write_text(json.dumps(proof, indent=2) + '\n')
print(json.dumps(proof, indent=2), flush=True)

