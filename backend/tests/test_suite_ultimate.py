import asyncio
import json
import sys
import os
import random
from datetime import datetime

sys.path.insert(0, os.path.abspath("./backend"))
from core.agent import handle_chat_stream

PROMPTS = [
    # 1. Price Benchmark (F&B)
    "berapa harga pasaran dimsum mentai di bandung?",
    
    # 2. Bulk/B2B Pricing (Manufacturing)
    "daftar harga sablon kaos dtf per lusin di jakarta",
    
    # 3. Service Pricing (Services)
    "pasaran harga cuci sepatu premium di yogyakarta",
    
    # 4. Rent/Asset Pricing (Real Estate)
    "perbandingan harga sewa ruko strategis di surabaya",
    
    # 5. Capital/Cost Pricing (General Business)
    "berapa modal bahan baku angkringan pinggir jalan?"
]

ITERATIONS_PER_PROMPT = 4
REPORT_FILE = os.path.abspath("./backend/tests/ultimate_test_report.md")

async def run_single_test(prompt: str, iteration: int, prompt_idx: int) -> dict:
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🚀 Running: '{prompt}' (Iter {iteration})")
    
    # Use a fresh user ID for each test to prevent profile state contamination
    test_user_id = f"test_user_{prompt_idx}_{iteration}_{int(datetime.now().timestamp())}"
    generator = handle_chat_stream(test_user_id, prompt)
    final_data = None
    
    async for chunk in generator:
        try:
            data = json.loads(chunk)
            if data.get("type") == "result":
                final_data = data.get("data")
        except:
            pass
            
    if not final_data:
        return {"status": "FAIL", "reason": "No final data returned"}
        
    artifacts = final_data.get("artifacts", [])
    if not artifacts:
        return {"status": "FAIL", "reason": "No artifacts found"}
        
    blocks = artifacts[0].get("blocks", [])
    text_blocks = [b for b in blocks if b.get("type") == "text"]
    table_blocks = [b for b in blocks if b.get("type") == "table"]
    checklist_blocks = [b for b in blocks if b.get("type") == "checklist"]
    
    return {
        "status": "SUCCESS",
        "text_count": len(text_blocks),
        "table_count": len(table_blocks),
        "checklist_count": len(checklist_blocks),
        "table_rows": len(table_blocks[0].get("data", {}).get("rows", [])) if table_blocks else 0,
        "text_content": text_blocks[0].get("content") if text_blocks else "",
        "table_content": json.dumps(table_blocks[0].get("data", {}).get("rows", []), indent=2) if table_blocks else ""
    }

async def run_all():
    os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
    
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("# Ultimate 20x Test Suite Report\n\n")
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
                    txt_cnt = result['text_count']
                    chk_cnt = result['checklist_count']
                    
                    pass_rows = "✅" if t_rows >= 5 else "❌"
                    pass_txt = "✅" if txt_cnt == 1 else "❌"
                    pass_chk = "✅" if chk_cnt == 0 else "❌"
                    
                    f.write(f"- {pass_rows} **Table Rows:** {t_rows} (Expected >= 5)\n")
                    f.write(f"- {pass_txt} **Text Blocks:** {txt_cnt} (Expected 1)\n")
                    f.write(f"- {pass_chk} **Checklists:** {chk_cnt} (Expected 0)\n\n")
                    
                    f.write("**Analytical Explanation Block:**\n")
                    f.write("```markdown\n" + result['text_content'] + "\n```\n\n")
                    
                    f.write("**Extracted Table Rows:**\n")
                    f.write("```json\n" + result['table_content'] + "\n```\n\n")
                    
            if not (prompt_idx == len(PROMPTS)-1 and i == ITERATIONS_PER_PROMPT):
                delay = random.uniform(5.0, 15.0)
                print(f"   [Jitter] Sleeping for {delay:.2f} seconds...")
                await asyncio.sleep(delay)
                
    print(f"\n🎉 20x Test Suite Completed! Report saved to {REPORT_FILE}")

if __name__ == "__main__":
    asyncio.run(run_all())
