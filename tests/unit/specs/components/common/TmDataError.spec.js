import { mount } from "@vue/test-utils"
import TmDataError from "common/TmDataError"

jest.mock(`src/../config.js`, () => ({
  mobileApp: true
}))

describe(`TmDataError`, () => {
  let wrapper
  beforeEach(() => {
    wrapper = mount(TmDataError)
  })

  it(`has the expected html structure`, () => {
    expect(wrapper.element).toMatchSnapshot()
  })

  it(`has an icon`, () => {
    expect(
      wrapper
        .find(`.tm-data-msg__icon i.material-icons`)
        .text()
        .trim()
    ).toBe(`sentiment_very_dissatisfied`)
  })

  it(`has a title`, () => {
    expect(
      wrapper
        .find(`.tm-data-msg__title div`)
        .text()
        .trim()
    ).toBe(`Aw shucks!`)
  })

  it(`has a subtitle`, () => {
    expect(
      wrapper
        .find(`.tm-data-msg__subtitle div`)
        .text()
        .trim()
    ).toContain(
      `Even though you're connected a full node, we can't display this data`
    )
  })

  it(`handleIntercom should dispatch displayMessenger action`, () => {
    const $store = { dispatch: jest.fn() }
    const self = {
      $store
    }
    TmDataError.methods.handleIntercom.call(self)
    expect($store.dispatch).toHaveBeenCalledWith(`displayMessenger`)
  })
})
