// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract FaceVerification {

    struct FaceRecord {
        string faceHash;
        bool verified;
        uint256 timestamp;
    }

    mapping(address => FaceRecord) private records;

    function registerFace(string memory _faceHash) public {
        records[msg.sender] = FaceRecord(
            _faceHash,
            true,
            block.timestamp
        );
    }

    function verifyFace(address _user)
        public
        view
        returns (string memory, bool, uint256)
    {
        FaceRecord memory record = records[_user];

        return (
            record.faceHash,
            record.verified,
            record.timestamp
        );
    }
}
