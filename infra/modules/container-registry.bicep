@description('Azure region for Azure Container Registry.')
param location string

@description('Azure Container Registry name. Must be globally unique, 5-50 lowercase alphanumeric chars.')
param registryName string

@description('Registry SKU. Basic is enough for new demos; keep Standard when the live registry was upgraded.')
param skuName string = 'Basic'

@description('Whether the admin user is enabled on the registry. Prefer managed-identity pulls; keep true only to match a live registry that depends on it.')
param adminUserEnabled bool = false

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
    name: skuName
  }
  properties: {
    adminUserEnabled: adminUserEnabled
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
