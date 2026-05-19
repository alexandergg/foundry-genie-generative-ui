using './main.bicep'

param location = 'westeurope'
param workloadName = 'riskgenie'
param environmentName = 'demo'
param databricksSku = 'premium'
param databricksPublicNetworkAccess = 'Enabled'
param nameSuffix = ''
param tags = {
  workload: 'risk-exposure-generative-ui'
  environment: 'demo'
  costControl: 'manual-stop-compute'
  demo: 'risk'
}
