const { getNetworkCapabilities } = require('./network-capabilities')
const { coinLookupDictionary } = require('./network-coinlookups')

module.exports = [
  {
    id: 'cosmos-hub-testnet',
    title: 'Gaia Testnet',
    chain_id: 'gaia-13007',
    rpc_url: 'wss://gaia-13007.lunie.io:26657/websocket',
    api_url:
      'http://gaia-13007--lcd--archive.datahub.figment.network/apikey/124a234fb3c6bccf430bfd298bd160ae',
    bech32_prefix: 'cosmos',
    address_prefix: 'cosmos',
    address_creator: 'cosmos',
    ledger_app: 'cosmos',
    network_type: 'cosmos',
    source_class_name: 'source/cosmosV2-source',
    block_listener_class_name: 'block-listeners/cosmos-node-subscription',
    testnet: true,
    ...getNetworkCapabilities[`cosmos-hub-testnet`],
    default: false,
    stakingDenom: 'MUON',
    coinLookup: coinLookupDictionary[`cosmos-hub-testnet`],
    enabled: true,
    experimental: false,
    icon: 'https://lunie.fra1.digitaloceanspaces.com/network-icons/cosmos.png',
    slug: 'cosmos-hub-testnet',
    powered: {
      name: 'Figment',
      picture:
        'https://s3.amazonaws.com/keybase_processed_uploads/bd5fb87f241bd78a9c4bceaaa849ca05_360_360.jpg'
    },
    lockUpPeriod: '3 days'
  },
  {
    id: 'cosmos-hub-mainnet',
    title: 'Cosmos Hub',
    chain_id: 'cosmoshub-3',
    rpc_url: 'wss://cosmos-hub-3.lunie.io/websocket',
    api_url:
      'https://cosmoshub-3--lcd--archive.datahub.figment.network/apikey/7996efcecdc5ef91da3715eb60cd2201',
    bech32_prefix: 'cosmos',
    address_prefix: 'cosmos',
    address_creator: 'cosmos',
    network_type: 'cosmos',
    ledger_app: 'cosmos',
    source_class_name: 'source/cosmosV2-source',
    block_listener_class_name: 'block-listeners/cosmos-node-subscription',
    testnet: false,
    ...getNetworkCapabilities[`cosmos-hub-mainnet`],
    default: true,
    stakingDenom: 'ATOM',
    coinLookup: coinLookupDictionary[`cosmos-hub-mainnet`],
    enabled: true,
    experimental: false,
    icon: 'https://lunie.fra1.digitaloceanspaces.com/network-icons/cosmos.png',
    slug: 'cosmos-hub',
    powered: {
      name: 'Figment',
      providerAddress: 'cosmosvaloper1hjct6q7npsspsg3dgvzk3sdf89spmlpfdn6m9d',
      picture:
        'https://s3.amazonaws.com/keybase_processed_uploads/bd5fb87f241bd78a9c4bceaaa849ca05_360_360.jpg'
    },
    lockUpPeriod: '21 days'
  },
  {
    id: 'terra-mainnet',
    title: 'Terra',
    chain_id: 'columbus-3',
    api_url: 'https://lcd-terra.p2p.org',
    rpc_url: 'ws://rpc-terra.p2p.org/websocket',
    bech32_prefix: 'terra',
    address_prefix: 'terra',
    address_creator: 'cosmos',
    ledger_app: 'cosmos',
    network_type: 'cosmos',
    source_class_name: 'source/terraV3-source',
    block_listener_class_name: 'block-listeners/cosmos-node-subscription',
    testnet: false,
    ...getNetworkCapabilities[`terra-mainnet`],
    default: false,
    stakingDenom: 'LUNA',
    coinLookup: coinLookupDictionary[`terra-mainnet`],
    enabled: true,
    experimental: false,
    icon: 'https://lunie.fra1.digitaloceanspaces.com/network-icons/terra.png',
    slug: 'terra',
    powered: {
      name: 'P2P Validator',
      providerAddress: 'terravaloper144l7c3uph5a7h62xd8u5et3rqvj3dqtvvka2fu',
      picture:
        'https://s3.amazonaws.com/keybase_processed_uploads/0e54d989cbe0b1eed716e222bf2cdd05_360_360.jpg'
    },
    lockUpPeriod: '21 days'
  },
  {
    id: 'terra-testnet',
    title: 'Terra Testnet',
    chain_id: 'soju-0014',
    api_url: 'https://soju-fcd.terra.dev',
    rpc_url: 'wss://terra-testnet.lunie.io/websocket',
    bech32_prefix: 'terra',
    address_prefix: 'terra',
    address_creator: 'cosmos',
    ledger_app: 'cosmos',
    network_type: 'cosmos',
    source_class_name: 'source/terraV3-source',
    block_listener_class_name: 'block-listeners/cosmos-node-subscription',
    testnet: true,
    ...getNetworkCapabilities[`terra-testnet`],
    default: false,
    stakingDenom: 'LUNA',
    coinLookup: coinLookupDictionary[`terra-testnet`],
    enabled: true,
    experimental: false,
    icon: 'https://lunie.fra1.digitaloceanspaces.com/network-icons/terra.png',
    slug: 'terra-testnet',
    lockUpPeriod: '21 days'
  },
  {
    id: 'emoney-mainnet',
    title: 'e-Money',
    chain_id: 'emoney-1',
    api_url: 'https://emoney.validator.network/light',
    rpc_url: 'wss://emoney.validator.network:443/websocket',
    bech32_prefix: 'emoney',
    address_prefix: 'emoney',
    address_creator: 'cosmos',
    ledger_app: 'cosmos',
    network_type: 'cosmos',
    source_class_name: 'source/emoneyV0-source',
    block_listener_class_name: 'block-listeners/cosmos-node-subscription',
    testnet: false,
    ...getNetworkCapabilities[`emoney-mainnet`],
    default: false,
    stakingDenom: 'NGM',
    coinLookup: coinLookupDictionary[`emoney-mainnet`],
    enabled: true,
    experimental: false,
    icon: 'https://lunie.fra1.digitaloceanspaces.com/network-icons/emoney.png',
    slug: 'emoney',
    lockUpPeriod: '21 days'
  },
  // {
  //   id: 'emoney-testnet',
  //   title: 'e-Money Testnet',
  //   chain_id: 'lilmermaid-5',
  //   api_url: 'http://lilmermaid.validator.network/light',
  //   rpc_url: 'wss://lilmermaid.validator.network/websocket',
  //   bech32_prefix: 'emoney',
  //   address_prefix: 'emoney',
  //   address_creator: 'cosmos',
  //   ledger_app: 'cosmos',
  //   network_type: 'cosmos',
  //   source_class_name: 'source/emoneyV0-source',
  //   block_listener_class_name: 'block-listeners/cosmos-node-subscription',
  //   testnet: true,
  //   ...getNetworkCapabilities[`emoney-testnet`],
  //   default: false,
  //   stakingDenom: 'NGM',
  //   coinLookup: coinLookupDictionary[`emoney-testnet`],
  //   enabled: true,
  //   experimental: false,
  //   icon: 'https://lunie.fra1.digitaloceanspaces.com/network-icons/emoney.png',
  //   slug: 'emoney-testnet'
  // },
  {
    id: 'kusama',
    title: 'Kusama',
    chain_id: 'kusama-cc3',
    api_url: 'https://host-01.polkascan.io/kusama/api/v1/',
    rpc_url: process.env.LOCAL_KUSAMA_API,
    public_rpc_url: 'wss://kusama-rpc.polkadot.io/', 
    bech32_prefix: ' ',
    address_prefix: '2', // used in Polkadot as well to generate display addresses (https://wiki.polkadot.network/docs/en/learn-accounts)
    ledger_app: 'polkadot',
    address_creator: 'polkadot',
    network_type: 'polkadot',
    source_class_name: 'source/polkadotV0-source',
    block_listener_class_name: 'block-listeners/polkadot-node-subscription',
    testnet: false,
    ...getNetworkCapabilities[`kusama`],
    default: false,
    stakingDenom: 'KSM',
    // https://wiki.polkadot.network/docs/en/learn-DOT
    coinLookup: coinLookupDictionary[`kusama`],
    enabled: true,
    experimental: true,
    icon:
      'https://lunie.fra1.digitaloceanspaces.com/network-icons/kusama.png',
    slug: 'kusama',
    powered: {
      name: 'stake.fish',
      providerAddress: 'GXaUd6gyCaEoBVzXnkLVGneCF3idnLNtNZs5RHTugb9dCpY',
      picture:
        'https://s3.amazonaws.com/keybase_processed_uploads/e1378cd4d5203ded716906687ad53905_360_360.jpg'
    },
    lockUpPeriod: '7 days'
  },
  {
    id: 'polkadot',
    title: 'Polkadot',
    chain_id: 'polkadot-cc1',
    api_url: 'https://api-01.polkascan.io/polkadot/api/v1/',
    rpc_url: process.env.LOCAL_POLKADOT_API,
    public_rpc_url: 'wss://rpc.polkadot.io',
    bech32_prefix: ' ',
    address_prefix: '0', // used in Polkadot as well to generate display addresses (https://wiki.polkadot.network/docs/en/learn-accounts)
    ledger_app: 'polkadot',
    address_creator: 'polkadot',
    network_type: 'polkadot',
    source_class_name: 'source/polkadotV0-source',
    block_listener_class_name: 'block-listeners/polkadot-node-subscription',
    testnet: false,
    ...getNetworkCapabilities[`polkadot`],
    default: false,
    stakingDenom: 'DOT',
    // https://wiki.polkadot.network/docs/en/learn-DOT
    coinLookup: coinLookupDictionary[`polkadot`],
    enabled: true,
    experimental: true,
    icon: 'https://lunie.fra1.digitaloceanspaces.com/polkadot.png',
    slug: 'polkadot',
    lockUpPeriod: '28 days'
  },
  {
    id: 'westend',
    title: 'Polkadot Testnet',
    chain_id: 'westend',
    api_url: 'https://api-01.polkascan.io/polkadot/api/v1/',
    rpc_url: process.env.LOCAL_WESTEND_API,
    public_rpc_url: 'wss://westend-rpc.polkadot.io',
    bech32_prefix: ' ',
    address_prefix: '42', // used in Polkadot as well to generate display addresses (https://wiki.polkadot.network/docs/en/learn-accounts)
    ledger_app: 'polkadot',
    address_creator: 'polkadot',
    network_type: 'polkadot',
    source_class_name: 'source/polkadotV0-source',
    block_listener_class_name: 'block-listeners/polkadot-node-subscription',
    testnet: true,
    ...getNetworkCapabilities[`westend`],
    default: false,
    stakingDenom: 'WND',
    // https://wiki.polkadot.network/docs/en/learn-DOT
    coinLookup: coinLookupDictionary[`westend`],
    enabled: true,
    experimental: true,
    icon: 'https://lunie.fra1.digitaloceanspaces.com/network-icons/westend.png',
    slug: 'westend',
    lockUpPeriod: '28 days'
  },
  {
    id: 'kava-mainnet',
    title: 'Kava',
    chain_id: 'kava-3',
    api_url: 'http://lcd.kava.forbole.com:1317',
    rpc_url: 'ws://rpc.kava.forbole.com:26657/websocket',
    bech32_prefix: 'kava',
    address_prefix: 'kava',
    address_creator: 'cosmos',
    ledger_app: 'cosmos',
    network_type: 'cosmos',
    source_class_name: 'source/kavaV1-source',
    block_listener_class_name: 'block-listeners/cosmos-node-subscription',
    testnet: false,
    ...getNetworkCapabilities[`kava-mainnet`],
    default: false,
    stakingDenom: 'KAVA',
    coinLookup: coinLookupDictionary[`kava-mainnet`],
    enabled: true,
    experimental: false,
    icon: 'https://lunie.fra1.digitaloceanspaces.com/network-icons/kava.png',
    slug: 'kava',
    powered: {
      name: 'Forbole',
      providerAddress: 'kavavaloper14kn0kk33szpwus9nh8n87fjel8djx0y02c7me3',
      picture:
        'https://lunie.fra1.digitaloceanspaces.com/validator-pictures/forbole.jpeg'
    },
    lockUpPeriod: '21 days'
  },
  {
    id: 'kava-testnet',
    title: 'Kava Testnet',
    chain_id: 'kava-testnet-6000',
    api_url: 'http://lcd.kava-testnet.forbole.com:1317',
    rpc_url: 'ws://rpc.kava-testnet.forbole.com:26657/websocket',
    bech32_prefix: 'kava',
    address_prefix: 'kava',
    address_creator: 'cosmos',
    ledger_app: 'cosmos',
    network_type: 'cosmos',
    source_class_name: 'source/kavaV1-source',
    block_listener_class_name: 'block-listeners/cosmos-node-subscription',
    testnet: true,
    ...getNetworkCapabilities[`kava-testnet`],
    default: false,
    stakingDenom: 'KAVA',
    coinLookup: coinLookupDictionary[`kava-testnet`],
    enabled: true,
    experimental: false,
    icon: 'https://lunie.fra1.digitaloceanspaces.com/network-icons/kava.png',
    slug: 'kava',
    powered: {
      name: 'Forbole',
      providerAddress: 'kavavaloper10tpyfe03nufsax5g038n287yzn9ldyqcgmk2d9',
      picture:
        'https://lunie.fra1.digitaloceanspaces.com/validator-pictures/forbole.jpeg'
    },
    lockUpPeriod: '60 minutes'
  },
  {
    id: 'akash-testnet',
    title: 'Akash Testnet',
    chain_id: 'centauri-2',
    api_url: 'http://akash-lcd.vitwit.com',
    rpc_url: 'ws://akash-rpc.vitwit.com:26657/websocket',
    bech32_prefix: 'akash',
    address_prefix: 'akash',
    address_creator: 'cosmos',
    ledger_app: 'cosmos',
    network_type: 'cosmos',
    source_class_name: 'source/akashV0-source',
    block_listener_class_name: 'block-listeners/cosmos-node-subscription',
    testnet: true,
    ...getNetworkCapabilities[`akash-testnet`],
    default: false,
    stakingDenom: 'AKT',
    coinLookup: coinLookupDictionary[`akash-testnet`],
    enabled: true,
    experimental: false,
    icon: 'https://app.lunie.io/img/networks/akash-testnet.png',
    slug: 'akash-testnet',
    lockUpPeriod: '21 days'
  }
  // {
  //   id: 'livepeer-mainnet',
  //   title: 'Livepeer',
  //   chain_id: 'ethereum-1',
  //   api_url: 'https://livepeer-mainnet.lunie.io/',
  //   rpc_url: 'wss://livepeer-mainnet.lunie.io/websocket',
  //   bech32_prefix: '0x',
  //   address_prefix: '0x',
  //   address_creator: 'ethereum',
  //   ledger_app: 'ethereum',
  //   network_type: 'ethereum',
  //   source_class_name: 'source/livepeerV0-source',
  //   block_listener_class_name: 'block-listeners/livepeer-node-polling',
  //   testnet: false,
  //   feature_session: false,
  //   feature_explore: true,
  //   feature_portfolio: false,
  //   feature_validators: true,
  //   feature_proposals: false,
  //   feature_activity: false,
  //   feature_explorer: false,
  //   action_send: false,
  //   action_claim_rewards: false,
  //   action_delegate: false,
  //   action_redelegate: false,
  //   action_undelegate: false,
  //   action_deposit: false,
  //   action_vote: false,
  //   action_proposal: false,
  //   default: false,
  //   stakingDenom: 'LPT',
  //   enabled: false,
  //   icon: 'https://app.lunie.io/img/networks/livepeer-mainnet.png',
  //   slug: 'livepeer'
  // }
]
