from conftest import CONTRACT
import json


URLS = ['https://law.example/standard', 'https://agency.example/decision', 'https://evidence.example/packet']
FINDINGS = ['Immediate structural safety risk exists', 'No narrower temporary measure is adequate']


def opened(vm, deploy, owner):
    vm.strict_mocks = True
    vm.check_pickling = True
    vm.sender = owner
    contract = deploy(CONTRACT)
    contract.open_docket('fd-4', 'Community hall closure', FINDINGS, *URLS)
    return contract


def sources(vm):
    vm.mock_web(r'law\.example', {'status': 200, 'body': 'Closure requires immediate risk and inadequacy of narrower measures.'})
    vm.mock_web(r'agency\.example', {'status': 200, 'body': 'Immediate roof risk; partial fencing cannot protect all entrances.'})
    vm.mock_web(r'evidence\.example', {'status': 200, 'body': 'Engineering report shows roof displacement and evaluates fencing. No contrary report.'})


def mapped(index, **changes):
    row = {'index': index, 'standard_authorizes': True, 'decision_addresses': True, 'evidence_supports': True, 'counterevidence_unanswered': False}
    row.update(changes)
    return row


def llm(vm, rows):
    vm.mock_llm(r'.*FindingDocket support audit.*', json.dumps({'rows': rows}))


def test_complete_support_graph_is_reasoned(direct_vm, direct_deploy, direct_alice):
    contract = opened(direct_vm, direct_deploy, direct_alice)
    sources(direct_vm); llm(direct_vm, [mapped(0), mapped(1)])
    contract.review_reasoning('fd-4')
    row = contract.get_docket('fd-4')
    assert row['state'] == 'REASONED' and row['gap_indexes'] == [] and len(row['digests']) == 3


def test_unanswered_counterevidence_creates_gap(direct_vm, direct_deploy, direct_alice):
    contract = opened(direct_vm, direct_deploy, direct_alice)
    sources(direct_vm); llm(direct_vm, [mapped(0), mapped(1, counterevidence_unanswered=True)])
    contract.review_reasoning('fd-4')
    assert contract.get_docket('fd-4')['gap_indexes'] == [1]
    assert contract.get_docket('fd-4')['state'] == 'GAPPED'


def test_multiple_missing_edges_union_once(direct_vm, direct_deploy, direct_alice):
    contract = opened(direct_vm, direct_deploy, direct_alice)
    sources(direct_vm); llm(direct_vm, [mapped(0, decision_addresses=False, evidence_supports=False), mapped(1)])
    contract.review_reasoning('fd-4')
    assert contract.get_docket('fd-4')['gap_indexes'] == [0]


def test_validator_rejects_forged_support_edge(direct_vm, direct_deploy, direct_alice):
    contract = opened(direct_vm, direct_deploy, direct_alice)
    sources(direct_vm); llm(direct_vm, [mapped(0), mapped(1)])
    result = contract._review(contract.dockets['FD-4'])
    assert direct_vm.run_validator(leader_result=result) is True
    forged = {'digests': result['digests'], 'rows': [dict(item) for item in result['rows']]}
    forged['rows'][0]['evidence_supports'] = False
    assert direct_vm.run_validator(leader_result=forged) is False


def test_duplicate_source_slot_and_id_rejected(direct_vm, direct_deploy, direct_alice):
    contract = opened(direct_vm, direct_deploy, direct_alice)
    with direct_vm.expect_revert('unique docket id'):
        contract.open_docket('fd-4', 'Duplicate docket', FINDINGS, *URLS)
    with direct_vm.expect_revert('distinct source slots'):
        contract.open_docket('fd-5', 'Bad source slots', FINDINGS, URLS[0], URLS[0], URLS[2])


def test_cancel_authorization_and_terminal_replay(direct_vm, direct_deploy, direct_alice, direct_bob):
    contract = opened(direct_vm, direct_deploy, direct_alice)
    direct_vm.sender = direct_bob
    with direct_vm.expect_revert('owner of open docket'):
        contract.cancel_open('fd-4')
    direct_vm.sender = direct_alice; sources(direct_vm); llm(direct_vm, [mapped(0), mapped(1)])
    contract.review_reasoning('fd-4')
    with direct_vm.expect_revert('open docket required'):
        contract.review_reasoning('fd-4')
