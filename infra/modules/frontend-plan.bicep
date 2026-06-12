@description('Azure region for the frontend App Service plan.')
param location string

@description('App Service plan name shared by the spectrum frontends.')
param appServicePlanName string

@description('App Service plan SKU name. B1 is suitable for demos; use a higher SKU for production.')
param appServicePlanSkuName string = 'B1'

@description('App Service plan SKU tier matching appServicePlanSkuName.')
param appServicePlanSkuTier string = 'Basic'

@description('Common resource tags.')
param tags object

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

output appServicePlanId string = appServicePlan.id
output appServicePlanName string = appServicePlan.name
