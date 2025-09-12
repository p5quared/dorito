enum ENV_VARS {
  SNS_TOPIC_ARN = "SNS_TOPIC_ARN",
  AWS_REGION = "AWS_REGION",
}

const getConfig = (n: string): string | undefined => {
  return process.env[n]
}

export const getConfigRequired = (n: string): string => {
  return getConfig(n) || (() => { throw new Error(`Missing required env var ${n}`) })()
}

export const printMessage = async (message: any) => {
  console.log(JSON.stringify(message, null, 2))
}
