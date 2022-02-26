import sessionModule from "src/vuex/modules/session.js"

describe(`Module: Session`, () => {
  let module, state, actions, mutations, node

  beforeEach(() => {
    node = {}
    module = sessionModule({ node })
    state = module.state
    actions = module.actions
    mutations = module.mutations

    state.externals = {
      track: jest.fn(),
      anonymize: jest.fn(),
      deanonymize: jest.fn(),
      config: {
        development: false,
        google_analytics_uid: `UA-123`,
        version: `abcfdef`,
        default_gas_price: 2.5e-8
      }
    }
  })

  it(`should default to signed out state`, () => {
    expect(state.signedIn).toBe(false)
    expect(state.address).toBe(null)
  })

  it("should always default to disable the local signer", () => {
    expect(state.insecureMode).toBe(false)
  })

  describe(`mutations`, () => {
    it(`should set signin`, () => {
      expect(state.signedIn).toBe(false)
      mutations.setSignIn(state, true)
      expect(state.signedIn).toBe(true)
      mutations.setSignIn(state, false)
      expect(state.signedIn).toBe(false)
    })

    it(`should add and remove history correctly`, () => {
      expect(state.history.length).toBe(0)
      mutations.addHistory(state, `/`)
      expect(state.history.length).toBe(1)
      mutations.popHistory(state)
      expect(state.history.length).toBe(0)
    })

    it(`should pauseHistory correctly`, () => {
      expect(state.pauseHistory).toBe(false)
      mutations.pauseHistory(state, true)
      expect(state.pauseHistory).toBe(true)
      mutations.pauseHistory(state, false)
      expect(state.pauseHistory).toBe(false)
    })

    it(`should set the session type`, () => {
      mutations.setSessionType(state, `xxx`)
      expect(state.sessionType).toBe(`xxx`)
    })

    it(`should set user address`, () => {
      mutations.setUserAddress(
        state,
        `cosmos15ky9du8a2wlstz6fpx3p4mqpjyrm5ctpesxxn9`
      )
      expect(state.address).toEqual(
        `cosmos15ky9du8a2wlstz6fpx3p4mqpjyrm5ctpesxxn9`
      )
    })

    it(`should add user address to previously used addresses array`, () => {
      let address = {
        address: `cosmos15ky9du8a2wlstz6fpx3p4mqpjyrm5ctpesxxn9`,
        sessionType: `explore`
      }
      mutations.setUserAddresses(state, address)
      expect(state.addresses).toEqual(address)
    })

    it(`should activate experimental mode`, () => {
      mutations.setExperimentalMode(state)
      expect(state.experimentalMode).toBe(true)
    })

    it(`should activate insecure mode`, () => {
      mutations.setInsecureMode(state, true)
      expect(state.insecureMode).toBe(true)
    })

    it(`should set current modal`, () => {
      expect(state.currrentModalOpen).toBe(false)
      mutations.setCurrrentModalOpen(state, true)
      expect(state.currrentModalOpen).toBe(true)
    })
  })

  it(`should clear all session related data`, () => {
    state.history = [`/x`]
    const commit = jest.fn()
    actions.resetSessionData({ state, commit })

    expect(state.history).toEqual(["/"])
    expect(localStorage.getItem(`session`)).toBeNull()
  })

  describe(`Signs in`, () => {
    it(`with local keystore`, async () => {
      const commit = jest.fn()
      const dispatch = jest.fn()
      const sessionType = `local`
      const address = `cosmos15ky9du8a2wlstz6fpx3p4mqpjyrm5ctpesxxn9`
      await actions.signIn(
        {
          state,
          commit,
          dispatch,
          rootState: {
            connection: { network: "fabo-net" }
          }
        },
        { address, sessionType }
      )
      expect(commit).toHaveBeenCalledWith(
        `setUserAddress`,
        `cosmos15ky9du8a2wlstz6fpx3p4mqpjyrm5ctpesxxn9`
      )
      expect(commit).toHaveBeenCalledWith(`setSessionType`, `local`)
      expect(state.externals.track).toHaveBeenCalledWith(
        `event`,
        `session`,
        `sign-in`,
        `local`
      )
    })

    it(`with Ledger Nano`, async () => {
      const address = `cosmos1qpd4xgtqmxyf9ktjh757nkdfnzpnkamny3cpzv`
      const commit = jest.fn()
      const dispatch = jest.fn()
      await actions.signIn(
        {
          state,
          commit,
          dispatch,
          rootState: {
            connection: { network: "fabo-net" }
          }
        },
        { sessionType: `ledger`, address }
      )
      expect(commit).toHaveBeenCalledWith(`setUserAddress`, address)
      expect(commit).toHaveBeenCalledWith(`setSessionType`, `ledger`)
      expect(state.externals.track).toHaveBeenCalledWith(
        `event`,
        `session`,
        `sign-in`,
        `ledger`
      )
    })

    it(`in explore mode`, async () => {
      const address = `cosmos1qpd4xgtqmxyf9ktjh757nkdfnzpnkamny3cpzv`
      const commit = jest.fn()
      const dispatch = jest.fn()
      await actions.signIn(
        {
          state,
          commit,
          dispatch,
          rootState: {
            connection: { network: "fabo-net" }
          }
        },
        { sessionType: `explore`, address }
      )
      expect(commit).toHaveBeenCalledWith(`setUserAddress`, address)
      expect(commit).toHaveBeenCalledWith(`setSessionType`, `explore`)
      expect(state.externals.track).toHaveBeenCalledWith(
        `event`,
        `session`,
        `sign-in`,
        `explore`
      )
    })

    it("should dispatch required actions", async () => {
      const address = `cosmos1z8mzakma7vnaajysmtkwt4wgjqr2m84tzvyfkz`
      const commit = jest.fn()
      const dispatch = jest.fn()
      state.signedIn = true
      state.addresses = [
        {
          address: `123`,
          type: `explore`
        },
        {
          address: `456`,
          type: `ledger`
        }
      ]
      await actions.signIn(
        {
          state,
          commit,
          dispatch,
          rootState: {
            connection: { network: "fabo-net" }
          }
        },
        { sessionType: `explore`, address }
      )
      expect(dispatch).toHaveBeenCalledWith(`persistAddresses`, {
        addresses: [
          {
            address: `123`,
            type: `explore`
          },
          {
            address: `456`,
            type: `ledger`
          }
        ]
      })
      expect(dispatch).toHaveBeenCalledWith(`persistSession`, {
        address: `cosmos1z8mzakma7vnaajysmtkwt4wgjqr2m84tzvyfkz`,
        sessionType: `explore`,
        networkId: "fabo-net"
      })
      expect(dispatch).toHaveBeenCalledWith(`rememberAddress`, {
        address: `cosmos1z8mzakma7vnaajysmtkwt4wgjqr2m84tzvyfkz`,
        sessionType: `explore`
      })
    })

    it("should commit checkForPersistedAddresses when dispatch checkForPersistedAddresses ", async () => {
      const address = `cosmos1z8mzakma7vnaajysmtkwt4wgjqr2m84tzvyfkz`
      const commit = jest.fn()
      state.signedIn = true
      state.addresses = [
        {
          address: `123`,
          type: `explore`
        }
      ]
      await actions.rememberAddress(
        { state, commit },
        { sessionType: `explore`, address }
      )
      expect(commit).toHaveBeenCalledWith(`setUserAddresses`, [
        {
          address: `123`,
          type: `explore`
        },
        {
          address,
          type: `explore`
        }
      ])
    })

    it("should remember the address", async () => {
      const address = `cosmos1z8mzakma7vnaajysmtkwt4wgjqr2m84tzvyfkz`
      const commit = jest.fn()
      state.signedIn = true
      await actions.rememberAddress(
        { state, commit },
        { sessionType: `explore`, address }
      )
      expect(commit).toHaveBeenCalledWith(`setUserAddresses`, [
        {
          type: `explore`,
          address
        }
      ])
    })
  })

  it(`should sign out`, async () => {
    const commit = jest.fn()
    const dispatch = jest.fn()
    await actions.signOut({ state, commit, dispatch }, "red-feliz")

    expect(dispatch).toHaveBeenCalledWith(`resetSessionData`, "red-feliz")
    expect(commit).toHaveBeenCalledWith(`setSignIn`, false)
    expect(state.externals.track).toHaveBeenCalled()
  })

  it(`should enable error collection`, async () => {
    jest.spyOn(console, `log`).mockImplementationOnce(() => {})
    const commit = jest.fn()
    const dispatch = jest.fn()
    await actions.setErrorCollection(
      {
        state,
        commit,
        dispatch
      },
      true
    )

    expect(state.errorCollection).toBe(true)
  })

  it(`should disable error collection`, async () => {
    jest.spyOn(console, `log`).mockImplementationOnce(() => {})
    const commit = jest.fn()
    const dispatch = jest.fn()
    await actions.setErrorCollection(
      {
        state,
        commit,
        dispatch
      },
      false
    )

    expect(state.errorCollection).toBe(false)
  })

  it(`should disable analytics collection`, async () => {
    jest.spyOn(console, `log`).mockImplementationOnce(() => {})
    const commit = jest.fn()
    const dispatch = jest.fn()
    await actions.setAnalyticsCollection(
      {
        state,
        commit,
        dispatch
      },
      false
    )

    expect(state.analyticsCollection).toBe(false)
    expect(state.externals.anonymize).toHaveBeenCalled()
  })

  it(`should load the persisted user preferences`, () => {
    localStorage.setItem(`lunie_user_preferences`, undefined)
    const dispatch = jest.fn()
    actions.loadLocalPreferences({
      state,
      dispatch
    })
    expect(state.cookiesAccepted).toBe(false)

    localStorage.setItem(
      `lunie_user_preferences`,
      JSON.stringify({
        errorCollection: true,
        analyticsCollection: true
      })
    )
    state.errorCollection = false
    state.analyticsCollection = false

    actions.loadLocalPreferences({
      state,
      dispatch
    })
    expect(state.cookiesAccepted).toBe(true)
    expect(dispatch).toHaveBeenCalledWith(`setErrorCollection`, true)

    localStorage.setItem(
      `lunie_user_preferences`,
      JSON.stringify({
        errorCollection: false,
        analyticsCollection: false
      })
    )
    state.errorCollection = true
    state.analyticsCollection = true

    dispatch.mockClear()
    actions.loadLocalPreferences({
      state,
      dispatch
    })

    expect(dispatch).toHaveBeenCalledWith(`setErrorCollection`, false)
    expect(dispatch).toHaveBeenCalledWith(`setAnalyticsCollection`, false)
  })

  it(`should store the persisted user preferences`, () => {
    localStorage.setItem(`lunie_user_preferences`, ``)
    state.errorCollection = true
    state.analyticsCollection = true

    actions.storeLocalPreferences({
      state
    })

    expect(localStorage.getItem(`lunie_user_preferences`)).toBe(
      `{"errorCollection":true,"analyticsCollection":true}`
    )
  })

  describe(`persistance`, () => {
    it(`persists the session in localstorage`, async () => {
      await actions.persistSession(
        {},
        { address: `xxx`, sessionType: `local`, networkId: "fabo-net" }
      )
      expect(localStorage.getItem(`session_fabo-net`)).toEqual(
        JSON.stringify({
          address: `xxx`,
          sessionType: `local`
        })
      )
    })

    it(`persists the session on sign in`, async () => {
      const dispatch = jest.fn()
      await actions.signIn(
        {
          state,
          commit: jest.fn(),
          dispatch,
          rootState: {
            connection: { network: "fabo-net" }
          }
        },
        {
          address: `cosmos15ky9du8a2wlstz6fpx3p4mqpjyrm5ctpesxxn9`,
          sessionType: `local`
        }
      )
      expect(dispatch).toHaveBeenCalledWith(`persistSession`, {
        address: `cosmos15ky9du8a2wlstz6fpx3p4mqpjyrm5ctpesxxn9`,
        sessionType: `local`,
        networkId: "fabo-net"
      })

      dispatch.mockClear()
      await actions.signIn(
        {
          state,
          commit: jest.fn(),
          dispatch,
          rootState: {
            connection: { network: "fabo-net" }
          }
        },
        {
          address: `cosmos15ky9du8a2wlstz6fpx3p4mqpjyrm5ctpesxxn9`,
          sessionType: `ledger`
        }
      )
      expect(dispatch).toHaveBeenCalledWith(`persistSession`, {
        address: `cosmos15ky9du8a2wlstz6fpx3p4mqpjyrm5ctpesxxn9`,
        sessionType: `ledger`,
        networkId: "fabo-net"
      })
    })

    it(`signs the user in if a session was found`, async () => {
      const dispatch = jest.fn()
      const commit = jest.fn()
      localStorage.setItem(
        `session_fabo-net`,
        JSON.stringify({
          address: `xxx`,
          sessionType: `local`
        })
      )
      await actions.checkForPersistedSession({
        dispatch,
        rootState: {
          connection: { network: "fabo-net" }
        }
      })
      expect(dispatch).toHaveBeenCalledWith(`signIn`, {
        address: `xxx`,
        sessionType: `local`
      })

      dispatch.mockClear()
      localStorage.removeItem(`session_fabo-net`)
      await actions.checkForPersistedSession({
        commit,
        dispatch,
        rootState: {
          connection: { network: "fabo-net" }
        }
      })
      expect(dispatch).not.toHaveBeenCalled()
    })
  })

  it(`signes the user out if no persisted session for the network was found`, async () => {
    const dispatch = jest.fn()
    const commit = jest.fn()
    localStorage.setItem(
      `session_fabo-net`,
      JSON.stringify({
        address: `xxx`,
        sessionType: `local`
      })
    )
    await actions.checkForPersistedSession({
      dispatch,
      commit,
      rootState: {
        connection: { network: "red-feliz" }
      }
    })
    expect(commit).toHaveBeenCalledWith(`setSignIn`, false)
  })

  it("should save used addresses in local storage", async () => {
    state.addresses = [
      {
        address: `123`,
        type: `explore`
      }
    ]
    await actions.persistAddresses({}, { addresses: state.addresses })
    expect(localStorage.getItem(`addresses`)).toEqual(
      JSON.stringify([
        {
          address: `123`,
          type: `explore`
        }
      ])
    )
  })

  it(`should restore previously used addresses from local storage`, async () => {
    const commit = jest.fn()
    localStorage.setItem(
      `addresses`,
      JSON.stringify([
        {
          address: `xxx`,
          type: `explore`
        },
        {
          address: `yyy`,
          type: `ledger`
        }
      ])
    )
    await actions.checkForPersistedAddresses({ commit })
    expect(commit).toHaveBeenCalledWith(`setUserAddresses`, [
      {
        address: `xxx`,
        type: `explore`
      },
      {
        address: `yyy`,
        type: `ledger`
      }
    ])
  })
})
