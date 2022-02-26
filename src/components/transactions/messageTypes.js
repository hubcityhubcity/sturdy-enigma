const messageType = {
  SEND: "cosmos-sdk/MsgSend",
  MULTISEND: "cosmos-sdk/MsgMultiSend",
  CREATE_VALIDATOR: "cosmos-sdk/MsgCreateValidator",
  EDIT_VALIDATOR: "cosmos-sdk/MsgEditValidator",
  DELEGATE: "cosmos-sdk/MsgDelegate",
  UNDELEGATE: "cosmos-sdk/MsgUndelegate",
  BEGIN_REDELEGATE: "cosmos-sdk/MsgBeginRedelegate",
  UNJAIL: "cosmos-sdk/MsgUnjail",
  SUBMIT_PROPOSAL: "cosmos-sdk/MsgSubmitProposal",
  DEPOSIT: "cosmos-sdk/MsgDeposit",
  VOTE: "cosmos-sdk/MsgVote",
  SET_WITHDRAW_ADDRESS: "cosmos-sdk/MsgSetWithdrawAddress",
  WITHDRAW_DELEGATION_REWARD: "cosmos-sdk/MsgWithdrawDelegationReward"
}

const transactionGroup = {
  [messageType.SEND]: "banking",
  [messageType.MULTISEND]: "banking",
  [messageType.CREATE_VALIDATOR]: "staking",
  [messageType.EDIT_VALIDATOR]: "staking",
  [messageType.DELEGATE]: "staking",
  [messageType.UNDELEGATE]: "staking",
  [messageType.BEGIN_REDELEGATE]: "staking",
  [messageType.UNJAIL]: "staking",
  [messageType.SUBMIT_PROPOSAL]: "governance",
  [messageType.DEPOSIT]: "governance",
  [messageType.VOTE]: "governance",
  [messageType.SET_WITHDRAW_ADDRESS]: "distribution",
  [messageType.WITHDRAW_DELEGATION_REWARD]: "distribution"
}

export { messageType, transactionGroup }
