import asyncio
import json
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.abspath("./backend"))
from core.agent_tool.web import scrape_ecommerce_pricing

PROMPTS = [
    # 1. Price Benchmark (F&B)
    "dimsum mentai frozen bandung",
    
    # 2. Bulk/B2B Pricing (Manufacturing)
    "sablon kaos dtf per lusin jakarta"
]

ITERATIONS_PER_PROMPT = 1
REPORT_FILE = os.path.abspath("./backend/tests/ultimate_test_report.md")

async def run_single_test(prompt: str, iteration: int, prompt_idx: int) -> dict:
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚀 Running: '{prompt}' (Iter {iteration})")
    
    try:
        res = await scrape_ecommerce_pricing(prompt)
        
        raw_md = res.get("raw_markdown", "")
        raw_json = res.get("raw_llm_json", {})
        table_rows = res.get("table_rows", [])
        
        telemetry = res.get("telemetry", {})
        telemetry_md = ""
        if telemetry:
            for platform, tel_data in telemetry.items():
                telemetry_md += f"- **{platform}**:\n"
                for engine, status in tel_data.items():
                    icon = "✅" if "SUCCESS" in status else "⚠️" if "RATE_LIMITED" in status else "❌" if "FAILED" in status else "⏭️"
                    telemetry_md += f"  - {icon} {engine}: `{status}`\n"
                    
        return {
            "status": "SUCCESS",
            "table_rows": len(table_rows),
            "telemetry_md": telemetry_md,
            "raw_md_snippet": raw_md[:6000] + "\n...(truncated)",
            "raw_llm_json": json.dumps(raw_json, indent=2),
            "final_table_rows": json.dumps(table_rows, indent=2)
        }
    except Exception as e:
        return {"status": "FAIL", "reason": str(e)}

async def run_all():
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# Ultimate Rigorous Extraction Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    for prompt_idx, prompt in enumerate(PROMPTS):
        with open(REPORT_FILE, "a", encoding="utf-8") as f:
            f.write(f"## Prompt {prompt_idx + 1}: `{prompt}`\n\n")
            
        for i in range(1, ITERATIONS_PER_PROMPT + 1):
            result = await run_single_test(prompt, i, prompt_idx)
            
            with open(REPORT_FILE, "a", encoding="utf-8") as f:
                f.write(f"### Iteration {i}\n")
                if result["status"] == "FAIL":
                    f.write(f"**❌ FAILED:** {result['reason']}\n\n")
                else:
                    t_rows = result['table_rows']
                    pass_rows = "✅" if t_rows > 0 else "❌"
                    f.write(f"- {pass_rows} **Table Rows Generated:** {t_rows}\n\n")
                    
                    f.write("#### 1. Search Engine Telemetry\n")
                    f.write(result.get('telemetry_md', 'No telemetry recorded.') + "\n\n")
                    
                    f.write("#### 2. Raw Scraped Data (Aggregated)\n")
                    f.write("```markdown\n" + result['raw_md_snippet'] + "\n```\n\n")
                    
                    f.write("#### 3. Raw Extraction (LLM Output)\n")
                    f.write("```json\n" + result['raw_llm_json'] + "\n```\n\n")
                    
                    f.write("#### 4. Final Normalized Table (Python Output)\n")
                    f.write("```json\n" + result['final_table_rows'] + "\n```\n\n")
                    
    print(f"\n🎉 Extraction Test Suite Completed! Report saved to {REPORT_FILE}")

if __name__ == "__main__":
    asyncio.run(run_all())
