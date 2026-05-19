@description('Principal ID for the user-assigned managed identity used by app/agent runtimes.')
param runtimePrincipalId string

@description('Foundry project system-assigned managed identity principal ID.')
param foundryProjectPrincipalId string

@description('Key Vault resource ID.')
param keyVaultResourceId string

@description('Microsoft Foundry AI Services account resource ID.')
param foundryAccountResourceId string

@description('Azure Container Registry resource ID.')
param containerRegistryResourceId string

var keyVaultSecretsUserRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
var cognitiveServicesOpenAiUserRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '5e0bd9bd-7b93-4f28-af87-19fc36ad61bd')
var cognitiveServicesUserRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'a97b65f3-24c7-4388-baec-2e87135dc908')
var acrRepositoryReaderRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'b93aa761-3e63-49ed-ac28-beffa264f7ac')
var acrRepositoryCatalogListerRoleId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'bfdb9389-c9a5-478a-bb2f-ba9ca092c3c7')

resource keyVault 'Microsoft.KeyVault/vaults@2024-11-01' existing = {
  name: last(split(keyVaultResourceId, '/'))
}

resource foundryAccount 'Microsoft.CognitiveServices/accounts@2025-06-01' existing = {
  name: last(split(foundryAccountResourceId, '/'))
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2025-11-01' existing = {
  name: last(split(containerRegistryResourceId, '/'))
}

resource runtimeKeyVaultSecretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, runtimePrincipalId, 'keyvault-secrets-user')
  scope: keyVault
  properties: {
    principalId: runtimePrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: keyVaultSecretsUserRoleId
  }
}

resource runtimeFoundryOpenAiUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundryAccount.id, runtimePrincipalId, 'foundry-openai-user')
  scope: foundryAccount
  properties: {
    principalId: runtimePrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: cognitiveServicesOpenAiUserRoleId
  }
}

resource runtimeFoundryCognitiveServicesUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(foundryAccount.id, runtimePrincipalId, 'foundry-cognitive-services-user')
  scope: foundryAccount
  properties: {
    principalId: runtimePrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: cognitiveServicesUserRoleId
  }
}

resource runtimeAcrRepositoryReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, runtimePrincipalId, 'acr-repository-reader')
  scope: containerRegistry
  properties: {
    principalId: runtimePrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: acrRepositoryReaderRoleId
  }
}

resource runtimeAcrRepositoryCatalogLister 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, runtimePrincipalId, 'acr-repository-catalog-lister')
  scope: containerRegistry
  properties: {
    principalId: runtimePrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: acrRepositoryCatalogListerRoleId
  }
}

resource foundryProjectAcrRepositoryReader 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(containerRegistry.id, foundryProjectPrincipalId, 'acr-repository-reader')
  scope: containerRegistry
  properties: {
    principalId: foundryProjectPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: acrRepositoryReaderRoleId
  }
}

resource foundryProjectKeyVaultSecretsUser 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVault.id, foundryProjectPrincipalId, 'foundry-project-keyvault-secrets-user')
  scope: keyVault
  properties: {
    principalId: foundryProjectPrincipalId
    principalType: 'ServicePrincipal'
    roleDefinitionId: keyVaultSecretsUserRoleId
  }
}
