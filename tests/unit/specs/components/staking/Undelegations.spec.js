import { shallowMount } from "@vue/test-utils"
import Undelegations from "staking/Undelegations"
import validators from "../../store/json/validators.js"

describe(`Undelegations`, () => {
  let wrapper, $store, undelegations
  const getters = {
    address: "cosmos1"
  }

  undelegations = [
    {
      validator: validators[0],
      delegatorAddress: `cosmos1`,
      amount: 10
    },
    {
      validator: validators[1],
      delegatorAddress: `cosmos1`,
      amount: 12
    },
    {
      validator: validators[2],
      delegatorAddress: `cosmos1`,
      amount: 11
    }
  ]

  const state = {
    session: { signedIn: true }
  }

  beforeEach(() => {
    $store = {
      commit: jest.fn(),
      dispatch: jest.fn(),
      state,
      getters
    }

    wrapper = shallowMount(Undelegations, {
      mocks: {
        $store
      }
    })
    wrapper.setData({ undelegations })
  })

  it(`should show unbonding validators`, () => {
    expect(wrapper.element).toMatchSnapshot()
  })
})
