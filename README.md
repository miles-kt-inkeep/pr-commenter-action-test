# Sync Inkeep Sources and Comment on PR

A GitHub action to sync Inkeep sources and add a PR comment for each successful sync.

## Usage Example
```yml
name: Inkeep Source Sync

on:
  push:
    branches:
      - main
    paths:
      - 'docs/**'
    
jobs:
  syncSourceJob:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      issues: write
      pull-requests: write
      
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      - name: Check for changes
        uses: dorny/paths-filter@v2
        id: changes
        with:
          filters: |
            docs:
              - 'docs/**'
      - name: Sync Docs Source 
        if: steps.changes.outputs.docs == 'true'
        uses: inkeep/pr-commenter-action@v10
        env: 
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          apiKey: ${{ secrets.INKEEP_API_KEY }}
          sourceId: '{insert-source-id-here}'
        
```

- This template will trigger on a push to the `main` branch when files under `docs/**` are changed.
- An Inkeep source sync job will be created for the source with id==`sourceId`. 
- If a PR is associated with the push to main then the following comment will be made:

    :mag_right: :speech_balloon: [Inkeep](https://inkeep.com) AI search and chat service is syncing content for source '{Source-Name}'

  ## Authentication
  Please add your Inkeep Api Token to your repo under `under settings -> secrets and variables -> actions`.





