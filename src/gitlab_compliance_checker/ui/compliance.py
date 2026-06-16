import concurrent.futures
from typing import Any, Dict

import streamlit as st

from gitlab_compliance_checker.infrastructure.gitlab.api_helper import get_project_branches as api_get_branches
from gitlab_compliance_checker.infrastructure.gitlab.pipeline_checker import EXPECTED_STAGES
from gitlab_compliance_checker.infrastructure.gitlab.projects import extract_path_from_url, get_project_with_retries
from gitlab_compliance_checker.services.compliance.compliance_service import (
    get_dx_suggestions,
    run_project_compliance_checks,
)


@st.cache_data(ttl=60)
def cached_get_project(_gl_client, path_or_id):
    """Cached wrapper for get_project_with_retries."""
    return get_project_with_retries(_gl_client, path_or_id)


@st.cache_data(ttl=300, show_spinner=False)
def cached_run_compliance(_gl_client, project_id: int, ref: str) -> dict:
    """Cache compliance results for 5 min — prevents 200 users re-running the same ~40 API calls."""
    return run_project_compliance_checks(_gl_client, project_id, ref=ref)


def get_project_branches(gl_client, project_id):
    try:
        return api_get_branches(gl_client, project_id)
    except Exception:
        return []


def render_precommit_analysis_ui(pc_report: Dict[str, Any]):
    st.markdown("#### 🪝 Pre-commit Hook Analysis")

    if not pc_report.get("available"):
        st.warning("No `.pre-commit-config.yaml` found in this repository.")
        return

    st.caption(
        f"{pc_report.get('repo_count', 0)} hook repo(s) configured — {len(pc_report.get('all_hooks', []))} hook(s) total"
    )
    st.markdown("---")

    categories = pc_report.get("categories", {})
    cols = st.columns(len(categories))
    for i, (_, cat_info) in enumerate(categories.items()):
        with cols[i]:
            icon = "✅" if cat_info["present"] else "❌"
            st.markdown(f"**{icon} {cat_info['label']}**")
            if cat_info["detected"]:
                st.caption(f"Tools: {', '.join(cat_info['detected'])}")
            else:
                st.caption("None detected")

    issues = pc_report.get("issues", [])
    if issues:
        st.markdown("##### 🚩 Hook Quality Issues:")
        for issue in issues:
            icon = "🔴" if issue.get("severity") == "error" else "🟡"
            st.markdown(f"{icon} {issue.get('message')}")


def render_dx_ci_pipeline_ui(dx_report: Dict[str, Any]):
    st.markdown("#### 🧠 CI Pipeline Analysis")

    if "error" in dx_report:
        st.error(f"Error parsing CI configuration: {dx_report['error']}")
        return

    # Stage Status Overview
    st.markdown("---")
    cols = st.columns(len(EXPECTED_STAGES))
    for i, stage in enumerate(EXPECTED_STAGES):
        details = dx_report.get("jobs", {}).get(stage, {})
        with cols[i]:
            if not details.get("stage_present"):
                st.markdown(f"❌ **{stage}**")
            else:
                job_icon = "✅" if details.get("job_present") else "❌"
                tool_icon = "✅" if details.get("tool_detected") else "❌"
                st.markdown(f"**{stage}**")
                st.write(f"Job: {job_icon}")
                st.write(f"Tool: {tool_icon}")
                if details.get("detected_tools"):
                    st.caption(f"Tools: {', '.join(details['detected_tools'])}")

    # Display Issues with severity icons
    issues = dx_report.get("issues", [])
    if issues:
        st.markdown("##### 🚩 Pipeline Quality Issues:")
        for issue in issues:
            icon = "🔴" if issue.get("severity") == "error" else "🟡"
            st.markdown(f"{icon} {issue.get('message')}")


def render_project_compliance_details(report: Dict[str, Any]):
    """Renders the detailed compliance report as a single scrollable page."""
    # --- Summary Metrics ---
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Compliance Score", f"{report.get('dx_score', 0)}%")
    lang = report.get("tools", {}).get("project_type", "Unknown")
    m_col2.metric("Stack", lang)
    m_col3.metric("AGPLv3 Compliance", "✅" if report["license"].get("valid") else "❌")
    docs = report.get("docs", {})
    docs_status = "✅ Complete" if docs.get("all_present") else f"❌ {len(docs.get('missing', []))} Missing"
    m_col4.metric("Documentation", docs_status)

    # --- Score Breakdown ---
    tools = report.get("tools", {})
    quality = tools.get("quality_tools", {})
    security = tools.get("security", {})
    testing = tools.get("testing", {})
    automation = tools.get("automation", {})
    speckit = report.get("speckit", {})
    meta = report.get("metadata", {})

    score_checks = [
        # DX Tools
        (
            quality.get("ruff") or quality.get("biome") or quality.get("eslint"),
            "Linter",
            "ruff / biome / eslint present in config",
        ),
        (
            quality.get("mypy") or quality.get("knip"),
            "Type Checker",
            "mypy (Python) or knip (JS/TS) present",
        ),
        (
            security.get("secret_scanning"),
            "Secret Scanning",
            "gitleaks / trufflehog / detect-secrets in CI or pre-commit",
        ),
        (
            security.get("dependency_audit"),
            "Dependency Audit",
            "pip-audit / npm audit / uv audit / snyk in CI or pre-commit",
        ),
        (
            testing.get("coverage"),
            "Coverage Reporting",
            "pytest-cov / --cov / codecov detected",
        ),
        (
            automation.get("git_cliff"),
            "Changelog Automation",
            "cliff.toml present or git-cliff in CI",
        ),
        (
            automation.get("pre_commit"),
            "Pre-commit Hooks",
            ".pre-commit-config.yaml present",
        ),
        (
            automation.get("gitlab_ci"),
            "GitLab CI Pipeline",
            ".gitlab-ci.yml present",
        ),
        # Compliance
        (
            report["license"].get("valid"),
            "AGPLv3 License",
            "LICENSE file contains full AGPLv3 text",
        ),
        (
            docs.get("all_present"),
            "Documentation",
            "All required documentation files present",
        ),
        (
            meta.get("description_present"),
            "Project Description",
            "GitLab project has a description set",
        ),
        (
            meta.get("tags_present"),
            "Git Tags",
            "Project has at least one release tag",
        ),
        # Spec-Kit
        (
            speckit.get("setup_present"),
            "Spec-Kit Setup",
            ".specify/ directory present",
        ),
        (
            speckit.get("constitution_present"),
            "Spec-Kit Constitution",
            ".specify/memory/constitution.md present",
        ),
        (
            speckit.get("templates_present"),
            "Spec-Kit Templates",
            ".specify/templates/ with standard templates",
        ),
        (
            speckit.get("specs_dir_present"),
            "Feature Specs",
            "specs/ directory with at least one feature spec",
        ),
    ]

    passed = sum(1 for ok, _, _ in score_checks if ok)
    total = len(score_checks)

    with st.expander(f"📊 Score Breakdown — {passed}/{total} checks passed ({report.get('dx_score', 0)}%)"):
        st.caption("Each check is worth 6.25% of the total score. All checks are binary: ✅ pass or ❌ fail.")
        st.markdown("---")
        for ok, label, detail in score_checks:
            icon = "✅" if ok else "❌"
            pts = "+6.25%" if ok else "+0%"
            col_a, col_b, col_c = st.columns([0.5, 3, 5])
            col_a.markdown(icon)
            col_b.markdown(f"**{label}** `{pts}`")
            col_c.caption(detail)

    st.markdown("---")

    # --- 1. Metadata ---
    st.markdown("### 📝 Metadata")
    st.write(f"{'✅' if meta.get('description_present') else '❌'} **Description**")
    st.write(f"{'✅' if meta.get('tags_present') else '❌'} **Git Tags**")

    st.markdown("---")

    # --- 2. Documentation Files ---
    st.markdown("### 📄 Documentation Files")
    files_status = docs.get("files", {})
    if not files_status:
        st.info("Documentation check not available.")
    else:
        for doc, present in files_status.items():
            st.write(f"{'✅' if present else '❌'} **{doc}**")
        if docs.get("all_present"):
            st.success("All required documentation files are present.")
        else:
            missing = docs.get("missing", [])
            st.warning(f"Missing {len(missing)} required file(s): {', '.join(missing)}")

    st.markdown("---")

    # --- 3. Repository Health Files ---
    st.markdown("### 🗂 Repository Health Files")
    repo_files = report.get("repo_files", {})
    rf_files = repo_files.get("files", {})
    if not rf_files:
        st.info("Repository health file check not available.")
    else:
        score = repo_files.get("score", 0)
        st.caption(
            f"Score: {score}% ({len(rf_files) - len(repo_files.get('missing', []))}/{len(rf_files)} files present)"
        )
        for filename, info in rf_files.items():
            icon = "✅" if info["present"] else "❌"
            st.write(f"{icon} **{filename}** — {info['reason']}")
        if repo_files.get("all_present"):
            st.success("All repository health files are present.")
        else:
            missing = repo_files.get("missing", [])
            st.warning(f"Missing {len(missing)} file(s): {', '.join(missing)}")

    st.markdown("---")

    # --- 4. Quality & Tools ---
    st.markdown("### 🛠 Quality & Tools")
    tools = report.get("tools", {}).get("quality_tools", {})
    if tools:
        for tool, present in tools.items():
            st.write(f"{'✅' if present else '❌'} **{tool.title()}**")
    else:
        st.info("No quality tools detected for this project type.")

    st.markdown("---")

    # --- 5. Security ---
    st.markdown("### 🔒 Security")
    sec = report.get("tools", {}).get("security", {})
    st.write(f"{'✅' if sec.get('secret_scanning') else '❌'} **Secret Scanning** (Gitleaks/TruffleHog)")
    st.write(f"{'✅' if sec.get('dependency_audit') else '❌'} **Dependency Audit** (uv audit/pip-audit/npm audit)")
    if "bandit" in sec:
        st.write(f"{'✅' if sec.get('bandit') else '❌'} **Static Analysis** (Bandit)")

    st.markdown("---")

    # --- 6. Testing ---
    st.markdown("### 🧪 Testing")
    test = report.get("tools", {}).get("testing", {})
    st.write(f"{'✅' if test.get('pytest') or test.get('jest_vitest') else '❌'} **Test Framework**")
    st.write(f"{'✅' if test.get('coverage') else '❌'} **Coverage Reporting**")
    st.write(f"{'✅' if test.get('coverage_threshold') else '🔍'} **Enforced Thresholds** (fail-under)")

    st.markdown("---")

    # --- 7. Automation & CI ---
    st.markdown("### 🤖 Automation & CI")
    auto = report.get("tools", {}).get("automation", {})
    st.write(f"{'✅' if auto.get('gitlab_ci') else '❌'} **GitLab CI Pipeline**")
    st.write(f"{'✅' if auto.get('pre_commit') else '❌'} **Pre-commit Hooks**")
    st.write(f"{'✅' if auto.get('git_cliff') else '❌'} **Automated Changelog** (Git-Cliff)")
    if report.get("dx_ci"):
        st.markdown("---")
        render_dx_ci_pipeline_ui(report["dx_ci"])
    if report.get("precommit"):
        st.markdown("---")
        render_precommit_analysis_ui(report["precommit"])

    st.markdown("---")

    # --- 8. Spec-Kit (Spec-Driven Development) ---
    st.markdown("### 📐 Spec-Kit (Spec-Driven Development)")
    speckit = report.get("speckit", {})
    if speckit.get("error"):
        st.warning(f"Spec-Kit check failed: {speckit['error']}")
    else:
        sk_score = speckit.get("score", 0)
        sk_icon = "🟢" if sk_score == 100 else "🟡" if sk_score >= 50 else "🔴"
        st.caption(f"{sk_icon} Spec-Kit Score: {sk_score}%")

        col_a, col_b, col_c, col_d = st.columns(4)
        col_a.metric(".specify/ setup", "✅" if speckit.get("setup_present") else "❌")
        col_b.metric("constitution.md", "✅" if speckit.get("constitution_present") else "❌")
        col_c.metric("Templates", "✅" if speckit.get("templates_present") else "❌")
        col_d.metric("specs/ directory", "✅" if speckit.get("specs_dir_present") else "❌")

        core_files = speckit.get("core_files", {})
        if core_files:
            with st.expander("📁 Core File Details"):
                for filepath, present in core_files.items():
                    st.write(f"{'✅' if present else '❌'} `{filepath}`")

        spec_features = speckit.get("spec_features", [])
        if spec_features:
            complete = speckit.get("complete_specs_count", 0)
            total = len(spec_features)
            with st.expander(f"📋 Feature Specs — {complete}/{total} complete"):
                for feat in spec_features:
                    status = "✅" if feat["complete"] else "⚠️"
                    st.markdown(f"{status} **{feat['name']}**")
                    for req_file, present in feat["files"].items():
                        st.write(f"  {'✅' if present else '❌'} `{req_file}`")
        elif speckit.get("setup_present"):
            st.info("No feature specs found under `specs/`. Create `specs/<feature>/spec.md`, `plan.md`, `tasks.md` to start using SDD.")

    st.markdown("---")

    # --- 9. Suggestions ---
    st.markdown("### 📌 Actionable Compliance Suggestions")
    sugs = get_dx_suggestions(report)
    if not sugs:
        st.success("Your project compliance is absolutely perfect! No suggestions.")
    else:
        for s in sugs:
            with st.expander(f"❌ {s['item']} — {s['reason']}"):
                st.markdown(f"**How to fix:** {s['action']}")


def render_compliance_mode(gl_client):
    st.subheader("🔍 Project Compliance Analysis")

    tabs = st.tabs(["Single Project", "Batch Projects"])

    with tabs[0]:
        st.markdown("#### Check a Single Project")

        # Step 1: Input Project
        project_input = st.text_input(
            "Enter Project ID or URL", placeholder="https://gitlab.com/group/project", key="single_project_input"
        )

        col1, col2 = st.columns([1, 2])

        with col1:
            fetch_project = st.button("Fetch Project & Branches", key="fetch_project_btn")

        # Step 2: Branch Selection (Intermediate Stage)
        if fetch_project or st.session_state.get("current_project_id") == project_input:
            try:
                if fetch_project:
                    with st.spinner("Fetching branches..."):
                        pid = extract_path_from_url(project_input)
                        project = cached_get_project(gl_client, pid)
                        if not isinstance(project, dict) or not project.get("id"):
                            st.error("Project not found. Check the URL or project ID, and ensure the token has access.")
                            st.session_state.pop("current_project_id", None)
                            st.stop()
                        st.session_state["current_project_obj"] = project
                        st.session_state["current_project_id"] = project_input
                        st.session_state["project_branches"] = get_project_branches(gl_client, project["id"])

                project = st.session_state.get("current_project_obj")
                branches = st.session_state.get("project_branches", [])

                if project:
                    st.success(f"Project found: **{project.get('name_with_namespace')}**")

                    default_branch = project.get("default_branch", "main")
                    default_idx = branches.index(default_branch) if default_branch in branches else 0

                    selected_branch = st.selectbox(
                        "Select Branch for Analysis",
                        options=branches,
                        index=default_idx,
                        key="selected_branch_dropdown",
                    )

                    if st.button("Run Compliance Analysis", key="run_analysis_single"):
                        with st.spinner(f"Analyzing branch '{selected_branch}'..."):
                            report = cached_run_compliance(gl_client, project["id"], selected_branch)
                            render_project_compliance_details(report)

            except Exception as e:
                st.error(f"Error: {e}")
                if "current_project_id" in st.session_state:
                    del st.session_state["current_project_id"]

    with tabs[1]:
        st.markdown("#### Batch Check Multiple Projects")
        render_batch_project_compliance_internal(gl_client)


def render_batch_project_compliance_internal(gl_client):
    project_input = st.text_area(
        "Enter Project IDs or URLs (one per line)",
        height=150,
        placeholder="https://gitlab.com/group/project1\n12345\n...",
    )

    b_col1, b_col2 = st.columns([2, 3])
    with b_col1:
        branch_input = st.text_input(
            "Branch to analyse (applied to all projects)",
            value="main",
            placeholder="main",
            help="If a project does not have this branch, its default branch will be used instead.",
            key="batch_branch_input",
        )
    with b_col2:
        st.markdown("&nbsp;", unsafe_allow_html=True)  # spacer to align button
        common_branches = ["main", "master", "dev", "develop", "staging"]
        st.caption(f"Common branches: {', '.join(f'`{b}`' for b in common_branches)}")

    selected_branch = branch_input.strip() or "main"

    if st.button("Run Batch Analysis", key="run_batch_btn"):
        lines = [line.strip() for line in project_input.splitlines() if line.strip()]
        if not lines:
            st.warning("Please enter at least one project.")
            return

        results = []
        progress_bar = st.progress(0)

        def _process_line(line):
            try:
                pid = extract_path_from_url(line)
                project = cached_get_project(gl_client, pid)

                # Use selected branch; fall back to project default if it doesn't exist
                available_branches = get_project_branches(gl_client, project["id"])
                branch = (
                    selected_branch if selected_branch in available_branches else project.get("default_branch", "main")
                )

                report = cached_run_compliance(gl_client, project["id"], branch)
                name = project.get("name_with_namespace", str(line))
                summary = {
                    "name": name,
                    "branch": branch,
                    "score": report.get("dx_score", 0),
                    "stack": report.get("tools", {}).get("project_type", "Unknown"),
                    "agplv3": report["license"].get("valid", False),
                    "security": report["tools"]["security"].get("secret_scanning", False),
                    "coverage": report["tools"]["testing"].get("coverage", False),
                    "ci": report["tools"]["automation"].get("gitlab_ci", False),
                    "precommit": report["tools"]["automation"].get("pre_commit", False),
                }
                return {"summary": summary, "report": report, "error": None}
            except Exception as e:
                return {"summary": {"name": line, "score": 0}, "report": None, "error": str(e)}

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_line = {executor.submit(_process_line, line): line for line in lines}
            for i, future in enumerate(concurrent.futures.as_completed(future_to_line)):
                results.append(future.result())
                progress_bar.progress((i + 1) / len(lines))

        if not results:
            return

        st.markdown(f"### 📊 Batch Compliance Summary — branch: `{selected_branch}`")

        for item in results:
            summary = item["summary"]
            report = item["report"]
            error = item["error"]
            name = summary.get("name", "Unknown")

            with st.container(border=True):
                if error:
                    st.error(f"**{name}** — {error}")
                    continue

                score = summary["score"]
                score_icon = "🟢" if score >= 75 else "🟡" if score >= 40 else "🔴"

                # --- Row 1: project name + branch + score + stack ---
                r1_col1, r1_col2, r1_col3, r1_col4 = st.columns([5, 1, 1, 1])
                r1_col1.markdown(f"#### {score_icon} {name}")
                r1_col2.metric("Branch", summary.get("branch", "main"))
                r1_col3.metric("Score", f"{score}%")
                r1_col4.metric("Stack", summary.get("stack", "—"))

                # --- Row 2: compliance metric badges ---
                m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
                m_col1.metric("AGPLv3", "✅" if summary["agplv3"] else "❌")
                m_col2.metric("Security", "✅" if summary["security"] else "❌")
                m_col3.metric("Coverage", "✅" if summary["coverage"] else "❌")
                m_col4.metric("CI/CD", "✅" if summary["ci"] else "❌")
                m_col5.metric("Pre-commit", "✅" if summary["precommit"] else "❌")

                # --- Expandable full report ---
                with st.expander("📋 View Full Compliance Report"):
                    if report:
                        render_project_compliance_details(report)
                    else:
                        st.warning("Report data not available.")
