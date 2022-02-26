let Node

describe(`Connector`, () => {
  const remoteLcdURL = `http://awesomenode.de:12345`

  beforeAll(() => {
    jest.mock(`src/connectors/tendermint`, () => () => ({
      fooRpc: `rpcBar`
    }))
    jest.mock(
      `@lunie/cosmos-api`,
      () =>
        class mockAPI {
          constructor() {
            this.get = {}
          }
        }
    )

    Node = require(`src/connectors/node`).default
  })

  it(`should setup the connectors`, () => {
    const node = new Node(remoteLcdURL)
    expect(node.tendermint.fooRpc).toBe(`rpcBar`)
    expect(node.get).toBeDefined()
  })
})
