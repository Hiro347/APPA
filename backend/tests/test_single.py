import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.abspath("./backend"))
from core.agent import handle_chat_stream

async def run_test():
    prompt = "berapa harga pasaran dimsum mentai di bandung?"
    print(f"🚀 Running single test for: '{prompt}'")
    
    generator = handle_chat_stream("test_user_single", prompt)
    final_data = None
    
    async for chunk in generator:
        try:
            data = json.loads(chunk)
            if data.get("type") == "result":
                final_data = data.get("data")
        except:
            pass
            
    if not final_data:
        print("❌ FAILED: No final data returned")
        return
        
    artifacts = final_data.get("artifacts", [])
    if not artifacts:
        print("❌ FAILED: No artifacts found")
        return
        
    blocks = artifacts[0].get("blocks", [])
    text_blocks = [b for b in blocks if b.get("type") == "text"]
    table_blocks = [b for b in blocks if b.get("type") == "table"]
    checklist_blocks = [b for b in blocks if b.get("type") == "checklist"]
    
    print("\n" + "="*50)
    print("✅ PIPELINE COMPLETED. VALIDATING RESULTS...")
    print("="*50)
    
    txt_cnt = len(text_blocks)
    chk_cnt = len(checklist_blocks)
    t_rows = len(table_blocks[0].get("data", {}).get("rows", [])) if table_blocks else 0
    
    print(f"{'✅ PASS' if txt_cnt == 1 else '❌ FAIL'}: Exactly 1 text block found ({txt_cnt}).")
    if text_blocks:
        print(f"   Content Snippet: {text_blocks[0]['content'][:100]}...")
        
    print(f"{'✅ PASS' if chk_cnt == 0 else '❌ FAIL'}: 0 checklist blocks found ({chk_cnt}).")
    print(f"{'✅ PASS' if t_rows >= 5 else '❌ FAIL'}: Table has {t_rows} rows (>= 5).")
    
    if text_blocks:
        print("\n📝 FULL TEXT BLOCK GENERATED:\n")
        print(text_blocks[0]['content'])

if __name__ == "__main__":
    asyncio.run(run_test())
