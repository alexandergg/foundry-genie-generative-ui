targetScope = 'resourceGroup'

@description('Azure region for all demo resources.')
param location string = resourceGroup().location

@description('Short workload name used in resource names.')
param workloadName string = 'riskgenie'

@description('Environment name used in tags and names.')
param environmentName string = 'demo'

@description('Azure Databricks workspace SKU. Genie/Unity Catalog demo should use premium.')
@allowed([
  'premium'
  'standard'
  'trial'
])
param databricksSku string = 'premium'

@description('Enable public network access for the demo workspace. Keep enabled for simplest demo setup.')
@allowed([
  'Enabled'
  'Disabled'
])
param databricksPublicNetworkAccess string = 'Enabled'

@description('Optional suffix override. Leave empty to use a deterministic unique suffix.')
param nameSuffix string = ''

@description('Common resource tags.')
param tags object = {
  workload: 'risk-exposure-generative-ui'
  environment: 'demo'
  costControl: 'manual-stop-compute'
  owner: 'copilot-prepared'
}

var suffix = empty(nameSuffix) ? take(uniqueString(subscription().id, resourceGroup().id, workloadName, environmentName), 8) : toLower(nameSuffix)
var safeWorkload = toLower(replace(workloadName, '-', ''))
var workspaceName = 'dbw-${safeWorkload}-${environmentName}-${suffix}'
var managedResourceGroupName = 'rg-${workspaceName}-managed'
var storageAccountName = take('st${safeWorkload}${environmentName}${suffix}', 24)
var logAnalyticsName = 'log-${safeWorkload}-${environmentName}-${suffix}'

module analytics './modules/databricks.bicep' = {
  name: 'databricks-workspace'
  params: {
    location: location
    workspaceName: workspaceName
    managedResourceGroupName: managedResourceGroupName
    skuName: databricksSku
    publicNetworkAccess: databricksPublicNetworkAccess
    tags: tags
  }
}

module storage './modules/storage.bicep' = {
  name: 'risk-storage'
  params: {
    location: location
    storageAccountName: storageAccountName
    tags: tags
  }
}

module monitoring './modules/monitoring.bicep' = {
  name: 'risk-monitoring'
  params: {
    location: location
    workspaceName: logAnalyticsName
    retentionInDays: 30
    tags: tags
  }
}

output databricksWorkspaceName string = analytics.outputs.workspaceName
output databricksWorkspaceResourceId string = analytics.outputs.workspaceResourceId
output databricksWorkspaceUrl string = analytics.outputs.workspaceUrl
output managedResourceGroupName string = managedResourceGroupName
output storageAccountName string = storage.outputs.storageAccountName
output sampleDataContainerName string = storage.outputs.sampleDataContainerName
output unityCatalogContainerName string = storage.outputs.unityCatalogContainerName
output logAnalyticsWorkspaceName string = monitoring.outputs.workspaceName
