// SPDX-License-Identifier: GPL-3.0-only

pragma solidity 0.8.3;

import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @dev this is just a dummy mintable/burnable ERC20 for testing purposes
 */
contract ECR1155MyToken is ERC1155, Ownable {
    event TokenCreated(address indexed owner_address, uint256 id);

    constructor(string memory uri) public ERC1155(uri) Ownable() {}

    function mint(
        address account,
        uint256 id,
        uint256 amount,
        bytes memory data
    ) public {
        _mint(account, id, amount, data);
        emit TokenCreated(msg.sender, id);
    }

    function mintBatch(
        address to,
        uint256[] memory ids,
        uint256[] memory amounts,
        bytes memory data
    ) public onlyOwner {
        _mintBatch(to, ids, amounts, data);
    }
}
