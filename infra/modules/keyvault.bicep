@description('Azure region for Key Vault.')
param location string

@description('Key Vault name. Must be globally unique, 3-24 chars, alphanumeric and hyphen.')
param keyVaultName string

@description('Common resource tags.')
param tags object

resource vault 'Microsoft.KeyVault/vaults@2024-11-01' = {
  name: keyVaultName
  location: location
  tags: union(tags, {
    component: 'key-vault'
    riskRole: 'agent-secret-boundary'
  })
  properties: {
    tenantId: tenant().tenantId
    enableRbacAuthorization: true
    enabledForTemplateDeployment: false
    enablePurgeProtection: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
    publicNetworkAccess: 'Enabled'
    sku: {
      family: 'A'
      name: 'standard'
    }
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Allow'
    }
  }
}

output keyVaultName string = vault.name
output keyVaultResourceId string = vault.id
output keyVaultUri string = vault.properties.vaultUri
