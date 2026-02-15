#!/usr/bin/env python3
"""
Risk Intelligence Graph Analysis

Runs the agentic graph analytics workflow for risk management / sanctions screening.
Uses the agentic-graph-analytics library with fintech-aligned patterns.
Same cluster/GAE config as fraud-intelligence for consistency.

Usage:
    python run_risk_analysis.py

Requirements:
    - agentic-graph-analytics installed (pip install -e ~/code/agentic-graph-analytics)
    - .env file with ArangoDB credentials and LLM API keys
    - Graph data loaded in ArangoDB (risk-management database)

Output:
    - Markdown/HTML reports in risk_analysis_output/
    - Risk patterns with classifications
    - Historical tracking in analytics catalog (for compliance/audit)
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Any


def _require_platform():
    try:
        from graph_analytics_ai.ai.llm import create_llm_provider  # type: ignore
        from graph_analytics_ai.db_connection import get_db_connection  # type: ignore

        from graph_analytics_ai.ai.agents import (  # type: ignore
            OrchestratorAgent,
            AgentNames,
            AgentDefaults,
            SchemaAnalysisAgent,
            RequirementsAgent,
            UseCaseAgent,
            TemplateAgent,
            ExecutionAgent,
            ReportingAgent,
        )

        from graph_analytics_ai.ai.reporting import ReportGenerator, ReportFormat  # type: ignore
        from graph_analytics_ai.catalog import (  # type: ignore
            AnalysisCatalog,
            CatalogQueries,
            ExecutionFilter,
            ExecutionStatus,
        )
        from graph_analytics_ai.catalog.storage import ArangoDBStorage  # type: ignore
        from graph_analytics_ai.ai.execution.models import (  # type: ignore
            AnalysisJob,
            ExecutionResult,
            ExecutionStatus as JobExecutionStatus,
        )

        return (
            create_llm_provider,
            get_db_connection,
            OrchestratorAgent,
            AgentNames,
            AgentDefaults,
            SchemaAnalysisAgent,
            RequirementsAgent,
            UseCaseAgent,
            TemplateAgent,
            ExecutionAgent,
            ReportingAgent,
            ReportGenerator,
            ReportFormat,
            AnalysisCatalog,
            CatalogQueries,
            ExecutionFilter,
            ExecutionStatus,
            ArangoDBStorage,
            AnalysisJob,
            ExecutionResult,
            JobExecutionStatus,
        )
    except ImportError as e:
        print("ERROR: agentic-graph-analytics is not available.")
        print("\nFix: pip install -e ~/code/agentic-graph-analytics")
        raise SystemExit(1) from e


def _apply_env_mapping() -> None:
    """
    Map env naming and ensure endpoint has port (same pattern as fraud-intelligence).
    Uses MODE/ARANGO_MODE to choose LOCAL vs REMOTE settings.
    Note: when using self-managed GRAL, routes can take ~30–90s to become ready after
    the service is created; transient 404/503s may occur during rollout.
    """
    try:
        sys.path.insert(0, "scripts")
        from common import apply_config_to_env, get_arango_config, load_dotenv  # type: ignore

        load_dotenv()
        cfg = get_arango_config(forced_mode=os.getenv("MODE") or os.getenv("ARANGO_MODE") or None)
        apply_config_to_env(cfg)
    except Exception:
        pass

    if os.getenv("ARANGO_ENDPOINT") is None and os.getenv("ARANGO_URL"):
        try:
            from common import ensure_endpoint_has_port  # type: ignore
            endpoint = ensure_endpoint_has_port(os.environ["ARANGO_URL"])
        except Exception:
            endpoint = os.environ["ARANGO_URL"]
        os.environ["ARANGO_ENDPOINT"] = endpoint
    if os.getenv("ARANGO_USER") is None and os.getenv("ARANGO_USERNAME"):
        os.environ["ARANGO_USER"] = os.environ["ARANGO_USERNAME"]

    # Same as fraud: self-managed GAE when no AMP keys
    mode = (os.getenv("GAE_DEPLOYMENT_MODE") or "").strip().lower()
    api_key_id = os.getenv("ARANGO_GRAPH_API_KEY_ID")
    if (not mode or mode in ("amp", "managed", "arangograph")) and not api_key_id:
        os.environ["GAE_DEPLOYMENT_MODE"] = "self_managed"


async def main():
    """Run risk intelligence graph analysis workflow."""
    print("=" * 70)
    print(" " * 15 + "RISK INTELLIGENCE GRAPH ANALYSIS")
    print(" " * 18 + "Sanctions / PEP-AML Risk Detection")
    print("=" * 70)
    print()

    _apply_env_mapping()

    (
        create_llm_provider,
        get_db_connection,
        OrchestratorAgent,
        AgentNames,
        AgentDefaults,
        SchemaAnalysisAgent,
        RequirementsAgent,
        UseCaseAgent,
        TemplateAgent,
        ExecutionAgent,
        ReportingAgent,
        ReportGenerator,
        ReportFormat,
        AnalysisCatalog,
        CatalogQueries,
        ExecutionFilter,
        ExecutionStatus,
        ArangoDBStorage,
        AnalysisJob,
        ExecutionResult,
        JobExecutionStatus,
    ) = _require_platform()

    max_exec_raw = (os.getenv("RISK_ANALYSIS_MAX_EXECUTIONS") or "").strip()
    if max_exec_raw:
        try:
            max_exec = int(max_exec_raw)
            if max_exec > 0:
                AgentDefaults.MAX_EXECUTIONS = max_exec
        except ValueError:
            pass

    output_dir = Path("risk_analysis_output")
    output_dir.mkdir(exist_ok=True)
    print(f"✓ Output directory: {output_dir.absolute()}")

    # Reports-only mode: regenerate HTML/MD from existing result collections (no GRAL needed).
    reports_only = (os.getenv("RISK_ANALYSIS_REPORTS_ONLY") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )

    GRAPH_NAME = os.getenv("RISK_GRAPH_NAME") or "KnowledgeGraph"
    INDUSTRY = "fintech"  # Closest built-in for risk/sanctions/PEP-AML

    input_files: List[str] = []
    possible_inputs = [
        "docs/business_requirements.md",
        "docs/domain_description.md",
        "docs/PRD.md",
        "docs/walkthrough.md",
        "docs/implementation_plan.md",
        "README.md",
    ]
    for filepath in possible_inputs:
        if Path(filepath).exists():
            input_files.append(filepath)

    if input_files:
        print(f"✓ Using {len(input_files)} input files for context:")
        for f in input_files:
            print(f"    - {f}")
    else:
        print("⚠ No input files found (analysis will be generic)")
    print()

    print("[1/5] Initializing agentic workflow...")
    print(f"      Graph: {GRAPH_NAME}")
    print(f"      Industry: {INDUSTRY}")

    enable_catalog = os.getenv("RISK_ANALYSIS_ENABLE_CATALOG", "true").lower() in ("1", "true", "yes", "on")

    try:
        db = get_db_connection()
        llm_provider = create_llm_provider()

        catalog: Optional[Any] = None
        current_epoch: Optional[Any] = None
        storage: Optional[Any] = None

        if enable_catalog:
            try:
                storage = ArangoDBStorage(db)
                catalog = AnalysisCatalog(storage)
                epoch_name = f"risk-detection-{datetime.now().strftime('%Y-%m')}"
                try:
                    existing_epochs = catalog.query_epochs(filter=None, limit=100)
                    current_epoch = next((e for e in existing_epochs if e.name == epoch_name), None)
                except Exception:
                    current_epoch = None

                if current_epoch:
                    print(f"✓ Using existing epoch: {epoch_name}")
                else:
                    current_epoch = catalog.create_epoch(
                        name=epoch_name,
                        description=f"Monthly risk detection analysis - {datetime.now().strftime('%B %Y')}",
                        tags=["production", "risk_intelligence", "monthly", "compliance"],
                    )
                    print(f"✓ Created catalog epoch: {epoch_name}")
                print(f"  Epoch ID: {current_epoch.epoch_id}")
                print("  📊 Catalog tracking ENABLED")
            except Exception as e:
                print(f"⚠ Failed to initialize catalog: {e}")
                catalog = None
                current_epoch = None
                storage = None
        else:
            print("  📊 Catalog tracking DISABLED")

        core_collections = ["Person", "Organization", "Vessel", "Aircraft"]
        satellite_collections = ["Class", "Property", "Ontology"]

        agents = {
            AgentNames.SCHEMA_ANALYST: SchemaAnalysisAgent(
                llm_provider=llm_provider, db_connection=db
            ),
            AgentNames.REQUIREMENTS_ANALYST: RequirementsAgent(
                llm_provider=llm_provider, catalog=catalog
            ),
            AgentNames.USE_CASE_EXPERT: UseCaseAgent(
                llm_provider=llm_provider, catalog=catalog
            ),
            AgentNames.TEMPLATE_ENGINEER: TemplateAgent(
                llm_provider=llm_provider,
                graph_name=GRAPH_NAME,
                core_collections=core_collections,
                satellite_collections=satellite_collections,
                catalog=catalog
            ),
            AgentNames.EXECUTION_SPECIALIST: ExecutionAgent(
                llm_provider=llm_provider, catalog=catalog
            ),
            AgentNames.REPORTING_SPECIALIST: ReportingAgent(
                llm_provider=llm_provider, industry=INDUSTRY
            ),
        }

        orchestrator = OrchestratorAgent(
            llm_provider=llm_provider,
            agents=agents,
            catalog=catalog
        )
        report_generator = ReportGenerator(llm_provider=llm_provider, industry=INDUSTRY)

        if catalog and current_epoch:
            agents[AgentNames.EXECUTION_SPECIALIST].executor.epoch_id = current_epoch.epoch_id

        print("✓ Initialized agents")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        print("\nCheck: .env, ArangoDB connection, pip install -e ~/code/agentic-graph-analytics")
        sys.exit(1)

    if reports_only:
        print()
        print("[2/5] Reports-only mode ENABLED")
        print("      Regenerating reports from existing result collections (no GRAL execution)")
        print()

        def _infer_algorithm(sample: list[dict]) -> str:
            for d in sample:
                if isinstance(d, dict) and "rank" in d:
                    return "pagerank"
                if isinstance(d, dict) and "component" in d:
                    return "wcc"
                if isinstance(d, dict) and ("community" in d or "label" in d):
                    return "label_propagation"
            return "wcc"

        def _fetch_results(collection: str, limit: int) -> list[dict]:
            cursor = db.aql.execute(
                "FOR d IN @@col LIMIT @limit RETURN d",
                bind_vars={"@col": collection, "limit": limit},
            )
            return list(cursor)

        report_collections = [
            "uc_001_results",
            "uc_s01_results",
            "uc_s02_results",
            "uc_s03_results",
            "uc_s04_results",
            "uc_s05_results",
            "uc_r01_results",
        ]
        limit = int(os.getenv("RISK_ANALYSIS_REPORTS_LIMIT", "1000") or "1000")

        existing = []
        for c in report_collections:
            try:
                if db.has_collection(c):
                    existing.append(c)
            except Exception:
                continue

        if not existing:
            print("✗ No known result collections found to report on.")
            sys.exit(1)

        print(f"✓ Found {len(existing)} result collections:")
        for c in existing:
            print(f"    - {c}")
        print()

        reports = []
        for idx, c in enumerate(existing, 1):
            results = _fetch_results(c, limit)
            algo = _infer_algorithm(results)

            job = AnalysisJob(
                job_id=f"regenerated-{c}",
                template_name=c,
                algorithm=algo,
                status=JobExecutionStatus.COMPLETED,
                submitted_at=datetime.now(),
                started_at=datetime.now(),
                completed_at=datetime.now(),
                result_collection=c,
                result_count=len(results),
                execution_time_seconds=0.0,
            )
            exec_result = ExecutionResult(job=job, success=True, results=results)
            reports.append(report_generator.generate_report(exec_result))

        print("[3/5] Processing results...")
        print(f"✓ Generated {len(reports)} reports")
        total_insights = sum(len(getattr(r, "insights", []) or []) for r in reports)
        print(f"✓ Total insights: {total_insights}")
        print()

        print("[4/5] Catalog disabled, skipping")
        print()

        print("[5/5] Saving reports...")
        for i, report in enumerate(reports, 1):
            report_name = f"risk_report_{i}"
            md_path = output_dir / f"{report_name}.md"
            html_path = output_dir / f"{report_name}.html"
            md_path.write_text(report_generator.format_report(report, ReportFormat.MARKDOWN))
            html_path.write_text(report_generator.format_report(report, ReportFormat.HTML))
            print(f"  ✓ {md_path.name}")
            print(f"  ✓ {html_path.name}")
        print()

        print("=" * 70)
        print(" " * 25 + "✓ REPORTS REGENERATED")
        print("=" * 70)
        print(f"📁 Reports: {output_dir.absolute()}")
        return

    print()
    print("[2/5] Running agentic workflow...")
    print("      Schema analysis → Requirements → Use cases → Templates → Execution → Reports")
    enable_parallelism = os.getenv("RISK_ANALYSIS_PARALLELISM", "false").lower() in ("1", "true", "yes", "on")
    print(f"      Parallelism: {'ENABLED' if enable_parallelism else 'DISABLED (safer for self-managed GAE)'}")
    print()

    try:
        if enable_parallelism:
            state = await orchestrator.run_workflow_async(
                input_documents=input_files if input_files else [],
                database_config=None,
                enable_parallelism=True,
            )
        else:
            state = orchestrator.run_workflow(
                input_documents=input_files if input_files else [],
                database_config=None,
            )
        print("✓ Workflow completed successfully")
    except Exception as e:
        print(f"✗ Workflow failed: {e}")
        sys.exit(1)

    print()
    print("[3/5] Processing results...")

    if not state.reports:
        print("✗ No reports generated")
        sys.exit(1)

    print(f"✓ Generated {len(state.reports)} reports")
    total_insights = sum(len(getattr(r, "insights", []) or []) for r in state.reports)
    print(f"✓ Total insights: {total_insights}")
    print()

    if catalog and current_epoch and storage:
        print("[4/5] Querying catalog...")
        try:
            queries = CatalogQueries(storage)
            recent_executions = queries.query_with_pagination(
                filter=ExecutionFilter(
                    epoch_id=current_epoch.epoch_id,
                    status=ExecutionStatus.COMPLETED,
                ),
                page=1,
                page_size=100
            )
            print(f"✓ Tracked {recent_executions.total_count} executions in catalog")
        except Exception as e:
            print(f"⚠ Failed to query catalog: {e}")
    else:
        print("[4/5] Catalog disabled, skipping")
    print()

    print("[5/5] Saving reports...")
    for i, report in enumerate(state.reports, 1):
        report_name = f"risk_report_{i}"
        md_path = output_dir / f"{report_name}.md"
        try:
            md_content = report_generator.format_report(report, ReportFormat.MARKDOWN)
            md_path.write_text(md_content)
            print(f"  ✓ {md_path.name}")
        except Exception as e:
            print(f"  ✗ Markdown: {e}")
        html_path = output_dir / f"{report_name}.html"
        try:
            html_content = report_generator.format_report(report, ReportFormat.HTML)
            html_path.write_text(html_content)
            print(f"  ✓ {html_path.name}")
        except Exception as e:
            print(f"  ⚠ HTML: {e}")
        print(f"  📊 Report {i}: {report.title} ({len(report.insights)} insights)")
    print()

    print("=" * 70)
    print(" " * 25 + "✓ ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"📁 Reports: {output_dir.absolute()}")
    print()
    if catalog and current_epoch:
        print("📊 Catalog:", current_epoch.name, current_epoch.epoch_id)
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠ Interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
