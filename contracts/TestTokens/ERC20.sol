// SPDX-License-Identifier: MIT
pragma solidity 0.8.3;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract ERC20MyToken is ERC20 {
    // wei
    constructor(uint256 initialSupply) ERC20("Fungible Token", "FT") {
        _mint(msg.sender, initialSupply);
    }
}
