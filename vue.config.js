const path = require(`path`)
const webpack = require(`webpack`)
const CSPWebpackPlugin = require(`csp-webpack-plugin`)
const { version } = require("./package.json")

function resolve(dir) {
  return path.join(__dirname, dir)
}

module.exports = {
  publicPath: `/`,
  chainWebpack: config => {
    config.plugins.delete(`prefetch`)
  },
  configureWebpack: () => {
    const config = {
      resolve: {
        alias: {
          src: resolve(`src`),
          "@": resolve(`src`),
          assets: resolve(`src/assets`),
          scripts: resolve(`src/scripts`),
          common: resolve(`src/components/common`),
          governance: resolve(`src/components/governance`),
          network: resolve(`src/components/network`),
          staking: resolve(`src/components/staking`),
          transactions: resolve(`src/components/transactions`),
          wallet: resolve(`src/components/wallet`),
          test: resolve(`test`)
        },
        extensions: [`.js`, `.vue`, `.css`]
      },
      plugins: [
        new webpack.IgnorePlugin(/^\.\/locale$/, /moment$/),
        new webpack.DefinePlugin({
          "process.env": {
            NODE_ENV: JSON.stringify(process.env.NODE_ENV),
            NETWORK: JSON.stringify(process.env.NETWORK),
            SENTRY_DSN: JSON.stringify(process.env.SENTRY_DSN),
            LUNIE_VERSION: JSON.stringify(version),
            GOOGLE_ANALYTICS_UID: JSON.stringify(
              process.env.GOOGLE_ANALYTICS_UID
            ),
            MOBILE_APP: JSON.stringify(process.env.MOBILE_APP)
          }
        })
      ],
      optimization: {
        splitChunks: {
          chunks: "all"
        }
      }
    }

    if (process.env.NODE_ENV === `production` && !process.env.E2E_TESTS) {
      config.plugins.push(
        // adds the content security policy to the index.html
        new CSPWebpackPlugin({
          "object-src": `'none'`,
          "base-uri": `'self'`,
          "default-src": `'self'`,
          "script-src": [`'self'`, `https://*.lunie.io`],
          "worker-src": `'none'`,
          "style-src": [`'self'`, `'unsafe-inline'`],
          "connect-src": [
            // third party tools
            `https://api-iam.intercom.io`,
            // mainnet
            `https://lcd.nylira.net`,
            `https://gaia-13006.lunie.io`
          ],
          "frame-src": [`'self'`, `https://api-iam.intercom.io`],
          "img-src": [`'self'`, `https://www.google-analytics.com/`]
        })
      )
    }

    return config
  },

  pluginOptions: {
    lintStyleOnBuild: false,
    stylelint: {}
  }
}
