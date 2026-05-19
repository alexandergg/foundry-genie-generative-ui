@description('Azure region for Log Analytics.')
param location string

@description('Log Analytics workspace name.')
param workspaceName string

@description('Log retention in days.')
@minValue(30)
@maxValue(730)
param retentionInDays int = 30

@description('Common resource tags.')
param tags object

resource workspace 'Microsoft.OperationalInsights/workspaces@2025-02-01' = {
  name: workspaceName
  location: location
  tags: union(tags, {
    component: 'monitoring'
    riskRole: 'demo-observability'
  })
  properties: {
    retentionInDays: retentionInDays
    sku: {
      name: 'PerGB2018'
    }
  }
}

output workspaceName string = workspace.name
output workspaceResourceId string = workspace.id
