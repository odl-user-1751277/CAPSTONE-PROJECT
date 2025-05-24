targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the environment that can be used as part of naming resource convention')
param environmentName string

@description('Primary location for all resources')
param location string

param prefix string = 'dev'
param uiAppExists bool = false

var tags = {
  'azd-env-name': environmentName
}

resource rg 'Microsoft.Resources/resourceGroups@2022-09-01' = {
  name: 'rg-${environmentName}'
  location: location
  tags: tags
}

var uniqueId = uniqueString(rg.id)

module acrModule './acr.bicep' = {
  name: 'acr'
  scope: rg
  params: {
    uniqueId: uniqueId
    prefix: prefix
    location: location
  }
}

module aca './aca.bicep' = {
  name: 'aca'
  scope: rg
  params: {
    uniqueId: uniqueId
    prefix: prefix
    containerRegistry: acrModule.outputs.acrName
    location: location
    uiAppExists: uiAppExists
  }
}

// These outputs are copied by azd to .azure/<env name>/.env file
// post provision script will use these values, too
output AZURE_RESOURCE_GROUP string = rg.name
output AZURE_CONTAINER_REGISTRY_ENDPOINT string = acrModule.outputs.acrEndpoint
