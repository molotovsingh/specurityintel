"""
Simple workflow scheduler for UAM Compliance System.

Provides automated scheduling and execution of compliance workflows.
"""

import asyncio
import schedule
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

from ..composition_root import ServiceContainer
from ..interfaces.errors import ProcessingError


class ComplianceScheduler:
    """Simple scheduler for compliance workflows."""
    
    def __init__(self, config_path: str = "config"):
        """Initialize scheduler with configuration."""
        self.config_path = config_path
        self.container = None
        self.logger = None
        
    def initialize(self):
        """Initialize services and logging."""
        try:
            self.container = ServiceContainer.create_production(self.config_path)
            self.logger = self.container.audit_logger
            
            self.logger.log_configuration_change(
                user_id="system",
                component="ComplianceScheduler",
                setting_name="initialization",
                old_value="N/A",
                new_value="initialized"
            )
            
        except Exception as e:
            raise ProcessingError(
                message=f"Scheduler initialization failed: {str(e)}",
                context={"config_path": self.config_path}
            )
    
    async def process_compliance_workflow(self) -> Dict[str, Any]:
        """Execute the main compliance processing workflow."""
        if not self.container:
            raise ProcessingError(
                message="Scheduler not initialized",
                context={"operation": "process_compliance_workflow"}
            )
        
        start_time = datetime.now()
        self.logger.log_data_access(
            user_id="system",
            resource_type="WORKFLOW",
            resource_id="compliance_processing",
            action="START"
        )
        
        try:
            # Discover data files
            data_dir = Path("data/incoming")
            if not data_dir.exists():
                return {
                    "status": "completed",
                    "message": "No data directory found"
                }
            
            # Find CSV files
            csv_files = list(data_dir.glob("*.csv"))
            if not csv_files:
                return {
                    "status": "completed", 
                    "message": "No CSV files found"
                }
            
            results = {
                "files_processed": 0,
                "total_records": 0,
                "kpis_computed": 0,
                "violations_found": 0,
                "alerts_generated": 0,
                "errors": []
            }
            
            # Process each file
            for file_path in csv_files:
                try:
                    # Parse CSV
                    data = self.container.csv_parser.parse(str(file_path))
                    results["total_records"] += len(data)
                    
                    # Compute KPIs
                    kpis = []
                    for app_id in data['app_id'].unique():
                        app_data = data[data['app_id'] == app_id]
                        for calculator in self.container.kpi_calculators:
                            try:
                                kpi = calculator.compute(app_data)
                                if kpi:
                                    kpis.append(kpi)
                                    self.container.storage.save_kpi(kpi)
                            except Exception as e:
                                self.logger.log_data_access(
                                    user_id="system",
                                    resource_type="KPI_CALCULATION",
                                    resource_id=f"{app_id}_{calculator.__class__.__name__}",
                                    action="ERROR",
                                    reason=str(e)
                                )
                    
                    results["kpis_computed"] += len(kpis)
                    
                    # Evaluate policies
                    violations = []
                    for kpi in kpis:
                        try:
                            violation = self.container.policy_engine.evaluate(kpi)
                            if violation:
                                violations.append(violation)
                                self.container.storage.save_violation(violation)
                        except Exception as e:
                            self.logger.log_data_access(
                                user_id="system",
                                resource_type="POLICY_EVALUATION",
                                resource_id=kpi.app_id,
                                action="ERROR",
                                reason=str(e)
                            )
                    
                    results["violations_found"] += len(violations)
                    
                    # Generate alerts
                    if violations:
                        try:
                            alert = self.container.alert_generator.create_alert(violations)
                            if alert:
                                self.container.storage.save_alert(alert)
                                
                                # Send notifications
                                self.container.slack_adapter.send_alert(alert)
                                self.container.email_adapter.send_alert(alert)
                                
                                results["alerts_generated"] += 1
                        except Exception as e:
                            self.logger.log_data_access(
                                user_id="system",
                                resource_type="ALERT_GENERATION",
                                resource_id=str(file_path),
                                action="ERROR",
                                reason=str(e)
                            )
                    
                    # Archive processed file
                    archive_dir = Path("data/archive")
                    archive_dir.mkdir(exist_ok=True)
                    
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    archive_path = archive_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
                    file_path.rename(archive_path)
                    
                    results["files_processed"] += 1
                    
                    self.logger.log_data_access(
                        user_id="system",
                        resource_type="CSV_FILE",
                        resource_id=str(file_path),
                        action="PROCESSED",
                        success=True
                    )
                    
                except Exception as e:
                    error_msg = f"Failed to process {file_path}: {str(e)}"
                    results["errors"].append(error_msg)
                    self.logger.log_data_access(
                        user_id="system",
                        resource_type="CSV_FILE",
                        resource_id=str(file_path),
                        action="ERROR",
                        reason=str(e)
                    )
            
            # Log completion
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.logger.log_data_access(
                user_id="system",
                resource_type="WORKFLOW",
                resource_id="compliance_processing",
                action="COMPLETE",
                success=True
            )
            
            results.update({
                "status": "completed",
                "started_at": start_time.isoformat(),
                "completed_at": end_time.isoformat(),
                "duration_seconds": duration,
                "records_per_second": results["total_records"] / duration if duration > 0 else 0
            })
            
            return results
            
        except Exception as e:
            self.logger.log_data_access(
                user_id="system",
                resource_type="WORKFLOW",
                resource_id="compliance_processing",
                action="ERROR",
                reason=str(e)
            )
            raise ProcessingError(
                message=f"Compliance workflow failed: {str(e)}"
            )
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """Generate daily compliance report."""
        if not self.container:
            raise ProcessingError(
                message="Scheduler not initialized",
                context={"operation": "generate_daily_report"}
            )
        
        try:
            # Load data
            kpis = self.container.storage.load_kpis()
            violations = self.container.storage.load_violations()
            alerts = self.container.storage.load_alerts()
            
            # Generate report
            report = {
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "total_applications": len(set(kpi.app_id for kpi in kpis)),
                    "total_kpis": len(kpis),
                    "total_violations": len(violations),
                    "total_alerts": len(alerts),
                    "high_risk_violations": len([
                        v for v in violations 
                        if v.severity.value in ["HIGH", "CRITICAL"]
                    ])
                },
                "violations_by_app": {},
                "violations_by_severity": {},
                "recommendations": []
            }
            
            # Categorize violations
            for violation in violations:
                app_id = violation.app_id
                severity = violation.severity.value
                
                report["violations_by_app"][app_id] = \
                    report["violations_by_app"].get(app_id, 0) + 1
                report["violations_by_severity"][severity] = \
                    report["violations_by_severity"].get(severity, 0) + 1
            
            # Generate recommendations
            if report["summary"]["high_risk_violations"] > 0:
                report["recommendations"].append(
                    "Immediate review required for high-risk violations"
                )
            
            if report["summary"]["total_violations"] > 20:
                report["recommendations"].append(
                    "Consider tightening access policies"
                )
            
            # Save report
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            
            report_file = reports_dir / f"compliance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            import json
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self.logger.log_configuration_change(
                user_id="system",
                component="ComplianceReporting",
                setting_name="daily_report",
                old_value="N/A",
                new_value=str(report_file)
            )
            
            return report
            
        except Exception as e:
            raise ProcessingError(
                message=f"Report generation failed: {str(e)}"
            )
    
    def run_scheduler(self):
        """Run the scheduler with scheduled jobs."""
        if not self.container:
            self.initialize()
        
        # Schedule jobs
        schedule.every().day.at("02:00").do(self.run_daily_compliance)
        schedule.every().day.at("06:00").do(self.generate_daily_report)
        schedule.every().hour.do(self.check_for_new_files)
        
        print("🚀 UAM Compliance Scheduler started")
        print("📅 Scheduled jobs:")
        print("   - Daily compliance check: 02:00 UTC")
        print("   - Daily report generation: 06:00 UTC") 
        print("   - File monitoring: Every hour")
        print("\nPress Ctrl+C to stop...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\n🛑 Scheduler stopped")
    
    async def run_daily_compliance(self):
        """Run daily compliance workflow."""
        print(f"🔄 Running daily compliance check at {datetime.now()}")
        result = await self.process_compliance_workflow()
        print(f"✅ Daily compliance completed: {result['status']}")
        if result.get('errors'):
            print(f"⚠️  Errors encountered: {len(result['errors'])}")
    
    def check_for_new_files(self):
        """Check for new files and process if found."""
        data_dir = Path("data/incoming")
        if not data_dir.exists():
            return
        
        # Find files modified in last hour
        cutoff_time = datetime.now() - timedelta(hours=1)
        new_files = [
            f for f in data_dir.glob("*.csv")
            if datetime.fromtimestamp(f.stat().st_mtime) > cutoff_time
        ]
        
        if new_files:
            print(f"📁 Found {len(new_files)} new files")
            # Trigger async processing
            asyncio.create_task(self.process_compliance_workflow())


def main():
    """Main entry point for scheduler."""
    import argparse
    
    parser = argparse.ArgumentParser(description="UAM Compliance Scheduler")
    parser.add_argument(
        "--mode", 
        choices=["scheduler", "process", "report"],
        default="scheduler",
        help="Operation mode"
    )
    parser.add_argument(
        "--config",
        default="config",
        help="Configuration directory path"
    )
    
    args = parser.parse_args()
    
    scheduler = ComplianceScheduler(args.config)
    
    if args.mode == "scheduler":
        scheduler.run_scheduler()
    elif args.mode == "process":
        asyncio.run(scheduler.run_daily_compliance())
    elif args.mode == "report":
        scheduler.initialize()
        report = scheduler.generate_daily_report()
        print(f"📊 Report generated: {report['summary']}")


if __name__ == "__main__":
    main()