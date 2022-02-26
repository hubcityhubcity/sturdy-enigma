import { percent } from "../scripts/num"
import moment from "moment"

export const date = date => moment(date).format("MMMM Do YYYY, HH:mm")

export const fromNow = date => moment(date).fromNow()

export const noBlanks = function(value) {
  return value === undefined ||
    value === null ||
    value === `` ||
    value === `[do-not-modify]`
    ? `--`
    : value
}

export const percentOrPending = function(value, totalValue, pending) {
  return pending ? `--` : percent(totalValue === 0 ? 0 : value / totalValue)
}

export const formatBech32 = (address, longForm = false, length = 4) => {
  if (!address) {
    return `Address Not Found`
  } else if (address.indexOf(`1`) === -1) {
    return `Not A Valid Bech32 Address`
  } else if (longForm) {
    return address
  } else {
    return address.split(`1`)[0] + `…` + address.slice(-1 * length)
  }
}

export const resolveValidatorName = (address, validators) => {
  if (validators[address]) {
    return validators[address].name
  }
  return formatBech32(address)
}
