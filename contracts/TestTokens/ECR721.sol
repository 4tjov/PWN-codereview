// SPDX-License-Identifier: MIT

pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";

contract ECR721MyToken is ERC721, Ownable {
    uint256 private id;
    string private baseURI;

    constructor(string memory _uri) public ERC721("Nonfungible token", "NT") {
        _mint(msg.sender, id);
        ++id;
    }

    function _baseURI() internal view virtual override returns (string memory) {
        return baseURI;
    }

    function setBaseURI(string memory _baseURI) public onlyOwner {
        baseURI = _baseURI;
    }
}
