#!/usr/bin/env python3
"""
UAM Compliance System Deployment Script

Deploys workflows to Prefect and starts monitoring.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from orchestration.prefect_flows import create_deployments, uam_compliance_flow
from prefect import serve


async def deploy_workflows():
    """Deploy workflows to Prefect."""
    print("🚀 Deploying UAM Compliance Workflows...")
    
    try:
        # Create deployments
        deployments = create_deployments()
        
        print(f"✅ Created {len(deployments)} deployments:")
        for deployment in deployments:
            print(f"   - {deployment.name}")
        
        # Start serving workflows
        print("\n🔄 Starting workflow service...")
        await serve(
            uam_compliance_flow,
            deployments[0],  # Daily deployment
            deployments[1]   # On-demand deployment
        )
        
    except Exception as e:
        print(f"❌ Deployment failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(deploy_workflows())