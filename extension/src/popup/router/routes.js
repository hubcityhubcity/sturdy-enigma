export default (store) => {
  return [
    {
      path: `/`,
      name: `accounts`,
      component: require('../../components/SessionAccounts').default,
      alias: '/accounts',
      beforeEnter: (to, from, next) => {
        if (!store.state.accounts.length) {
          next({ path: '/welcome', replace: true })
        } else {
          next()
        }
      }
    },
    {
      path: '/welcome',
      name: 'welcome',
      component: require('../../components/SessionWelcome').default
    },
    {
      path: '/success',
      name: 'success',
      component: require('../../components/SessionSuccess').default
    },
    {
      path: '/existing',
      name: 'existing',
      component: require('common/CardSignInRequired').default
    },
    {
      path: `/create`,
      name: `create`,
      component: require('common/TmSessionSignUp').default
    },
    {
      path: `/create/password`,
      name: `create-password`,
      component: require('common/TmSessionSignUpPassword').default
    },
    {
      path: `/create/confirm`,
      name: `create-confirm`,
      component: require('common/TmSessionSignUpSeed').default
    },
    {
      path: `/recover`,
      name: `recover`,
      component: require('common/TmSessionImport').default
    },
    {
      path: `/reveal/:address`,
      name: `reveal`,
      component: require('account/RevealSeedModal').default
    },
    {
      path: `/select-network`,
      name: `select-network`,
      component: require('common/TmSelectNetwork').default
    },
    {
      path: `/select-network/recover`,
      name: `select-network-recover`,
      component: require('common/TmSelectNetwork').default
    },
    {
      path: `/select-network/create`,
      name: `select-network-create`,
      component: require('common/TmSelectNetwork').default
    },
    {
      path: `/recover/name`,
      name: `recover-name`,
      component: require('common/TmSessionImportName').default
    },
    {
      path: `/recover/password`,
      name: `recover-password`,
      component: require('common/TmSessionImportPassword').default
    },
    {
      path: `/approve`,
      name: `approve`,
      component: require('../../components/SessionApprove').default,
      beforeEnter: (to, from, next) => {
        if (!store.state.signRequest) {
          next({ path: '/accounts' })
        } else {
          next()
        }
      }
    }
  ]
}
