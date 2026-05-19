@description('Azure region for the managed identity.')
param location string

@description('User-assigned managed identity name.')
param identityName string

@description('Common resource tags.')
param tags object

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: identityName
  location: location
  tags: union(tags, {
    component: 'identity'
    riskRole: 'agent-runtime-identity'
  })
}

output identityResourceId string = identity.id
output identityName string = identity.name
output clientId string = identity.properties.clientId
output principalId string = identity.properties.principalId
