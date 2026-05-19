using './main.bicep'

param location = 'swedencentral'
param foundryLocation = 'swedencentral'
param workloadName = 'riskgenie'
param environmentName = 'demo'
param deployDatabricksWorkspace = false
param existingDatabricksResourceGroupName = 'rg-uc3-databricks-genie-poc'
param existingDatabricksWorkspaceName = 'dbw-uc3genie-poc-hmpwknyf'
param databricksSku = 'premium'
param databricksPublicNetworkAccess = 'Enabled'
param foundryPublicNetworkAccess = 'Enabled'
param deployFoundryModel = true
param foundryModelDeploymentName = 'gpt-5-4'
param foundryModelName = 'gpt-5.4'
param foundryModelVersion = '2026-03-05'
param foundryModelSkuName = 'GlobalStandard'
param foundryModelCapacity = 1
param nameSuffix = ''
param tags = {
  workload: 'risk-exposure-generative-ui'
  environment: 'demo'
  costControl: 'manual-stop-compute'
  demo: 'risk'
}
