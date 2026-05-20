@description('Azure region for the frontend web app.')
param location string

@description('App Service plan name for the frontend.')
param appServicePlanName string

@description('Azure App Service web app name for the Next.js frontend.')
param webAppName string

@description('App Service plan SKU name. B1 is suitable for demos; use a higher SKU for production.')
param appServicePlanSkuName string = 'B1'

@description('App Service plan SKU tier matching appServicePlanSkuName.')
param appServicePlanSkuTier string = 'Basic'

@description('Node.js runtime stack for the Linux App Service.')
param nodeRuntimeVersion string = 'NODE|22-lts'

@description('Foundry Hosted Agent Invocations endpoint used by the Next.js BFF. Leave empty until the hosted agent exists.')
param agUiAgentUrl string = ''

@description('Token scope used when the Next.js BFF authenticates to the Foundry Hosted Agent endpoint.')
param agUiAgentScope string = 'https://ai.azure.com/.default'

@description('Optional Application Insights connection string for frontend App Service telemetry.')
@secure()
param applicationInsightsConnectionString string = ''

@description('Common resource tags.')
param tags object

var appServiceAlwaysOn = !contains([
  'F1'
  'D1'
], appServicePlanSkuName)

resource appServicePlan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: appServicePlanName
  location: location
  tags: union(tags, {
    component: 'app-service-plan'
    riskRole: 'frontend-hosting'
  })
  sku: {
    name: appServicePlanSkuName
    tier: appServicePlanSkuTier
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

resource webApp 'Microsoft.Web/sites@2024-04-01' = {
  name: webAppName
  location: location
  tags: union(tags, {
    component: 'app-service'
    riskRole: 'nextjs-frontend'
  })
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    publicNetworkAccess: 'Enabled'
    siteConfig: {
      linuxFxVersion: nodeRuntimeVersion
      appCommandLine: 'node apps/web/server.js'
      alwaysOn: appServiceAlwaysOn
      ftpsState: 'FtpsOnly'
      minTlsVersion: '1.2'
      http20Enabled: true
      appSettings: [
        {
          name: 'AG_UI_AGENT_URL'
          value: agUiAgentUrl
        }
        {
          name: 'AG_UI_AGENT_AUTH'
          value: empty(agUiAgentUrl) ? '' : 'azure-identity'
        }
        {
          name: 'AG_UI_AGENT_SCOPE'
          value: agUiAgentScope
        }
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'false'
        }
        {
          name: 'ENABLE_ORYX_BUILD'
          value: 'false'
        }
        {
          name: 'WEBSITE_NODE_DEFAULT_VERSION'
          value: '~22'
        }
        {
          name: 'NEXT_TELEMETRY_DISABLED'
          value: '1'
        }
        {
          name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
          value: applicationInsightsConnectionString
        }
      ]
    }
  }
}

output webAppName string = webApp.name
output webAppResourceId string = webApp.id
output webAppDefaultHostName string = webApp.properties.defaultHostName
output webAppPrincipalId string = webApp.identity.principalId
output appServicePlanName string = appServicePlan.name
