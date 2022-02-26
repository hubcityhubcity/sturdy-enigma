const dev = process.env.NODE_ENV === `development`
const stargate = process.env.STARGATE || `http://localhost:9070`

export default {
  name: `Lunie`,
  development: dev,
  network: process.env.NETWORK || `cosmos-hub-mainnet`,
  stargate,
  google_analytics_uid: process.env.GOOGLE_ANALYTICS_UID || "",
  node_halted_timeout: 120000,
  block_timeout: 10000,
  default_gas_price: dev ? 1e-9 : 2.5e-8, // Recommended from Cosmos Docs

  // Ledger
  CosmosAppTestModeAllowed: false,
  mobileApp: Boolean(process.env.MOBILE_APP),

  e2e: process.env.VUE_APP_E2E
}
