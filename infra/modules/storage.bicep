@description('Azure region for storage.')
param location string

@description('Globally unique storage account name, 3-24 lowercase letters/numbers.')
param storageAccountName string

@description('Common resource tags.')
param tags object

resource account 'Microsoft.Storage/storageAccounts@2025-01-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  tags: union(tags, {
    component: 'storage'
    riskRole: 'landing-and-uc-storage'
  })
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowCrossTenantReplication: false
    allowSharedKeyAccess: false
    defaultToOAuthAuthentication: true
    dnsEndpointType: 'Standard'
    isHnsEnabled: true
    minimumTlsVersion: 'TLS1_2'
    publicNetworkAccess: 'Enabled'
    supportsHttpsTrafficOnly: true
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2025-01-01' = {
  parent: account
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
    containerDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

resource sampleData 'Microsoft.Storage/storageAccounts/blobServices/containers@2025-01-01' = {
  parent: blobService
  name: 'sample-data'
  properties: {
    publicAccess: 'None'
  }
}

resource unityCatalog 'Microsoft.Storage/storageAccounts/blobServices/containers@2025-01-01' = {
  parent: blobService
  name: 'unity-catalog'
  properties: {
    publicAccess: 'None'
  }
}

output storageAccountName string = account.name
output storageAccountResourceId string = account.id
output sampleDataContainerName string = sampleData.name
output unityCatalogContainerName string = unityCatalog.name
