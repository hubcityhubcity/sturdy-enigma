import delegatesModule from "src/vuex/modules/delegates.js"
const mockValues = require(`tests/unit/helpers/mockValues.js`)
import BN from "bignumber.js"

const mockRootState = {
  connection: {
    connected: true
  }
}

describe(`Module: Delegates`, () => {
  let instance
  let node

  beforeEach(() => {
    node = {
      get: {}
    }
    instance = delegatesModule({
      node
    })
  })

  it(`sets the loading state`, () => {
    const { mutations, state } = instance
    expect(state.loading).toBe(false)
    mutations.setDelegateLoading(state, true)
    expect(state.loading).toBe(true)
  })

  it(`adds delegate to state`, () => {
    const { mutations, state } = instance
    mutations.setDelegates(state, [
      {
        operator_address: `foo`,
        percent_of_vote: `100.00%`,
        tokens: `10`
      }
    ])
    expect(state.delegates).toEqual([
      {
        operator_address: `foo`,
        percent_of_vote: `100.00%`,
        tokens: `10`
      }
    ])
  })

  it(`replaces existing delegate with same id`, () => {
    const { mutations, state } = instance
    mutations.setDelegates(state, [
      {
        operator_address: `foo`,
        tokens: `12`,
        updated: true
      }
    ])
    expect(state.delegates).toEqual([
      {
        operator_address: `foo`,
        tokens: `12`,
        updated: true
      }
    ])
  })

  it(`fetches all candidates`, async () => {
    node.get.validators = () => []
    const { actions, state } = instance
    const commit = jest.fn()
    const dispatch = jest.fn()
    const candidates = await actions.getDelegates({
      state,
      commit,
      dispatch,
      rootState: mockRootState
    })
    expect(commit.mock.calls).toEqual([
      [`setDelegateLoading`, true],
      [`setDelegates`, candidates],
      [`setDelegateLoading`, false]
    ])
  })

  it(`keeps the loading state if loading failed`, async () => {
    const { actions, state } = instance
    const commit = jest.fn()
    const dispatch = jest.fn()
    node.get.validators = () => Promise.reject(new Error(`Expected`))
    await actions.getDelegates({
      state,
      commit,
      dispatch,
      rootState: mockRootState
    })
    expect(commit.mock.calls).toEqual([
      [`setDelegateLoading`, true],
      [
        `notifyError`,
        {
          body: `Expected`,
          title: `Error fetching validators`
        }
      ]
    ])
  })

  it(`should query for delegates on reconnection if was loading before`, async () => {
    const { actions } = delegatesModule({})
    const instance = {
      state: {
        loading: true
      },
      dispatch: jest.fn()
    }
    await actions.reconnected(instance)
    expect(instance.dispatch).toHaveBeenCalledWith(`getDelegates`)
  })

  it(`should not query for delegates on reconnection if not stuck in loading`, async () => {
    const { actions } = delegatesModule({})
    const instance = {
      state: {
        loading: false
      },
      dispatch: jest.fn()
    }
    await actions.reconnected(instance)
    expect(instance.dispatch).not.toHaveBeenCalledWith(`getDelegates`)
  })

  it(`should query self bond of a validator`, async () => {
    const { actions, state } = instance
    const commit = jest.fn()
    const validator = {
      operator_address: mockValues.validators[0],
      delegator_shares: `120`
    }
    node.get.delegations = jest.fn(() => [
      { shares: `12`, validator_address: mockValues.validators[0] }
    ])

    await actions.getSelfBond({ commit, state }, validator)
    expect(commit).toHaveBeenCalledWith(`setSelfBond`, {
      validator,
      ratio: BN(0.1)
    })
  })

  it(`should not query self bond of a validator if already queried`, async () => {
    const { actions, state } = instance
    const commit = jest.fn()
    const validator = {
      operator_address: mockValues.validators[0],
      delegator_shares: `120`
    }
    state.selfBond[mockValues.validators[0]] = `0.1`
    node.get.delegation = jest.fn(() => [])

    await actions.getSelfBond({ commit, state }, validator)
    expect(node.get.delegation).not.toHaveBeenCalled()
  })

  it(`should set self bond of a validator`, async () => {
    const { state, mutations } = instance
    const validator = {
      operator_address: mockValues.validators[0],
      delegator_shares: `120`
    }

    await mutations.setSelfBond(state, {
      validator,
      ratio: BN(0.1)
    })
    expect(state.selfBond[mockValues.validators[0]]).toEqual(BN(0.1))
  })

  it(`should store an error if failed to load delegates`, async () => {
    const { actions, state } = instance
    node.get.validators = async () => Promise.reject(`Error`)
    await actions.getDelegates({
      commit: jest.fn(),
      dispatch: jest.fn(),
      state,
      rootState: mockRootState
    })
    expect(state.error).toBe(`Error`)
  })
})
