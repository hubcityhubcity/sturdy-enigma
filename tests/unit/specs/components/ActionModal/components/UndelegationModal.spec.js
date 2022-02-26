"use strict"

import { shallowMount, createLocalVue } from "@vue/test-utils"
import UndelegationModal from "src/ActionModal/components/UndelegationModal"
import Vuelidate from "vuelidate"

describe(`UndelegationModal`, () => {
  let wrapper, $store
  const validator = {
    operatorAddress: `cosmosvaladdr15ky9du8a2wlstz6fpx3p4mqpjyrm5ctplpn3au`
    // we don't need other props in this component
  }
  const localVue = createLocalVue()
  localVue.use(Vuelidate)
  localVue.directive("focus", () => {})

  beforeEach(() => {
    $store = {
      commit: jest.fn(),
      dispatch: jest.fn(),
      getters: {
        network: "testnet",
        address: "cosmos12345"
      }
    }
    wrapper = shallowMount(UndelegationModal, {
      localVue,
      mocks: {
        $store
      },
      propsData: {
        sourceValidator: validator
      }
    })
    wrapper.setData({
      delegations: [
        {
          validator,
          amount: 1000
        }
      ],
      denom: "STAKE"
    })
  })

  it(`should display undelegation modal form`, () => {
    expect(wrapper.element).toMatchSnapshot()
  })

  it(`opens`, () => {
    const $refs = { actionModal: { open: jest.fn() } }
    UndelegationModal.methods.open.call({ $refs })
    expect($refs.actionModal.open).toHaveBeenCalled()
  })

  it(`emits switch to redelegation event`, () => {
    wrapper.vm.$refs = { actionModal: { close: jest.fn() } }
    wrapper.find("#switch-to-redelgation").trigger("click")
    expect(wrapper.vm.$refs.actionModal.close).toHaveBeenCalled()
    expect(wrapper.emitted().switchToRedelegation).toBeTruthy()
  })

  it(`clears on close`, () => {
    const self = {
      $v: { $reset: jest.fn() },
      amount: 10
    }
    UndelegationModal.methods.clear.call(self)
    expect(self.$v.$reset).toHaveBeenCalled()
    expect(self.amount).toBeNull()
  })

  describe(`only submits on correct form`, () => {
    describe(`validates`, () => {
      it(`to false with default values`, () => {
        expect(wrapper.vm.validateForm()).toBe(false)
      })

      it(`to true if the amount is positive and the user has enough liquid atoms`, () => {
        wrapper.setData({ amount: 50 })
        expect(wrapper.vm.validateForm()).toBe(true)
      })
    })
  })

  it(`should submit when enterPressed is called`, async () => {
    const self = {
      $refs: { actionModal: { validateChangeStep: jest.fn() } }
    }
    UndelegationModal.methods.enterPressed.call(self)
    expect(self.$refs.actionModal.validateChangeStep).toHaveBeenCalled()
  })

  describe(`if amount field max button clicked`, () => {
    it(`amount has to match the delegation`, async () => {
      wrapper.vm.setMaxAmount()
      expect(wrapper.vm.amount).toBe(1000)
    })
  })

  describe("Submission Data", () => {
    beforeEach(() => {
      wrapper.setData({
        amount: 10
      })
    })

    it("should return correct transaction data", () => {
      expect(wrapper.vm.transactionData).toEqual({
        type: "MsgUndelegate",
        validatorAddress:
          "cosmosvaladdr15ky9du8a2wlstz6fpx3p4mqpjyrm5ctplpn3au",
        amount: "10000000",
        denom: "stake"
      })
    })

    it("should return correct notification message", () => {
      expect(wrapper.vm.notifyMessage).toEqual({
        title: `Successful undelegation!`,
        body: `You have successfully undelegated 10 STAKEs.`
      })
    })
  })
})
