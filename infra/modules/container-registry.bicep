@description('Azure region for Azure Container Registry.')
param location string

@description('Azure Container Registry name. Must be globally unique, 5-50 lowercase alphanumeric chars.')
param registryName string

@description('Common resource tags.')
param tags object

resource registry 'Microsoft.ContainerRegistry/registries@2025-11-01' = {
  name: registryName
  location: location
  tags: union(tags, {
    component: 'container-registry'
    riskRole: 'hosted-agent-image-registry'
  })
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
    roleAssignmentMode: 'AbacRepositoryPermissions'
    policies: {
      quarantinePolicy: {
        status: 'disabled'
      }
      trustPolicy: {
        type: 'Notary'
        status: 'disabled'
      }
      retentionPolicy: {
        days: 7
        status: 'disabled'
      }
    }
  }
}

output registryName string = registry.name
output registryResourceId string = registry.id
output loginServer string = registry.properties.loginServer
