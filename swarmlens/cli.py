from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from . import __version__
from .dashboard.server import serve_report
from .engine.analyzer import analyze_case, explain_account
from .io.loaders import load_case, validate_case
from .reporting.html_writer import write_html
from .reporting.json_writer import write_json


def _print_summary(report: dict) -> None:
    s = report["summary"]
    print(f"\nSwarmLens {__version__}")
    print(f"Case: {s['case_name']}")
    print(f"Accounts: {s['accounts']} | Posts: {s['posts']} | Interactions: {s['interactions']}")
    print(f"High-risk accounts: {s['high_risk_accounts']}")
    print(f"Coordinated clusters: {s['coordinated_clusters']}")
    print(f"Campaign score: {s['campaign_score']} ({s['campaign_grade']})")

def cmd_scan(args: argparse.Namespace) -> int:
    data = load_case(args.case_dir)
    validation = validate_case(data)
    if not validation["ok"]:
        print("[!] Validation failed")
        for issue in validation["issues"]:
            print(f" - {issue}")
        return 2
    out_dir = Path(args.output)
    if out_dir.exists() and args.clean:
        shutil.rmtree(out_dir)
    report = analyze_case(data, case_name=Path(args.case_dir).name)
    write_json(report, out_dir)
    write_html(report, out_dir)
    _print_summary(report)
    print(f"[+] JSON report: {out_dir / 'report.json'}")
    print(f"[+] HTML report: {out_dir / 'report.html'}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    data = load_case(args.case_dir)
    result = validate_case(data)
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 2


def cmd_explain(args: argparse.Namespace) -> int:
    report = json.loads(Path(args.report).read_text(encoding='utf-8'))
    result = explain_account(report, args.account_id)
    if not result:
        print(f"[!] account_id not found: {args.account_id}")
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_dashboard(args: argparse.Namespace) -> int:
    serve_report(args.report_dir, port=args.port, open_browser=not args.no_browser)
    return 0


def cmd_init_case(args: argparse.Namespace) -> int:
    src = Path(__file__).parent / 'demo_data' / 'case_alpha'
    dst = Path(args.output)
    dst.mkdir(parents=True, exist_ok=True)
    for name in ('accounts.csv', 'posts.csv', 'interactions.csv'):
        shutil.copy2(src / name, dst / name)
    print(f"[+] Demo case initialized in {dst}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog='swarmlens', description='SwarmLens - coordinated inauthentic behavior analysis toolkit')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    sub = parser.add_subparsers(dest='command', required=True)

    p_scan = sub.add_parser('scan', help='Analyze a case folder and generate reports')
    p_scan.add_argument('case_dir', help='Folder containing accounts/posts/interactions CSV or JSON files')
    p_scan.add_argument('-o', '--output', default='swarmlens-report', help='Output directory')
    p_scan.add_argument('--clean', action='store_true', help='Delete output directory before writing new report')
    p_scan.set_defaults(func=cmd_scan)

    p_run = sub.add_parser('run', help='Alias for scan with the same behavior')
    p_run.add_argument('case_dir')
    p_run.add_argument('-o', '--output', default='swarmlens-report')
    p_run.add_argument('--clean', action='store_true')
    p_run.set_defaults(func=cmd_scan)

    p_validate = sub.add_parser('validate', help='Validate case files before scanning')
    p_validate.add_argument('case_dir')
    p_validate.set_defaults(func=cmd_validate)

    p_explain = sub.add_parser('explain', help='Explain why a specific account was flagged')
    p_explain.add_argument('account_id')
    p_explain.add_argument('-r', '--report', default='swarmlens-report/report.json')
    p_explain.set_defaults(func=cmd_explain)

    p_dashboard = sub.add_parser('dashboard', help='Open a local interactive dashboard for a generated report')
    p_dashboard.add_argument('report_dir', nargs='?', default='swarmlens-report')
    p_dashboard.add_argument('--port', type=int, default=8765)
    p_dashboard.add_argument('--no-browser', action='store_true')
    p_dashboard.set_defaults(func=cmd_dashboard)

    p_init = sub.add_parser('init-case', help='Copy a ready-to-run demo dataset into a folder')
    p_init.add_argument('output', nargs='?', default='demo-case')
    p_init.set_defaults(func=cmd_init_case)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
