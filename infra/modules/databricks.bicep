@description('Azure region for the Databricks workspace.')
param location string

@description('Databricks workspace name.')
param workspaceName string

@description('Name of the Azure-managed resource group used by Databricks compute resources.')
param managedResourceGroupName string

@description('Databricks workspace SKU.')
param skuName string

@description('Workspace public network access.')
param publicNetworkAccess string

@description('Common resource tags.')
param tags object

resource workspace 'Microsoft.Databricks/workspaces@2026-01-01' = {
  name: workspaceName
  location: location
  sku: {
    name: skuName
  }
  tags: union(tags, {
    component: 'databricks'
    uc3Role: 'genie-workspace'
  })
  properties: {
    computeMode: 'Hybrid'
    managedResourceGroupId: subscriptionResourceId('Microsoft.Resources/resourceGroups', managedResourceGroupName)
    publicNetworkAccess: publicNetworkAccess
    requiredNsgRules: 'AllRules'
  }
}

output workspaceName string = workspace.name
output workspaceResourceId string = workspace.id
output workspaceUrl string = workspace.properties.workspaceUrl
