import { shallowMount } from "@vue/test-utils"
import TmSessionWelcome from "common/TmSessionWelcome"

describe(`TmSessionWelcome`, () => {
  let $store, wrapper

  beforeEach(() => {
    const state = {
      session: {
        insecureMode: true,
        browserWithLedgerSupport: null
      }
    }
    $store = {
      commit: jest.fn(),
      dispatch: jest.fn(),
      state
    }
    wrapper = shallowMount(TmSessionWelcome, {
      mocks: {
        $store,
        isMobile: function() {
          return false
        }
      },
      stubs: [`router-link`]
    })
  })

  it(`has the expected html structure`, async () => {
    expect(wrapper.element).toMatchSnapshot()
  })

  it(`has the expected html structure when on mobile`, async () => {
    wrapper = shallowMount(TmSessionWelcome, {
      mocks: {
        $store,
        isMobile: function() {
          return true
        }
      },

      stubs: [`router-link`]
    })
    expect(wrapper.element).toMatchSnapshot()
  })
})
