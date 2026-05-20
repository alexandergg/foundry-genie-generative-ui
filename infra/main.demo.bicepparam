using './main.bicep'

param location = 'swedencentral'
param foundryLocation = 'swedencentral'
param workloadName = 'riskgenie'
param environmentName = 'demo'
param deployDatabricksWorkspace = false
param existingDatabricksResourceGroupName = '<existing-databricks-resource-group>'
param existingDatabricksWorkspaceName = '<existing-databricks-workspace-name>'
param databricksSku = 'premium'
param databricksPublicNetworkAccess = 'Enabled'
param foundryPublicNetworkAccess = 'Enabled'
param deployFrontendApp = false
param frontendAgUiAgentUrl = ''
param frontendAppServicePlanSkuName = 'B1'
param frontendAppServicePlanSkuTier = 'Basic'
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
