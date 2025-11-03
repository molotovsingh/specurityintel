"""
Prefect workflow orchestration for UAM Compliance System.

Provides automated, scheduled, and monitored execution of compliance workflows.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

import prefect
from prefect import flow, task, get_run_logger
from prefect.deployments import Deployment
from prefect.schedules import CronSchedule

from ..composition_root import ServiceContainer
from ..interfaces.dto import KPIRecord, Violation, Alert
from ..interfaces.errors import ProcessingError, ConfigurationError


# Configure Prefect
prefect.settings.update(
    {
        "PREFECT_API_URL": "http://localhost:4200/api",
        "PREFECT_LOGGING_LEVEL": "INFO"
    }
)


@task(
    name="Load Configuration",
    retries=3,
    retry_delay_seconds=30,
    timeout_seconds=300
)
async def load_configuration(config_path: str = "config") -> Dict[str, Any]:
    """
    Load system configuration and initialize services.
    
    Args:
        config_path: Path to configuration directory
        
    Returns:
        Initialized service container
    """
    logger = get_run_logger()
    logger.info("Loading system configuration")
    
    try:
        # Initialize production services
        container = ServiceContainer.create_production(config_path)
        
        # Validate configuration
        config = container.get_config()
        logger.info(f"Configuration loaded successfully for {len(config.thresholds.alert_thresholds)} KPIs")
        
        return {
            "container": container,
            "config": config
        }
        
    except Exception as e:
        logger.error(f"Configuration loading failed: {str(e)}")
        raise ProcessingError(
            message=f"Failed to load configuration: {str(e)}",
            context={"config_path": config_path}
        )


@task(
    name="Discover Data Files",
    retries=2,
    retry_delay_seconds=10
)
async def discover_data_files(data_dir: str = "data/incoming") -> List[str]:
    """
    Discover CSV files ready for processing.
    
    Args:
        data_dir: Directory containing CSV files
        
    Returns:
        List of file paths ready for processing
    """
    logger = get_run_logger()
    logger.info(f"Discovering data files in {data_dir}")
    
    try:
        data_path = Path(data_dir)
        if not data_path.exists():
            logger.warning(f"Data directory {data_dir} does not exist")
            return []
        
        # Find CSV files modified in last 24 hours
        cutoff_time = datetime.now() - timedelta(hours=24)
        csv_files = []
        
        for file_path in data_path.glob("*.csv"):
            if file_path.stat().st_mtime > cutoff_time.timestamp():
                csv_files.append(str(file_path))
        
        logger.info(f"Found {len(csv_files)} files for processing")
        return csv_files
        
    except Exception as e:
        logger.error(f"File discovery failed: {str(e)}")
        raise ProcessingError(
            message=f"Failed to discover data files: {str(e)}",
            context={"data_dir": data_dir}
        )


@task(
    name="Process CSV File",
    retries=3,
    retry_delay_seconds=60,
    timeout_seconds=1800  # 30 minutes
)
async def process_csv_file(file_path: str, services: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single CSV file through the complete pipeline.
    
    Args:
        file_path: Path to CSV file
        services: Service container and configuration
        
    Returns:
        Processing results with KPIs, violations, and alerts
    """
    logger = get_run_logger()
    logger.info(f"Processing CSV file: {file_path}")
    
    try:
        container = services["container"]
        
        # Parse CSV data
        logger.info("Parsing CSV data")
        data = container.csv_parser.parse(file_path)
        logger.info(f"Parsed {len(data)} records from {file_path}")
        
        # Compute KPIs
        logger.info("Computing KPIs")
        kpis = []
        for app_id in data['app_id'].unique():
            app_data = data[data['app_id'] == app_id]
            for calculator in container.kpi_calculators:
                try:
                    kpi = calculator.compute(app_data)
                    if kpi:
                        kpis.append(kpi)
                        container.storage.save_kpi(kpi)
                except Exception as e:
                    logger.warning(f"KPI calculation failed for {app_id}: {str(e)}")
        
        logger.info(f"Computed {len(kpis)} KPIs")
        
        # Evaluate policies
        logger.info("Evaluating policies")
        violations = []
        for kpi in kpis:
            try:
                violation = container.policy_engine.evaluate(kpi)
                if violation:
                    violations.append(violation)
                    container.storage.save_violation(violation)
            except Exception as e:
                logger.warning(f"Policy evaluation failed for {kpi.app_id}: {str(e)}")
        
        logger.info(f"Found {len(violations)} violations")
        
        # Generate alerts if violations exist
        alerts = []
        if violations:
            logger.info("Generating alerts")
            try:
                alert = container.alert_generator.create_alert(violations)
                if alert:
                    alerts.append(alert)
                    container.storage.save_alert(alert)
                    
                    # Send notifications
                    logger.info("Sending notifications")
                    container.slack_adapter.send_alert(alert)
                    container.email_adapter.send_alert(alert)
                    
            except Exception as e:
                logger.error(f"Alert generation failed: {str(e)}")
        
        logger.info(f"Generated {len(alerts)} alerts")
        
        # Log completion
        container.audit_logger.log_data_access(
            user_id="system",
            resource_type="CSV_FILE",
            resource_id=file_path,
            action="PROCESS",
            success=True
        )
        
        return {
            "file_path": file_path,
            "records_processed": len(data),
            "kpis_computed": len(kpis),
            "violations_found": len(violations),
            "alerts_generated": len(alerts),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"CSV processing failed: {str(e)}")
        
        # Log failure
        if "container" in services:
            services["container"].audit_logger.log_data_access(
                user_id="system",
                resource_type="CSV_FILE",
                resource_id=file_path,
                action="PROCESS",
                success=False,
                reason=str(e)
            )
        
        return {
            "file_path": file_path,
            "success": False,
            "error": str(e)
        }


@task(
    name="Generate Compliance Report",
    retries=2,
    retry_delay_seconds=30
)
async def generate_compliance_report(services: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate daily compliance report.
    
    Args:
        services: Service container and configuration
        
    Returns:
        Compliance report summary
    """
    logger = get_run_logger()
    logger.info("Generating compliance report")
    
    try:
        container = services["container"]
        
        # Load recent data
        kpis = container.storage.load_kpis()
        violations = container.storage.load_violations()
        alerts = container.storage.load_alerts()
        
        # Generate summary statistics
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_applications": len(set(kpi.app_id for kpi in kpis)),
                "total_kpis": len(kpis),
                "total_violations": len(violations),
                "total_alerts": len(alerts),
                "high_risk_apps": len([
                    v for v in violations 
                    if v.severity in ["HIGH", "CRITICAL"]
                ])
            },
            "violations_by_severity": {},
            "top_violating_apps": {},
            "recommendations": []
        }
        
        # Categorize violations by severity
        for violation in violations:
            severity = violation.severity.value
            report["violations_by_severity"][severity] = \
                report["violations_by_severity"].get(severity, 0) + 1
        
        # Find top violating applications
        app_violations = {}
        for violation in violations:
            app_violations[violation.app_id] = \
                app_violations.get(violation.app_id, 0) + 1
        
        report["top_violating_apps"] = dict(
            sorted(app_violations.items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        # Generate recommendations
        if report["summary"]["high_risk_apps"] > 0:
            report["recommendations"].append(
                "Immediate review required for high-risk applications"
            )
        
        if report["summary"]["total_violations"] > 10:
            report["recommendations"].append(
                "Consider tightening access policies across organization"
            )
        
        # Save report
        report_path = f"reports/compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        Path("reports").mkdir(exist_ok=True)
        
        import json
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Compliance report saved to {report_path}")
        
        # Log report generation
        container.audit_logger.log_configuration_change(
            user_id="system",
            component="ComplianceReporting",
            setting_name="daily_report",
            old_value="N/A",
            new_value=report_path
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise ProcessingError(
            message=f"Failed to generate compliance report: {str(e)}"
        )


@task(
    name="Cleanup Processed Files",
    retries=1
)
async def cleanup_processed_files(processed_files: List[str], 
                             archive_dir: str = "data/archive") -> None:
    """
    Move processed files to archive directory.
    
    Args:
        processed_files: List of successfully processed files
        archive_dir: Directory for archived files
    """
    logger = get_run_logger()
    logger.info(f"Archiving {len(processed_files)} processed files")
    
    try:
        archive_path = Path(archive_dir)
        archive_path.mkdir(exist_ok=True)
        
        for file_path in processed_files:
            source = Path(file_path)
            if source.exists():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{source.stem}_{timestamp}{source.suffix}"
                destination = archive_path / filename
                
                source.rename(destination)
                logger.info(f"Archived {file_path} to {destination}")
        
    except Exception as e:
        logger.error(f"File cleanup failed: {str(e)}")


@flow(
    name="UAM Compliance Processing",
    description="End-to-end compliance monitoring workflow",
    retries=1,
    log_prints=True
)
async def uam_compliance_flow(
    data_dir: str = "data/incoming",
    config_path: str = "config",
    archive_dir: str = "data/archive",
    generate_report: bool = True
) -> Dict[str, Any]:
    """
    Main UAM compliance processing workflow.
    
    Args:
        data_dir: Directory containing CSV files
        config_path: Configuration directory path
        archive_dir: Archive directory for processed files
        generate_report: Whether to generate compliance report
        
    Returns:
        Workflow execution summary
    """
    logger = get_run_logger()
    logger.info("Starting UAM Compliance Processing workflow")
    
    try:
        # Load configuration
        services = await load_configuration(config_path)
        
        # Discover data files
        csv_files = await discover_data_files(data_dir)
        
        if not csv_files:
            logger.info("No files to process")
            return {
                "status": "completed",
                "files_processed": 0,
                "message": "No files found for processing"
            }
        
        # Process each file
        processing_results = []
        processed_files = []
        
        for file_path in csv_files:
            result = await process_csv_file(file_path, services)
            processing_results.append(result)
            
            if result["success"]:
                processed_files.append(file_path)
        
        # Archive processed files
        if processed_files:
            await cleanup_processed_files(processed_files, archive_dir)
        
        # Generate compliance report
        report = None
        if generate_report:
            report = await generate_compliance_report(services)
        
        # Prepare summary
        successful_files = [r for r in processing_results if r["success"]]
        failed_files = [r for r in processing_results if not r["success"]]
        
        summary = {
            "status": "completed",
            "workflow_id": prefect.context.get_run_id(),
            "started_at": prefect.context.get_start_time(),
            "completed_at": datetime.now(),
            "files_found": len(csv_files),
            "files_processed": len(successful_files),
            "files_failed": len(failed_files),
            "total_records": sum(r.get("records_processed", 0) for r in successful_files),
            "total_kpis": sum(r.get("kpis_computed", 0) for r in successful_files),
            "total_violations": sum(r.get("violations_found", 0) for r in successful_files),
            "total_alerts": sum(r.get("alerts_generated", 0) for r in successful_files),
            "report_generated": report is not None,
            "errors": [r.get("error") for r in failed_files]
        }
        
        logger.info(f"Workflow completed: {summary}")
        return summary
        
    except Exception as e:
        logger.error(f"Workflow failed: {str(e)}")
        raise


@flow(
    name="UAM Daily Compliance Check",
    description="Scheduled daily compliance monitoring",
    retries=1
)
async def uam_daily_compliance() -> Dict[str, Any]:
    """
    Scheduled daily compliance check workflow.
    
    Returns:
        Daily compliance summary
    """
    logger = get_run_logger()
    logger.info("Starting daily compliance check")
    
    return await uam_compliance_flow(
        data_dir="data/incoming",
        config_path="config",
        archive_dir="data/archive",
        generate_report=True
    )


# Deployments
def create_deployments():
    """Create Prefect deployments for workflows."""
    
    # Daily compliance check at 2 AM UTC
    daily_deployment = Deployment.build_from_flow(
        flow=uam_daily_compliance,
        name="Daily UAM Compliance Check",
        schedule=CronSchedule(cron="0 2 * * *"),  # 2 AM UTC daily
        tags=["compliance", "daily"],
        description="Automated daily compliance monitoring and reporting"
    )
    
    # On-demand processing
    on_demand_deployment = Deployment.build_from_flow(
        flow=uam_compliance_flow,
        name="On-Demand UAM Processing",
        tags=["compliance", "on-demand"],
        description="Manual compliance processing workflow"
    )
    
    return [daily_deployment, on_demand_deployment]


if __name__ == "__main__":
    # Example usage
    import asyncio
    
    # Run on-demand processing
    result = asyncio.run(uam_compliance_flow())
    print(f"Processing result: {result}")
    
    # Create deployments
    deployments = create_deployments()
    for deployment in deployments:
        print(f"Created deployment: {deployment.name}")