const getConfig = (n: string): string | undefined => {
  return process.env[n]
}

const getConfigRequired = (n: string): string => {
  return getConfig(n) || (() => { throw new Error(`Missing required env var ${n}`) })()
}
