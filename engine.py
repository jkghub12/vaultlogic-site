import asyncio
from yieldscout import get_all_yields, evaluate_opportunity

async def run_alm_engine(wallet_address, log_callback=None):
    def log(m):
        if log_callback: log_callback(m)
        print(f"[ENGINE] {m}")

    log(f"Deterministic Engine Attached to {wallet_address[:8]}")
    current_pos = {"protocol": "AAVE V3", "apy": 2.87}
    
    while True:
        try:
            yields = await get_all_yields()
            best_opp = max(yields, key=lambda x: float(x['apy']))
            
            report = evaluate_opportunity(current_pos['apy'], best_opp['apy'])
            
            if report['is_viable']:
                log(f"Rebalance Triggered: {current_pos['protocol']} -> {best_opp['protocol']} (+{report['delta']}% Delta)")
                current_pos = best_opp
            else:
                log(f"Holding {current_pos['protocol']}. Target Delta ({report['delta']}%) below 5% threshold.")
                
        except Exception as e:
            log(f"Sensor Error: {str(e)}")
            
        await asyncio.sleep(600)