import {
  listenToExtensionMessages,
  processLunieExtensionMessages,
  getAccountsFromExtension,
  getSignQueue,
  signWithExtension,
  cancelSignWithExtension
} from "scripts/extension-utils.js"

describe(`Extension Utils`, () => {
  describe("listenToExtensionMessages", () => {
    let store

    beforeEach(() => {
      store = {
        commit: jest.fn(),
        dispatch: jest.fn()
      }
    })

    it("listens for extension messages", () => {
      const spy = jest.spyOn(global, "addEventListener")
      listenToExtensionMessages(store)
      expect(spy).toHaveBeenCalledWith("message", expect.any(Function))
    })

    it("should signal that the extension is enabled", () => {
      processLunieExtensionMessages(store)({
        source: global,
        data: {
          type: "FROM_LUNIE_EXTENSION",
          message: {
            type: "INIT_EXTENSION"
          }
        }
      })

      expect(store.commit).toHaveBeenCalledWith("setExtensionAvailable")
      expect(store.dispatch).toHaveBeenCalledWith("getAddressesFromExtension")
    })

    it("should ignore messages not from the extension", () => {
      processLunieExtensionMessages(store)({
        source: global,
        data: {
          type: "NOT_FROM_LUNIE_EXTENSION",
          message: {
            type: "INIT_EXTENSION"
          }
        }
      })

      expect(store.commit).not.toHaveBeenCalledWith("setExtensionAvailable")
    })

    it("should react to query wallet responses", () => {
      processLunieExtensionMessages(store)({
        source: global,
        data: {
          type: "FROM_LUNIE_EXTENSION",
          message: {
            type: "GET_WALLETS_RESPONSE",
            payload: [
              {
                address: "cosmos1234",
                name: "TEST_ADDRESS"
              }
            ]
          }
        }
      })

      expect(store.commit).toHaveBeenCalledWith("setExtensionAccounts", [
        {
          address: "cosmos1234",
          name: "TEST_ADDRESS"
        }
      ])
    })

    it("should do nothing with no message type", () => {
      const result = processLunieExtensionMessages(store)({
        source: global,
        data: {
          type: "FROM_LUNIE_EXTENSION",
          message: {
            type: "IN CORRECT TYPE"
          }
        }
      })

      expect(result).toBeFalsy()
    })
  })

  describe("messages", () => {
    beforeEach(() => {
      jest.spyOn(global, "postMessage")
      global.postMessage.mockClear()
    })
    afterAll(() => {
      global.postMessage.mockReset()
    })

    it("should request wallets", async () => {
      global.postMessage.mockClear()

      getAccountsFromExtension()
      expect(global.postMessage.mock.calls).toEqual([
        [
          {
            payload: { type: "GET_WALLETS" },
            skipResponse: false,
            type: "FROM_LUNIE_IO"
          },
          "*"
        ]
      ])
    })

    it(`should return total amount of transactions in the sign queue in extension`, async () => {
      global.postMessage.mockClear()
      getSignQueue()
      expect(global.postMessage.mock.calls).toEqual([
        [
          {
            payload: {
              payload: {},
              type: "LUNIE_GET_SIGN_QUEUE"
            },
            skipResponse: true,
            type: "FROM_LUNIE_IO"
          },
          "*"
        ]
      ])
    })

    describe("sign", () => {
      beforeEach(() => {
        jest.spyOn(global, "addEventListener")
        global.postMessage.mockClear()
      })

      afterAll(() => {
        global.addEventListener.mockReset()
      })

      it("should cancel requests", () => {
        cancelSignWithExtension("abc", "cosmos1234")
        expect(global.postMessage.mock.calls).toEqual([
          [
            {
              payload: {
                payload: {
                  senderAddress: "abc",
                  network: "cosmos1234"
                },
                type: "LUNIE_SIGN_REQUEST_CANCEL"
              },
              skipResponse: true,
              type: "FROM_LUNIE_IO"
            },
            "*"
          ]
        ])
      })

      it("should request a signature", () => {
        signWithExtension("abc", "cosmos1234")
        expect(global.postMessage.mock.calls).toEqual([
          [
            {
              payload: {
                payload: {
                  senderAddress: "cosmos1234",
                  signMessage: "abc"
                },
                type: "LUNIE_SIGN_REQUEST"
              },
              skipResponse: true,
              type: "FROM_LUNIE_IO"
            },
            "*"
          ]
        ])
      })

      it("should react to signature rejection", () => {
        global.addEventListener.mockImplementationOnce((type, callback) => {
          callback({
            source: global,
            data: {
              message: {
                payload: {
                  rejected: true
                },
                type: "LUNIE_SIGN_REQUEST_RESPONSE"
              },
              type: "FROM_LUNIE_EXTENSION"
            }
          })
        })
        expect(signWithExtension("abc")).rejects.toThrow(
          "User rejected action in extension."
        )
      })

      it("should react to errors in extension", () => {
        global.addEventListener.mockImplementationOnce((type, callback) => {
          callback({
            source: global,
            data: {
              message: {
                payload: {
                  error: "Expected"
                },
                type: "LUNIE_SIGN_REQUEST_RESPONSE"
              },
              type: "FROM_LUNIE_EXTENSION"
            }
          })
        })
        expect(signWithExtension("abc")).rejects.toThrow("Expected")
      })

      it("should react to signature approval", async () => {
        global.addEventListener.mockImplementationOnce((type, callback) => {
          callback({
            source: global,
            data: {
              message: {
                payload: {
                  signature: "abcd",
                  publicKey: "1234"
                },
                type: "LUNIE_SIGN_REQUEST_RESPONSE"
              },
              type: "FROM_LUNIE_EXTENSION"
            }
          })
        })
        const result = await signWithExtension("abc")
        expect(result).toEqual({
          signature: expect.any(Buffer),
          publicKey: expect.any(Buffer)
        })
      })
    })
  })
})
