@description('Azure region for the Microsoft Foundry account and project.')
param location string

@description('Microsoft Foundry AI Services account name.')
param accountName string

@description('Microsoft Foundry project name.')
param projectName string

@description('Human-readable Microsoft Foundry project display name.')
param projectDisplayName string

@description('Whether to deploy the model into the Foundry AI Services account. Disable if quota/capacity is not available in this region.')
param deployModel bool = true

@description('Foundry model deployment name used by the Genie prompt agent.')
param modelDeploymentName string = 'gpt-5-4'

@description('Model name to deploy.')
param modelName string = 'gpt-5.4'

@description('Model version to deploy. Use the Azure-published model version for the selected model.')
param modelVersion string = '2026-03-05'

@description('Model deployment SKU name.')
param modelSkuName string = 'GlobalStandard'

@description('Model deployment capacity.')
@minValue(1)
param modelCapacity int = 1

@description('Public network access for the Foundry account.')
@allowed([
  'Enabled'
  'Disabled'
])
param publicNetworkAccess string = 'Enabled'

@description('Common resource tags.')
param tags object

resource account 'Microsoft.CognitiveServices/accounts@2025-06-01' = {
  name: accountName
  location: location
  tags: union(tags, {
    component: 'ai-foundry'
    riskRole: 'agent-project-host'
  })
  kind: 'AIServices'
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  properties: {
    allowProjectManagement: true
    customSubDomainName: accountName
    disableLocalAuth: true
    publicNetworkAccess: publicNetworkAccess
    restrictOutboundNetworkAccess: false
  }
}

resource project 'Microsoft.CognitiveServices/accounts/projects@2026-03-01' = {
  parent: account
  name: projectName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  tags: union(tags, {
    component: 'ai-foundry-project'
    riskRole: 'genie-agent-project'
  })
  properties: {
    displayName: projectDisplayName
    description: 'Microsoft Foundry project for the Risk Exposure Generative UI demo, Databricks Genie MCP connection, prompt agent, and hosted AG-UI agent runtime.'
  }
}

resource modelDeployment 'Microsoft.CognitiveServices/accounts/deployments@2025-06-01' = if (deployModel) {
  parent: account
  name: modelDeploymentName
  sku: {
    name: modelSkuName
    capacity: modelCapacity
  }
  properties: {
    model: union({
      format: 'OpenAI'
      name: modelName
    }, empty(modelVersion) ? {} : {
      version: modelVersion
    })
    versionUpgradeOption: 'OnceCurrentVersionExpired'
  }
}

output accountName string = account.name
output accountResourceId string = account.id
output endpoint string = account.properties.endpoint
output projectName string = project.name
output projectResourceId string = project.id
output projectEndpoint string = '${account.properties.endpoint}api/projects/${project.name}'
output projectPrincipalId string = project.identity.principalId
output modelDeploymentName string = deployModel ? modelDeployment.name : modelDeploymentName
