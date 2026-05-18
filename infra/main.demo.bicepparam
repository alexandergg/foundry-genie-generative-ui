using './main.bicep'

param location = 'westeurope'
param workloadName = 'uc3genie'
param environmentName = 'demo'
param databricksSku = 'premium'
param databricksPublicNetworkAccess = 'Enabled'
param nameSuffix = ''
param tags = {
  workload: 'risk-exposure-generative-ui'
  environment: 'demo'
  costControl: 'manual-stop-compute'
  demo: 'uc3'
}
