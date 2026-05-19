@description('Azure region for Log Analytics and Application Insights.')
param location string

@description('Log Analytics workspace name.')
param workspaceName string

@description('Application Insights component name.')
param applicationInsightsName string

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
    features: {
      disableLocalAuth: true
    }
  }
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: applicationInsightsName
  location: location
  tags: union(tags, {
    component: 'application-insights'
    riskRole: 'agent-observability'
  })
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspace.id
  }
}

output workspaceName string = workspace.name
output workspaceResourceId string = workspace.id
output applicationInsightsName string = applicationInsights.name
output applicationInsightsResourceId string = applicationInsights.id
output applicationInsightsConnectionString string = applicationInsights.properties.ConnectionString
