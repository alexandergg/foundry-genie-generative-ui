targetScope = 'resourceGroup'

@description('Azure region for all demo resources.')
param location string = resourceGroup().location

@description('Azure region for the Microsoft Foundry account and project. Keep separate because Foundry model and hosted-agent availability can differ from Databricks availability.')
param foundryLocation string = location

@description('Short workload name used in resource names.')
param workloadName string = 'riskgenie'

@description('Environment name used in tags and names.')
param environmentName string = 'demo'

@description('Deploy a new Azure Databricks workspace. Set to false to reuse an existing workspace and Genie Space.')
param deployDatabricksWorkspace bool = true

@description('Existing Azure Databricks workspace resource group when deployDatabricksWorkspace is false.')
param existingDatabricksResourceGroupName string = ''

@description('Existing Azure Databricks workspace name when deployDatabricksWorkspace is false.')
param existingDatabricksWorkspaceName string = ''

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

@description('Public network access for the Microsoft Foundry AI Services account.')
@allowed([
  'Enabled'
  'Disabled'
])
param foundryPublicNetworkAccess string = 'Enabled'

@description('Deploy the controlled-band (Genie) Next.js frontend. Disabled by default to avoid adding idle cost to local-only demos.')
param deployControlledFrontend bool = false

@description('Deploy the declarative-band (A2UI catalog) Next.js frontend.')
param deployDeclarativeFrontend bool = false

@description('Deploy the open-ended-band (sandboxed UI + MCP Apps) Next.js frontend.')
param deployOpenEndedFrontend bool = false

@description('Foundry Hosted Agent Invocations endpoint for the controlled frontend. Leave empty until the hosted agent exists, then update app settings or redeploy.')
param controlledFrontendAgentUrl string = ''

@description('Foundry Hosted Agent Invocations endpoint for the declarative frontend.')
param declarativeFrontendAgentUrl string = ''

@description('Foundry Hosted Agent Invocations endpoint for the open-ended frontend.')
param openEndedFrontendAgentUrl string = ''

@description('App Service plan SKU name for the shared frontend plan (all deployed bands share one plan).')
param frontendAppServicePlanSkuName string = 'B1'

@description('App Service plan SKU tier matching frontendAppServicePlanSkuName.')
param frontendAppServicePlanSkuTier string = 'Basic'

@description('Container registry SKU. Keep aligned with the live registry to avoid accidental downgrades.')
param containerRegistrySkuName string = 'Basic'

@description('Whether the registry admin user is enabled. Keep aligned with the live registry.')
param containerRegistryAdminUserEnabled bool = false

@description('Whether to deploy the default Foundry model. Disable if capacity or quota is unavailable and use an existing deployment instead.')
param deployFoundryModel bool = true

@description('Foundry model deployment name used by the Genie prompt agent.')
param foundryModelDeploymentName string = 'gpt-5-4'

@description('Foundry model name to deploy.')
param foundryModelName string = 'gpt-5.4'

@description('Foundry model version to deploy. Use the Azure-published model version for the selected model.')
param foundryModelVersion string = '2026-03-05'

@description('Foundry model deployment SKU name.')
param foundryModelSkuName string = 'GlobalStandard'

@description('Foundry model deployment capacity.')
@minValue(1)
param foundryModelCapacity int = 1

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
var applicationInsightsName = 'appi-${safeWorkload}-${environmentName}-${suffix}'
var keyVaultName = take('kv-${safeWorkload}-${environmentName}-${suffix}', 24)
var identityName = 'id-${safeWorkload}-${environmentName}-${suffix}'
var containerRegistryName = take('cr${safeWorkload}${environmentName}${suffix}', 50)
var foundryAccountName = 'aif-${safeWorkload}-${environmentName}-${suffix}'
var foundryProjectName = take('proj-${safeWorkload}-${environmentName}', 64)
var frontendAppServicePlanName = 'asp-${safeWorkload}-${environmentName}-${suffix}'
var controlledWebAppName = take('app-${safeWorkload}-ctrl-${environmentName}-${suffix}', 60)
var declarativeWebAppName = take('app-${safeWorkload}-decl-${environmentName}-${suffix}', 60)
var openEndedWebAppName = take('app-${safeWorkload}-open-${environmentName}-${suffix}', 60)
var deployAnyFrontend = deployControlledFrontend || deployDeclarativeFrontend || deployOpenEndedFrontend
var frontendAlwaysOn = !contains([
  'F1'
  'D1'
], frontendAppServicePlanSkuName)
var existingDatabricksScopeName = empty(existingDatabricksResourceGroupName) ? resourceGroup().name : existingDatabricksResourceGroupName

module analytics './modules/databricks.bicep' = if (deployDatabricksWorkspace) {
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

resource existingDatabricks 'Microsoft.Databricks/workspaces@2026-01-01' existing = if (!deployDatabricksWorkspace) {
  scope: resourceGroup(existingDatabricksScopeName)
  name: existingDatabricksWorkspaceName
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
    applicationInsightsName: applicationInsightsName
    retentionInDays: 30
    tags: tags
  }
}

module identity './modules/identity.bicep' = {
  name: 'risk-agent-identity'
  params: {
    location: location
    identityName: identityName
    tags: tags
  }
}

module keyVault './modules/keyvault.bicep' = {
  name: 'risk-key-vault'
  params: {
    location: location
    keyVaultName: keyVaultName
    tags: tags
  }
}

module containerRegistry './modules/container-registry.bicep' = {
  name: 'risk-container-registry'
  params: {
    location: location
    registryName: containerRegistryName
    skuName: containerRegistrySkuName
    adminUserEnabled: containerRegistryAdminUserEnabled
    tags: tags
  }
}

module foundry './modules/foundry.bicep' = {
  name: 'risk-ai-foundry'
  params: {
    location: foundryLocation
    accountName: foundryAccountName
    projectName: foundryProjectName
    projectDisplayName: 'Risk Exposure Generative UI'
    deployModel: deployFoundryModel
    modelDeploymentName: foundryModelDeploymentName
    modelName: foundryModelName
    modelVersion: foundryModelVersion
    modelSkuName: foundryModelSkuName
    modelCapacity: foundryModelCapacity
    publicNetworkAccess: foundryPublicNetworkAccess
    applicationInsightsResourceId: monitoring.outputs.applicationInsightsResourceId
    applicationInsightsConnectionString: monitoring.outputs.applicationInsightsConnectionString
    tags: tags
  }
}

module frontendPlan './modules/frontend-plan.bicep' = if (deployAnyFrontend) {
  name: 'risk-frontend-plan'
  params: {
    location: location
    appServicePlanName: frontendAppServicePlanName
    appServicePlanSkuName: frontendAppServicePlanSkuName
    appServicePlanSkuTier: frontendAppServicePlanSkuTier
    tags: tags
  }
}

module controlledFrontend './modules/frontend-app.bicep' = if (deployControlledFrontend) {
  name: 'risk-frontend-controlled'
  params: {
    location: location
    appServicePlanId: frontendPlan!.outputs.appServicePlanId
    webAppName: controlledWebAppName
    alwaysOn: frontendAlwaysOn
    appCommandLine: 'node apps/controlled/web/server.js'
    agUiAgentUrl: controlledFrontendAgentUrl
    bandName: 'controlled'
    applicationInsightsConnectionString: monitoring.outputs.applicationInsightsConnectionString
    tags: tags
  }
}

module declarativeFrontend './modules/frontend-app.bicep' = if (deployDeclarativeFrontend) {
  name: 'risk-frontend-declarative'
  params: {
    location: location
    appServicePlanId: frontendPlan!.outputs.appServicePlanId
    webAppName: declarativeWebAppName
    alwaysOn: frontendAlwaysOn
    appCommandLine: 'node apps/declarative/web/server.js'
    agUiAgentUrl: declarativeFrontendAgentUrl
    bandName: 'declarative'
    applicationInsightsConnectionString: monitoring.outputs.applicationInsightsConnectionString
    tags: tags
  }
}

module openEndedFrontend './modules/frontend-app.bicep' = if (deployOpenEndedFrontend) {
  name: 'risk-frontend-open-ended'
  params: {
    location: location
    appServicePlanId: frontendPlan!.outputs.appServicePlanId
    webAppName: openEndedWebAppName
    alwaysOn: frontendAlwaysOn
    appCommandLine: 'node apps/open-ended/web/server.js'
    agUiAgentUrl: openEndedFrontendAgentUrl
    bandName: 'open-ended'
    applicationInsightsConnectionString: monitoring.outputs.applicationInsightsConnectionString
    tags: tags
  }
}

module roleAssignments './modules/role-assignments.bicep' = {
  name: 'risk-agent-role-assignments'
  params: {
    runtimePrincipalId: identity.outputs.principalId
    foundryProjectPrincipalId: foundry.outputs.projectPrincipalId
    frontendPrincipalIds: concat(
      deployControlledFrontend ? [controlledFrontend!.outputs.webAppPrincipalId] : [],
      deployDeclarativeFrontend ? [declarativeFrontend!.outputs.webAppPrincipalId] : [],
      deployOpenEndedFrontend ? [openEndedFrontend!.outputs.webAppPrincipalId] : []
    )
    keyVaultResourceId: keyVault.outputs.keyVaultResourceId
    foundryAccountResourceId: foundry.outputs.accountResourceId
    containerRegistryResourceId: containerRegistry.outputs.registryResourceId
  }
}

output databricksWorkspaceName string = deployDatabricksWorkspace ? analytics!.outputs.workspaceName : existingDatabricks!.name
output databricksWorkspaceResourceId string = deployDatabricksWorkspace ? analytics!.outputs.workspaceResourceId : existingDatabricks!.id
output databricksWorkspaceUrl string = deployDatabricksWorkspace ? analytics!.outputs.workspaceUrl : existingDatabricks!.properties.workspaceUrl
output managedResourceGroupName string = managedResourceGroupName
output storageAccountName string = storage.outputs.storageAccountName
output sampleDataContainerName string = storage.outputs.sampleDataContainerName
output unityCatalogContainerName string = storage.outputs.unityCatalogContainerName
output logAnalyticsWorkspaceName string = monitoring.outputs.workspaceName
output applicationInsightsName string = monitoring.outputs.applicationInsightsName
output applicationInsightsResourceId string = monitoring.outputs.applicationInsightsResourceId
output applicationInsightsConnectionString string = monitoring.outputs.applicationInsightsConnectionString
output keyVaultName string = keyVault.outputs.keyVaultName
output keyVaultUri string = keyVault.outputs.keyVaultUri
output runtimeIdentityName string = identity.outputs.identityName
output runtimeIdentityClientId string = identity.outputs.clientId
output runtimeIdentityResourceId string = identity.outputs.identityResourceId
output containerRegistryName string = containerRegistry.outputs.registryName
output containerRegistryLoginServer string = containerRegistry.outputs.loginServer
output controlledFrontendUrl string = deployControlledFrontend ? 'https://${controlledFrontend!.outputs.webAppDefaultHostName}' : ''
output controlledFrontendWebAppName string = deployControlledFrontend ? controlledFrontend!.outputs.webAppName : ''
output declarativeFrontendUrl string = deployDeclarativeFrontend ? 'https://${declarativeFrontend!.outputs.webAppDefaultHostName}' : ''
output declarativeFrontendWebAppName string = deployDeclarativeFrontend ? declarativeFrontend!.outputs.webAppName : ''
output openEndedFrontendUrl string = deployOpenEndedFrontend ? 'https://${openEndedFrontend!.outputs.webAppDefaultHostName}' : ''
output openEndedFrontendWebAppName string = deployOpenEndedFrontend ? openEndedFrontend!.outputs.webAppName : ''
output foundryAccountName string = foundry.outputs.accountName
output foundryEndpoint string = foundry.outputs.endpoint
output foundryProjectName string = foundry.outputs.projectName
output foundryProjectEndpoint string = foundry.outputs.projectEndpoint
output foundryProjectResourceId string = foundry.outputs.projectResourceId
output foundryProjectPrincipalId string = foundry.outputs.projectPrincipalId
output foundryModelDeploymentName string = foundry.outputs.modelDeploymentName
