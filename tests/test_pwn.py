from scripts.helpful_scripts import get_account
from brownie import (
    PWN,
    PWNDeed,
    PWNVault,
    network,
    config,
    ECR20MyToken,
    ECR721MyToken,
    ECR1155MyToken,
    accounts,
    exceptions,
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
    ECR1155_VAL,
    ECR721_VAL,
    ECR20_VAL,
)
import pytest


def base_set_up(PWN_OWNER, PLEDGER, LENDER):

    pwn_deed, pwn_vault, pwn = deploy_pwn(PWN_OWNER)
    set_PWN_ownership(PWN_OWNER)
    ecr20, ecr721, ecr721_token_id, ecr1155, ecr1155_id = deploy_testing_tokens(
        LENDER, PLEDGER, PLEDGER
    )

    send_token(PLEDGER, LENDER, 200, ecr20, ECR20_VAL)
    return pwn_deed, pwn_vault, pwn, ecr20, ecr721, ecr721_token_id, ecr1155, ecr1155_id


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
        ecr20,
        ecr721,
        ecr721_token_id,
        ecr1155,
        ecr1155_id,
    ) = base_set_up(PWN_OWNER, PLEDGER, LENDER)

    with pytest.raises(exceptions.VirtualMachineError):
        deed_token_id = pwn_create_deed(
            ecr721.address, 1, 3600, ecr721_token_id, 1, PLEDGER
        )
    set_approve(PLEDGER, pwn_vault.address, ecr721, ECR721_VAL, ecr721_token_id)
    deed_token_id = pwn_create_deed(
        ecr721.address, 1, 3600, ecr721_token_id, 1, PLEDGER
    )
    assert (
        1,
        "0x0000000000000000000000000000000000000000",
        3600,
        0,
        (ecr721.address, 1, 1, 0),
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
        deed_token_id = pwn_create_deed(ecr20.address, 0, 3600, 0, 50, PLEDGER)
    with pytest.raises(exceptions.VirtualMachineError):
        deed_token_id = pwn_create_deed(
            ecr1155.address, 2, 3600, ecr1155_id, 2, PLEDGER
        )
    set_approve(PLEDGER, pwn_vault.address, ecr20, ECR20_VAL, amount=50)
    set_approve(PLEDGER, pwn_vault.address, ecr1155, ECR1155_VAL, ecr1155_id)
    did_ecr20 = pwn_create_deed(ecr20.address, 0, 3600, 0, 50, PLEDGER)
    did_ecr1155 = pwn_create_deed(ecr1155.address, 2, 3600, ecr1155_id, 2, PLEDGER)
    assert pwn_deed.deeds(did_ecr20) == (
        1,
        "0x0000000000000000000000000000000000000000",
        3600,
        0,
        (ecr20.address, 0, 50, 0),
        "0x0000000000000000000000000000000000000000000000000000000000000000",
    )
    assert pwn_deed.deeds(did_ecr1155) == (
        1,
        "0x0000000000000000000000000000000000000000",
        3600,
        0,
        (ecr1155.address, 2, 2, 1),
        "0x0000000000000000000000000000000000000000000000000000000000000000",
    )
    assert ecr20.balanceOf(pwn_vault) == 50
    assert ecr20.balanceOf(PLEDGER) == 150

    assert ecr721.balanceOf(pwn_vault) == 1
    assert ecr721.balanceOf(PLEDGER) == 0

    assert ecr1155.balanceOf(pwn_vault, ecr1155_id) == 2
    assert ecr1155.balanceOf(PLEDGER, ecr1155_id) == 1

    set_approve(PLEDGER, pwn_vault.address, ecr20, ECR20_VAL, amount=50)
    with pytest.raises(OverflowError):
        did_ecr20 = pwn_create_deed(ecr20.address, 0, -10, 0, 50, PLEDGER)


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
        ecr20,
        ecr721,
        ecr721_token_id,
        ecr1155,
        ecr1155_id,
    ) = base_set_up(PWN_OWNER, PLEDGER_1, LENDER)
    set_approve(PLEDGER_1, pwn_vault.address, ecr721, ECR721_VAL, ecr721_token_id)
    did_1 = pwn_create_deed(ecr721.address, 1, 3600, ecr721_token_id, 1, PLEDGER_1)
    send_token(PLEDGER_2, LENDER, 100, ecr20, ECR20_VAL)
    set_approve(PLEDGER_2, pwn_vault.address, ecr20, ECR20_VAL, amount=100)
    did_2 = pwn_create_deed(ecr20.address, 0, 3600, 0, 100, PLEDGER_2)
    set_approve(PLEDGER_1, pwn_vault.address, ecr1155, ECR1155_VAL, ecr1155_id)
    did_3 = pwn_create_deed(ecr1155.address, 2, 3600, ecr1155_id, 3, PLEDGER_1)

    with pytest.raises(exceptions.VirtualMachineError):
        revoke_deed(did_1, RANDOM_USER)

    with pytest.raises(exceptions.VirtualMachineError):
        revoke_deed(did_1, PLEDGER_2)

    revoke_deed(did_1, PLEDGER_1)
    assert 0 == pwn_deed.getDeedStatus(did_1)

    assert pwn_deed.balanceOf(PLEDGER_1, did_1) == 0
    assert ecr721.balanceOf(PLEDGER_1) == 1

    revoke_deed(did_2, PLEDGER_2)
    assert pwn_deed.balanceOf(PLEDGER_2, did_2) == 0
    assert ecr20.balanceOf(PLEDGER_2) == 100

    print(pwn_deed.deeds(did_3))

    revoke_deed(did_3, PLEDGER_1)
    assert pwn_deed.balanceOf(PLEDGER_1, did_3) == 0
    assert ecr1155.balanceOf(PLEDGER_1, ecr1155_id) == 3

    set_approve(PLEDGER_1, pwn_vault.address, ecr721, ECR721_VAL, ecr721_token_id)
    did_4 = pwn_create_deed(ecr721.address, 1, 3600, ecr721_token_id, 1, PLEDGER_1)
    offer_id = make_offer(ecr20.address, 100, did_4, 120, LENDER)
    set_approve(PLEDGER_1, pwn_vault.address, pwn_deed, ECR1155_VAL, PLEDGER_1)
    set_approve(LENDER, pwn_vault.address, ecr20, ECR20_VAL, amount=100)
    accept_offer(offer_id, PLEDGER_1)

    with pytest.raises(exceptions.VirtualMachineError):
        revoke_deed(did_4, LENDER)


def test_make_offer():