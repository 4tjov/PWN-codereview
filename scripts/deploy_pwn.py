from glob import escape
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
)


ECR20_VAL = 0
ECR721_VAL = 1
ECR1155_VAL = 2


def deploy_pwn(owner):
    pwn_deed = PWNDeed.deploy("", {"from": owner})
    print("Deployed PWNDeed")

    pwn_vault = PWNVault.deploy({"from": owner})
    print("Deployed PWNVault")

    pwn = PWN.deploy(pwn_deed.address, pwn_vault.address, {"from": owner})
    print("Deployed PWN")

    return pwn_deed, pwn_vault, pwn


def deploy_testing_tokens(ecr20_owner, ecr721_owner, ecr1155_owner):
    ecr20 = ECR20MyToken.deploy(1000, {"from": ecr20_owner})
    print("Deployed ECR20 token")

    ecr721 = ECR721MyToken.deploy("ECR721", {"from": ecr721_owner})
    print("Deployed ECR721 token")
    ecr721_id = ecr721.tx.events["TokenCreated"]["id"]

    ecr1155 = ECR1155MyToken.deploy("ECR1155", {"from": ecr1155_owner})
    tx = ecr1155.mint(ecr1155_owner, 1, 3, 0b10011)
    tx.wait(1)
    ecr1155_id = tx.events["TokenCreated"]["id"]

    return ecr20, ecr721, ecr721_id, ecr1155, ecr1155_id


def set_PWN_ownership(owner):
    pwn_deed, pwn_vault, pwn = PWNDeed[-1], PWNVault[-1], PWN[-1]
    tx = pwn_deed.setPWN(pwn.address, {"from": owner})
    tx = pwn_vault.setPWN(pwn.address, {"from": owner})
    print("Set ownership of PWN")
    tx.wait(1)


def set_approve(
    address_owner,
    address_operator,
    token,
    token_type,
    token_id=None,
    approve_to_all=None,
    amount=None,
):
    if token_type == ECR20_VAL:
        tx = token.approve(address_operator, amount, {"from": address_owner})
    elif token_type == ECR721_VAL:
        if approve_to_all:
            tx = token.setApprovalForAll(address_operator, 1, {"from": address_owner})
        else:
            tx = token.approve(address_operator, token_id, {"from": address_owner})
    elif token_type == ECR1155_VAL:
        tx = token.setApprovalForAll(address_operator, 1, {"from": address_owner})
    else:
        print("Incorrect token_type")

    tx.wait(1)


def send_token(address_to, account_from, amount, token, token_type, token_id=None):
    if token_type == ECR20_VAL:
        tx = token.transfer(address_to, amount, {"from": account_from})
        print(f"sent {amount} ECR20 tokens to {address_to}")
    elif token_type == ECR721_VAL:
        tx = token.transferFrom(account_from, address_to, token_id)
        print(f"sent ECR721 tokens to {address_to}")
    else:
        tx = token.safeTransferFrom(account_from, address_to, token_id, amount, "IDK")

    tx.wait(1)


# enum Category {
#     ERC20,
#     ERC721,
#     ERC1155
# }
def pwn_create_deed(
    collateral_address,
    collateral_type,
    loan_duration,
    collateral_id,
    collateral_amount,
    creator,
):
    pwn = PWN[-1]
    tx = pwn.createDeed(
        collateral_address,
        collateral_type,
        loan_duration,
        collateral_id,
        collateral_amount,
        {"from": creator},
    )
    deed_id = tx.events["DeedCreated"]["did"]
    tx.wait(1)
    return deed_id


def make_offer(asset_addres, amount, deed_id, to_be_paid, offerer):
    pwn = PWN[-1]
    tx = pwn.makeOffer(asset_addres, amount, deed_id, to_be_paid, {"from": offerer})
    offer_id = tx.events["OfferMade"]["offer"]
    tx.wait(1)

    return offer_id


def accept_offer(offer_id, accepter):
    pwn = PWN[-1]
    tx = pwn.acceptOffer(offer_id, {"from": accepter})
    tx.wait(1)


def repay_loan(deed_id, payer):
    pwn = PWN[-1]
    tx = pwn.repayLoan(deed_id, {"from": payer})
    tx.wait(1)


def claim_deed(deed_id, claimer):
    pwn = PWN[-1]
    tx = pwn.claimDeed(deed_id, {"from": claimer})
    tx.wait(1)


def revoke_deed(deed_id, revoker):
    pwn = PWN[-1]
    tx = pwn.revokeDeed(deed_id, {"from": revoker})
    tx.wait(1)


def main():
    PWN_OWNER = get_account(index=0)
    PLEDGER = get_account(index=1)
    LENDER = get_account(index=2)

    pwn_deed, pwn_vault, pwn = deploy_pwn(PWN_OWNER)
    set_PWN_ownership(PWN_OWNER)
    ecr20, ecr721, ecr721_token_id, ecr1155, ecr1155_id = deploy_testing_tokens(
        LENDER, PLEDGER, PLEDGER
    )

    print(ecr20.balanceOf(LENDER))
    print(ecr721.balanceOf(PLEDGER))
    print(ecr1155.balanceOf(PLEDGER, ecr1155_id))

    send_token(PLEDGER, LENDER, 200, ecr20, ECR20_VAL)
    print(ecr20.balanceOf(LENDER))
    print(ecr20.balanceOf(PLEDGER))

    set_approve(PLEDGER, pwn_vault.address, ecr721, ECR721_VAL, ecr721_token_id)
    deed_token_id = pwn_create_deed(
        ecr721.address, 1, 3600, ecr721_token_id, 1, PLEDGER
    )
    print(pwn_deed.balanceOf(PLEDGER, deed_token_id))

    offer_id = make_offer(ecr20.address, 100, deed_token_id, 120, LENDER)
    print(pwn_deed.offers(offer_id))
    set_approve(PLEDGER, pwn_vault.address, pwn_deed, ECR1155_VAL, deed_token_id)
    set_approve(LENDER, pwn_vault.address, ecr20, ECR20_VAL, amount=100)
    accept_offer(offer_id, PLEDGER)
    print(ecr20.balanceOf(PLEDGER))
    print(pwn_deed.balanceOf(LENDER, deed_token_id))

    set_approve(PLEDGER, pwn_vault.address, ecr20, ECR20_VAL, amount=120)
    repay_loan(deed_token_id, PLEDGER)
    print(ecr20.balanceOf(pwn_vault.address))

    claim_deed(deed_token_id, LENDER)
    print(ecr20.balanceOf(PLEDGER))
    print(ecr20.balanceOf(LENDER))
    print(pwn_deed.balanceOf(LENDER, deed_token_id))
