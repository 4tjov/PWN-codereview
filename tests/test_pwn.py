from scripts.helpful_scripts import get_account
import time
from brownie import (
    PWN,
    PWNDeed,
    PWNVault,
    network,
    config,
    ERC20MyToken,
    ERC721MyToken,
    ERC1155MyToken,
    accounts,
    exceptions,
    chain,
)
from scripts.deploy_pwn import (
    deploy_pwn,
    set_PWN_ownership,
    deploy_testing_tokens,
    set_approve,
    send_token,
    pwn_create_deed,
    make_offer,
    revoke_deed,
    accept_offer,
    revoke_offer,
    repay_loan,
    claim_deed,
    ERC1155_VAL,
    ERC721_VAL,
    ERC20_VAL,
)
import pytest


def base_set_up(PWN_OWNER, PLEDGER, LENDER):

    pwn_deed, pwn_vault, pwn = deploy_pwn(PWN_OWNER)
    set_PWN_ownership(PWN_OWNER)
    erc20, erc721, erc721_token_id, erc1155, erc1155_id = deploy_testing_tokens(
        LENDER, PLEDGER, PLEDGER
    )

    send_token(PLEDGER, LENDER, 200, erc20, ERC20_VAL)
    return pwn_deed, pwn_vault, pwn, erc20, erc721, erc721_token_id, erc1155, erc1155_id


def test_set_pwn():
    owner = get_account(index=0)
    pwn_deed, pwn_vault, pwn = deploy_pwn(owner)
    set_PWN_ownership(owner)
    assert pwn.address == pwn_deed.PWN()
    assert pwn.address == pwn_vault.PWN()


def test_create_deed():
    PWN_OWNER = get_account(index=0)
    PLEDGER = get_account(index=1)
    LENDER = get_account(index=2)
    (
        pwn_deed,
        pwn_vault,
        pwn,
        erc20,
        erc721,
        erc721_token_id,
        erc1155,
        erc1155_id,
    ) = base_set_up(PWN_OWNER, PLEDGER, LENDER)

    with pytest.raises(exceptions.VirtualMachineError):
        deed_token_id = pwn_create_deed(
            erc721.address, 1, 3600, erc721_token_id, 1, PLEDGER
        )
    set_approve(PLEDGER, pwn_vault.address, erc721, ERC721_VAL, erc721_token_id)
    deed_token_id = pwn_create_deed(
        erc721.address, 1, 3600, erc721_token_id, 1, PLEDGER
    )
    assert (
        1,
        "0x0000000000000000000000000000000000000000",
        3600,
        0,
        (erc721.address, 1, 1, 0),
        "0x0000000000000000000000000000000000000000000000000000000000000000",
    ) == pwn_deed.deeds(deed_token_id)
    assert (
        "0xe7CB1c67752cBb975a56815Af242ce2Ce63d3113",
        1,
        1,
        0,
    ) == pwn_deed.getDeedCollateral(deed_token_id)
    assert "0x0000000000000000000000000000000000000000" == pwn_deed.getBorrower(
        deed_token_id
    )
    assert 3600 == pwn_deed.getDuration(deed_token_id)
    assert 0 == pwn_deed.getExpiration(deed_token_id)
    assert 1 == pwn_deed.getDeedStatus(deed_token_id)

    with pytest.raises(exceptions.VirtualMachineError):
        deed_token_id = pwn_create_deed(erc20.address, 0, 3600, 0, 50, PLEDGER)

    with pytest.raises(exceptions.VirtualMachineError):
        deed_token_id = pwn_create_deed(
            erc1155.address, 2, 3600, erc1155_id, 2, PLEDGER
        )
    set_approve(PLEDGER, pwn_vault.address, erc20, ERC20_VAL, amount=50)
    set_approve(PLEDGER, pwn_vault.address, erc1155, ERC1155_VAL, erc1155_id)
    did_erc20 = pwn_create_deed(erc20.address, 0, 3600, 0, 50, PLEDGER)
    did_erc1155 = pwn_create_deed(erc1155.address, 2, 3600, erc1155_id, 2, PLEDGER)
    assert pwn_deed.deeds(did_erc20) == (
        1,
        "0x0000000000000000000000000000000000000000",
        3600,
        0,
        (erc20.address, 0, 50, 0),
        "0x0000000000000000000000000000000000000000000000000000000000000000",
    )
    assert pwn_deed.deeds(did_erc1155) == (
        1,
        "0x0000000000000000000000000000000000000000",
        3600,
        0,
        (erc1155.address, 2, 2, 1),
        "0x0000000000000000000000000000000000000000000000000000000000000000",
    )
    assert erc20.balanceOf(pwn_vault) == 50
    assert erc20.balanceOf(PLEDGER) == 150

    assert erc721.balanceOf(pwn_vault) == 1
    assert erc721.balanceOf(PLEDGER) == 0

    assert erc1155.balanceOf(pwn_vault, erc1155_id) == 2
    assert erc1155.balanceOf(PLEDGER, erc1155_id) == 1

    set_approve(PLEDGER, pwn_vault.address, erc20, ERC20_VAL, amount=50)
    with pytest.raises(OverflowError):
        did_erc20 = pwn_create_deed(erc20.address, 0, -10, 0, 50, PLEDGER)


def test_revoke_deed():
    PWN_OWNER = get_account(index=0)
    PLEDGER_1 = get_account(index=1)
    PLEDGER_2 = get_account(index=2)
    RANDOM_USER = get_account(index=3)
    LENDER = get_account(index=4)
    (
        pwn_deed,
        pwn_vault,
        pwn,
        erc20,
        erc721,
        erc721_token_id,
        erc1155,
        erc1155_id,
    ) = base_set_up(PWN_OWNER, PLEDGER_1, LENDER)
    set_approve(PLEDGER_1, pwn_vault.address, erc721, ERC721_VAL, erc721_token_id)
    did_1 = pwn_create_deed(erc721.address, 1, 3600, erc721_token_id, 1, PLEDGER_1)
    send_token(PLEDGER_2, LENDER, 100, erc20, ERC20_VAL)
    set_approve(PLEDGER_2, pwn_vault.address, erc20, ERC20_VAL, amount=100)
    did_2 = pwn_create_deed(erc20.address, 0, 3600, 0, 100, PLEDGER_2)
    set_approve(PLEDGER_1, pwn_vault.address, erc1155, ERC1155_VAL, erc1155_id)
    did_3 = pwn_create_deed(erc1155.address, 2, 3600, erc1155_id, 3, PLEDGER_1)

    with pytest.raises(exceptions.VirtualMachineError):
        revoke_deed(did_1, RANDOM_USER)

    with pytest.raises(exceptions.VirtualMachineError):
        revoke_deed(did_1, PLEDGER_2)

    revoke_deed(did_1, PLEDGER_1)
    assert 0 == pwn_deed.getDeedStatus(did_1)

    assert pwn_deed.balanceOf(PLEDGER_1, did_1) == 0
    assert erc721.balanceOf(PLEDGER_1) == 1

    revoke_deed(did_2, PLEDGER_2)
    assert pwn_deed.balanceOf(PLEDGER_2, did_2) == 0
    assert erc20.balanceOf(PLEDGER_2) == 100

    print(pwn_deed.deeds(did_3))

    revoke_deed(did_3, PLEDGER_1)
    assert pwn_deed.balanceOf(PLEDGER_1, did_3) == 0
    assert erc1155.balanceOf(PLEDGER_1, erc1155_id) == 3

    set_approve(PLEDGER_1, pwn_vault.address, erc721, ERC721_VAL, erc721_token_id)
    did_4 = pwn_create_deed(erc721.address, 1, 3600, erc721_token_id, 1, PLEDGER_1)
    offer_id = make_offer(erc20.address, 100, did_4, 120, LENDER)
    set_approve(PLEDGER_1, pwn_vault.address, pwn_deed, ERC1155_VAL)
    set_approve(LENDER, pwn_vault.address, erc20, ERC20_VAL, amount=100)
    accept_offer(offer_id, PLEDGER_1)

    with pytest.raises(exceptions.VirtualMachineError):
        revoke_deed(did_4, LENDER)


def test_make_offer():
    PWN_OWNER = get_account(index=0)
    PLEDGER = get_account(index=1)
    LENDER = get_account(index=2)
    (
        pwn_deed,
        pwn_vault,
        pwn,
        erc20,
        erc721,
        erc721_token_id,
        erc1155,
        erc1155_id,
    ) = base_set_up(PWN_OWNER, PLEDGER, LENDER)
    set_approve(PLEDGER, pwn_vault.address, erc20, ERC20_VAL, amount=100)
    did_erc20 = pwn_create_deed(erc20.address, 0, 3600, 0, 100, PLEDGER)
    set_approve(PLEDGER, pwn_vault.address, erc721, ERC721_VAL, erc721_token_id)
    did_erc721 = pwn_create_deed(erc721.address, 1, 3600, erc721_token_id, 1, PLEDGER)
    set_approve(PLEDGER, pwn_vault.address, erc1155, ERC1155_VAL, erc1155_id)
    did_erc1155 = pwn_create_deed(erc1155.address, 2, 3600, erc1155_id, 3, PLEDGER)

    # this should make exception not sufficient balance
    offer_id = make_offer(erc20.address, 1100, did_erc20, 1500, LENDER)

    with pytest.raises(exceptions.VirtualMachineError):
        accept_offer(offer_id, PLEDGER)

    # set_approve(PLEDGER, pwn_vault.address, pwn_deed, ERC1155_VAL)

    offer_erc20 = make_offer(erc20.address, 110, did_erc20, 130, LENDER)
    offer_erc721 = make_offer(erc20.address, 110, did_erc721, 130, LENDER)
    offer_erc1155 = make_offer(erc20.address, 110, did_erc1155, 130, LENDER)

    assert (1, 130, LENDER.address, (erc20.address, 0, 110, 0)) == pwn_deed.offers(
        offer_erc20
    )
    assert (2, 130, LENDER.address, (erc20.address, 0, 110, 0)) == pwn_deed.offers(
        offer_erc721
    )
    assert (3, 130, LENDER.address, (erc20.address, 0, 110, 0)) == pwn_deed.offers(
        offer_erc1155
    )

    set_approve(PLEDGER, pwn_vault.address, pwn_deed, ERC1155_VAL)
    set_approve(LENDER, pwn_vault.address, erc20, ERC20_VAL, amount=110)
    accept_offer(offer_erc721, PLEDGER)
    with pytest.raises(exceptions.VirtualMachineError):
        offer_erc721 = make_offer(erc721.address, 110, did_erc721, 130, LENDER)


def test_revoke_offer():
    PWN_OWNER = get_account(index=0)
    PLEDGER = get_account(index=1)
    LENDER = get_account(index=2)
    RANDOM_USER = get_account(index=3)
    (
        pwn_deed,
        pwn_vault,
        pwn,
        erc20,
        erc721,
        erc721_token_id,
        erc1155,
        erc1155_id,
    ) = base_set_up(PWN_OWNER, PLEDGER, LENDER)
    set_approve(PLEDGER, pwn_vault.address, erc20, ERC20_VAL, amount=100)
    did_erc20 = pwn_create_deed(erc20.address, 0, 3600, 0, 100, PLEDGER)
    set_approve(PLEDGER, pwn_vault.address, erc721, ERC721_VAL, erc721_token_id)
    did_erc721 = pwn_create_deed(erc721.address, 1, 3600, erc721_token_id, 1, PLEDGER)
    set_approve(PLEDGER, pwn_vault.address, erc1155, ERC1155_VAL, erc1155_id)
    did_erc1155 = pwn_create_deed(erc1155.address, 2, 3600, erc1155_id, 3, PLEDGER)

    offer_erc20 = make_offer(erc20.address, 110, did_erc20, 130, LENDER)
    offer_erc721 = make_offer(erc20.address, 110, did_erc721, 130, LENDER)
    offer_erc1155 = make_offer(erc20.address, 110, did_erc1155, 130, LENDER)

    with pytest.raises(exceptions.VirtualMachineError):
        revoke_offer(offer_erc721, RANDOM_USER)

    offer_erc721_2 = make_offer(erc20.address, 110, did_erc721, 130, LENDER)
    revoke_offer(offer_erc721_2, LENDER)
    assert (
        0,
        0,
        "0x0000000000000000000000000000000000000000",
        ("0x0000000000000000000000000000000000000000", 0, 0, 0),
    ) == pwn_deed.offers(offer_erc721_2)

    set_approve(PLEDGER, pwn_vault.address, pwn_deed, ERC1155_VAL)
    set_approve(LENDER, pwn_vault.address, erc20, ERC20_VAL, amount=110)
    accept_offer(offer_erc721, PLEDGER)
    print(pwn_deed.deeds(did_erc721))
    with pytest.raises(exceptions.VirtualMachineError):
        revoke_offer(offer_erc721, LENDER)


def test_accept_offer():
    PWN_OWNER = get_account(index=0)
    PLEDGER = get_account(index=1)
    LENDER = get_account(index=2)
    RANDOM_USER = get_account(index=3)
    (
        pwn_deed,
        pwn_vault,
        pwn,
        erc20,
        erc721,
        erc721_token_id,
        erc1155,
        erc1155_id,
    ) = base_set_up(PWN_OWNER, PLEDGER, LENDER)
    set_approve(PLEDGER, pwn_vault.address, erc20, ERC20_VAL, amount=100)
    did_erc20 = pwn_create_deed(erc20.address, 0, 3600, 0, 100, PLEDGER)
    set_approve(PLEDGER, pwn_vault.address, erc721, ERC721_VAL, erc721_token_id)
    did_erc721 = pwn_create_deed(erc721.address, 1, 3600, erc721_token_id, 1, PLEDGER)
    set_approve(PLEDGER, pwn_vault.address, erc1155, ERC1155_VAL, erc1155_id)
    did_erc1155 = pwn_create_deed(erc1155.address, 2, 3600, erc1155_id, 3, PLEDGER)

    offer_erc20 = make_offer(erc20.address, 110, did_erc20, 130, LENDER)
    offer_erc721 = make_offer(erc20.address, 110, did_erc721, 130, LENDER)
    offer_erc721_2 = make_offer(erc20.address, 1000, did_erc721, 1100, LENDER)
    offer_erc721_3 = make_offer(erc20.address, 90, did_erc721, 130, LENDER)
    offer_erc1155 = make_offer(erc20.address, 110, did_erc1155, 130, LENDER)

    # ERC20: insufficient allowance
    with pytest.raises(exceptions.VirtualMachineError):
        accept_offer(offer_erc721_2, PLEDGER)

    set_approve(LENDER, pwn_vault.address, erc20, ERC20_VAL, amount=1000)

    # ERC20: transfer amount exceeds balance
    with pytest.raises(exceptions.VirtualMachineError):
        accept_offer(offer_erc721_2, PLEDGER)

    # ERC1155: caller is not owner nor approved
    with pytest.raises(exceptions.VirtualMachineError):
        accept_offer(offer_erc721, PLEDGER)

    # revert: The deed doesn't belong to the caller
    with pytest.raises(exceptions.VirtualMachineError):
        accept_offer(offer_erc721, RANDOM_USER)

    set_approve(PLEDGER, pwn_vault.address, pwn_deed, ERC1155_VAL)
    accept_offer(offer_erc20, PLEDGER)
    accept_offer(offer_erc721, PLEDGER)
    accept_offer(offer_erc1155, PLEDGER)
    assert offer_erc20 == pwn_deed.getAcceptedOffer(did_erc20)
    assert offer_erc721 == pwn_deed.getAcceptedOffer(did_erc721)
    assert offer_erc1155 == pwn_deed.getAcceptedOffer(did_erc1155)

    assert 100 == erc20.balanceOf(pwn_vault)
    assert 1 == erc721.balanceOf(pwn_vault)
    assert 3 == erc1155.balanceOf(pwn_vault, erc1155_id)
    assert 430 == erc20.balanceOf(PLEDGER)
    assert 1 == pwn_deed.balanceOf(LENDER, did_erc20)
    assert 1 == pwn_deed.balanceOf(LENDER, did_erc721)
    assert 1 == pwn_deed.balanceOf(LENDER, did_erc1155)

    # revert: Deed can't accept more offers
    with pytest.raises(exceptions.VirtualMachineError):
        accept_offer(offer_erc721_3, LENDER)


def test_repay_loan():
    PWN_OWNER = get_account(index=0)
    PLEDGER = get_account(index=1)
    LENDER = get_account(index=2)
    RANDOM_USER = get_account(index=3)
    (
        pwn_deed,
        pwn_vault,
        pwn,
        erc20,
        erc721,
        erc721_token_id,
        erc1155,
        erc1155_id,
    ) = base_set_up(PWN_OWNER, PLEDGER, LENDER)
    set_approve(PLEDGER, pwn_vault.address, erc20, ERC20_VAL, amount=100)
    did_erc20 = pwn_create_deed(erc20.address, 0, 3600, 0, 100, PLEDGER)
    set_approve(PLEDGER, pwn_vault.address, erc721, ERC721_VAL, erc721_token_id)
    did_erc721 = pwn_create_deed(erc721.address, 1, 3600, erc721_token_id, 1, PLEDGER)
    set_approve(PLEDGER, pwn_vault.address, erc1155, ERC1155_VAL, erc1155_id)
    did_erc1155 = pwn_create_deed(erc1155.address, 2, 3600, erc1155_id, 3, PLEDGER)

    offer_erc20 = make_offer(erc20.address, 110, did_erc20, 130, LENDER)
    offer_erc721 = make_offer(erc20.address, 110, did_erc721, 130, LENDER)
    offer_erc1155 = make_offer(erc20.address, 110, did_erc1155, 130, LENDER)

    set_approve(PLEDGER, pwn_vault.address, pwn_deed, ERC1155_VAL)
    set_approve(LENDER, pwn_vault.address, erc20, ERC20_VAL, amount=1000)

    # revert: Deed doesn't have an accepted offer to be paid back
    with pytest.raises(exceptions.VirtualMachineError):
        repay_loan(did_erc721, PLEDGER)

    accept_offer(offer_erc20, PLEDGER)
    accept_offer(offer_erc721, PLEDGER)
    accept_offer(offer_erc1155, PLEDGER)

    set_approve(PLEDGER, pwn_vault.address, erc20, ERC20_VAL, amount=390)
    repay_loan(did_erc20, PLEDGER)
    repay_loan(did_erc721, PLEDGER)
    repay_loan(did_erc1155, PLEDGER)

    assert 390 == erc20.balanceOf(pwn_vault)
    assert 0 == erc721.balanceOf(pwn_vault)
    assert 0 == erc1155.balanceOf(pwn_vault, erc1155_id)
    assert 1 == pwn_deed.balanceOf(LENDER, did_erc20)
    assert 1 == pwn_deed.balanceOf(LENDER, did_erc721)
    assert 1 == pwn_deed.balanceOf(LENDER, did_erc1155)

    set_approve(PLEDGER, pwn_vault.address, erc721, ERC721_VAL, erc721_token_id)
    did_erc20_time_out = pwn_create_deed(
        erc721.address, 1, 1, erc721_token_id, 1, PLEDGER
    )
    offer_timeout = make_offer(erc20.address, 110, did_erc20_time_out, 130, LENDER)
    accept_offer(offer_timeout, PLEDGER)
    time.sleep(1)
    # revert: Deed doesn't have an accepted offer to be paid back
    # misleading error code. Deed expired
    with pytest.raises(exceptions.VirtualMachineError):
        repay_loan(did_erc20, PLEDGER)


def test_claim_deed():
    PWN_OWNER = get_account(index=0)
    PLEDGER = get_account(index=1)
    LENDER = get_account(index=2)
    RANDOM_USER = get_account(index=3)
    (
        pwn_deed,
        pwn_vault,
        pwn,
        erc20,
        erc721,
        erc721_token_id,
        erc1155,
        erc1155_id,
    ) = base_set_up(PWN_OWNER, PLEDGER, LENDER)
    set_approve(PLEDGER, pwn_vault.address, erc20, ERC20_VAL, amount=100)
    did_erc20 = pwn_create_deed(erc20.address, 0, 3600, 0, 100, PLEDGER)
    set_approve(PLEDGER, pwn_vault.address, erc721, ERC721_VAL, erc721_token_id)
    did_erc721 = pwn_create_deed(erc721.address, 1, 3600, erc721_token_id, 1, PLEDGER)
    set_approve(PLEDGER, pwn_vault.address, erc1155, ERC1155_VAL, erc1155_id)
    did_erc1155 = pwn_create_deed(erc1155.address, 2, 3600, erc1155_id, 3, PLEDGER)

    offer_erc20 = make_offer(erc20.address, 110, did_erc20, 130, LENDER)
    offer_erc721 = make_offer(erc20.address, 110, did_erc721, 130, LENDER)
    offer_erc1155 = make_offer(erc20.address, 110, did_erc1155, 130, LENDER)

    set_approve(PLEDGER, pwn_vault.address, pwn_deed, ERC1155_VAL)
    set_approve(LENDER, pwn_vault.address, erc20, ERC20_VAL, amount=1000)

    accept_offer(offer_erc20, PLEDGER)
    accept_offer(offer_erc721, PLEDGER)
    accept_offer(offer_erc1155, PLEDGER)

    # revert: Deed can't be claimed yet
    with pytest.raises(exceptions.VirtualMachineError):
        claim_deed(did_erc721, LENDER)

    set_approve(PLEDGER, pwn_vault.address, erc20, ERC20_VAL, amount=390)
    repay_loan(did_erc20, PLEDGER)
    repay_loan(did_erc721, PLEDGER)
    repay_loan(did_erc1155, PLEDGER)

    # revert: Caller is not the deed owner
    with pytest.raises(exceptions.VirtualMachineError):
        claim_deed(did_erc721, RANDOM_USER)
    chain.mine(1)
    claim_deed(did_erc20, LENDER)
    claim_deed(did_erc721, LENDER)
    claim_deed(did_erc1155, LENDER)

    assert 860 == erc20.balanceOf(LENDER)

    set_approve(PLEDGER, pwn_vault.address, erc721, ERC721_VAL, erc721_token_id)
    did_erc721_timeout_after_payment = pwn_create_deed(
        erc721.address, 1, 5, erc721_token_id, 1, PLEDGER
    )
    offer_timeout_after_payment = make_offer(
        erc20.address, 110, did_erc721_timeout_after_payment, 130, LENDER
    )
    accept_offer(offer_timeout_after_payment, PLEDGER)
    set_approve(PLEDGER, pwn_vault.address, erc20, ERC20_VAL, amount=130)
    repay_loan(did_erc721_timeout_after_payment, PLEDGER)
    time.sleep(6)
    # its taking time from the block so claim
    # so claim must be in different block than
    # accept offer
    chain.mine(1)
    assert 3 == pwn_deed.getDeedStatus(did_erc721_timeout_after_payment)

    set_approve(PLEDGER, pwn_vault.address, erc721, ERC721_VAL, erc721_token_id)
    did_erc721_time_out = pwn_create_deed(
        erc721.address, 1, 1, erc721_token_id, 1, PLEDGER
    )
    offer_timeout = make_offer(erc20.address, 110, did_erc721_time_out, 130, LENDER)
    accept_offer(offer_timeout, PLEDGER)
    time.sleep(2)
    # its taking time from the block so claim
    # so claim must be in different block than
    # accept offer
    chain.mine(1)
    assert 4 == pwn_deed.getDeedStatus(did_erc721_time_out)
    claim_deed(did_erc721_time_out, LENDER)
    assert 1 == erc721.balanceOf(LENDER)


def test_lend_ecr1155():
    PWN_OWNER = get_account(index=0)
    PLEDGER = get_account(index=1)
    LENDER = get_account(index=2)

    pwn_deed, pwn_vault, pwn = deploy_pwn(PWN_OWNER)
    set_PWN_ownership(PWN_OWNER)
    erc20, erc721, erc721_token_id, erc1155, erc1155_id = deploy_testing_tokens(
        LENDER, PLEDGER, LENDER
    )

    print(erc20.balanceOf(LENDER))
    print(erc721.balanceOf(PLEDGER))
    print(erc1155.balanceOf(LENDER, erc1155_id))

    send_token(PLEDGER, LENDER, 200, erc20, ERC20_VAL)

    set_approve(PLEDGER, pwn_vault.address, erc721, ERC1155_VAL, erc721_token_id)
    deed_token_id = pwn_create_deed(
        erc721.address, 1, 3600, erc721_token_id, 1, PLEDGER
    )
    print(pwn_deed.balanceOf(PLEDGER, deed_token_id))

    offer_id = make_offer(erc1155.address, 1, deed_token_id, 1, LENDER)
    print(pwn_deed.offers(offer_id))
    set_approve(PLEDGER, pwn_vault.address, pwn_deed, ERC1155_VAL)
    set_approve(LENDER, pwn_vault.address, erc1155, ERC1155_VAL)
    accept_offer(offer_id, PLEDGER)

    assert erc1155.balanceOf(PLEDGER, erc1155_id) == 1
