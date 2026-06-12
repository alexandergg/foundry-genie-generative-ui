@description('Azure region for the frontend web app.')
param location string

@description('Resource ID of the (shared) App Service plan hosting this web app.')
param appServicePlanId string

@description('Azure App Service web app name for this Next.js frontend.')
param webAppName string

@description('Whether the plan SKU supports Always On (false for F1/D1).')
param alwaysOn bool = true

@description('Node.js runtime stack for the Linux App Service.')
param nodeRuntimeVersion string = 'NODE|22-lts'

@description('Startup command pointing at the Next.js standalone server for this band, e.g. node apps/controlled/web/server.js.')
param appCommandLine string

@description('AG-UI agent endpoint used by the Next.js BFF (Foundry Hosted Agent Invocations endpoint). Leave empty until the hosted agent exists.')
param agUiAgentUrl string = ''

@description('Token scope used when the Next.js BFF authenticates to the Foundry Hosted Agent endpoint.')
param agUiAgentScope string = 'https://ai.azure.com/.default'

@description('Optional Application Insights connection string for frontend App Service telemetry.')
@secure()
param applicationInsightsConnectionString string = ''

@description('Band label used in resource tags (controlled / declarative / open-ended).')
param bandName string

@description('Common resource tags.')
param tags object

resource webApp 'Microsoft.Web/sites@2024-04-01' = {
  name: webAppName
  location: location
  tags: union(tags, {
    component: 'app-service'
    riskRole: 'nextjs-frontend'
    genUiBand: bandName
  })
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlanId
    httpsOnly: true
    publicNetworkAccess: 'Enabled'
    siteConfig: {
      linuxFxVersion: nodeRuntimeVersion
      appCommandLine: appCommandLine
      alwaysOn: alwaysOn
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
