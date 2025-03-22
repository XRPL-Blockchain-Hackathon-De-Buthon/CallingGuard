// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract VoicePhishingBlocker {
    address public owner;

    struct Caller {
        string name;
        string organization;
        bool isVerified;
    }

    struct OTP {
        string code;
        uint256 expiresAt;
    }

    mapping(address => Caller) public verifiedCallers;
    mapping(address => OTP) public otpRecords;
    mapping(address => bool) public blacklist;

    event CallerRegistered(address indexed caller, string name, string organization);
    event OTPGenerated(address indexed caller, string code);
    event OTPVerified(address indexed caller);
    event Blacklisted(address indexed caller);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only the contract owner can perform this action.");
        _;
    }

    modifier onlyVerifiedCaller() {
        require(verifiedCallers[msg.sender].isVerified, "Caller is not verified.");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    // 신뢰할 수 있는 발신자 등록 (관리자 전용)
    function registerCaller(address _caller, string memory _name, string memory _organization) public onlyOwner {
        verifiedCallers[_caller] = Caller(_name, _organization, true);
        emit CallerRegistered(_caller, _name, _organization);
    }

    // 블랙리스트 등록
    function addToBlacklist(address _caller) public onlyOwner {
        blacklist[_caller] = true;
        emit Blacklisted(_caller);
    }

    // 외부에서 OTP 설정 (FastAPI 서버에서 생성 후 등록)
    function setOTP(address _caller, string memory _otp, uint256 _expiresAt) public onlyOwner {
        otpRecords[_caller] = OTP(_otp, _expiresAt);
        emit OTPGenerated(_caller, _otp);
    }

    // OTP 검증 (수신자 쪽에서 호출)
    function verifyOTP(address _caller, string memory _otp) public view returns (bool) {
        OTP memory record = otpRecords[_caller];
        if (
            verifiedCallers[_caller].isVerified &&
            block.timestamp <= record.expiresAt &&
            keccak256(abi.encodePacked(record.code)) == keccak256(abi.encodePacked(_otp))
        ) {
            return true;
        }
        return false;
    }

    // 발신자 정보 조회 (등록 여부 제한 없음)
    function getCallerInfo(address _caller) public view returns (string memory, string memory, bool) {
        Caller memory caller = verifiedCallers[_caller];
        return (caller.name, caller.organization, caller.isVerified && !blacklist[_caller]);
    }

    // 등록 여부 확인
    function isCallerRegistered(address _caller) public view returns (bool) {
        return verifiedCallers[_caller].isVerified;
    }

    // 블랙리스트 여부 확인
    function isBlacklisted(address _caller) public view returns (bool) {
        return blacklist[_caller];
    }
}
