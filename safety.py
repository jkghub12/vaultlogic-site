import time

# 1. Define the class FIRST
class VaultlogicSafety:
    def __init__(self):
        self.MIN_TVL = 5_000_000  
        self.MAX_SLIPPAGE = 0.005 
        self.MIN_REAL_YIELD_RATIO = 0.70  
        
    def is_pool_whale_proof(self, pool):
        if pool['tvl'] < self.MIN_TVL:
            return False, f"TVL too low: ${pool['tvl']:,}"

        total_apy = pool.get('apy', 0)
        fee_apy = pool.get('fee_apy', 0)
        
        if total_apy > 0:
            real_yield_ratio = fee_apy / total_apy
            if real_yield_ratio < self.MIN_REAL_YIELD_RATIO:
                return False, f"Low quality yield ({real_yield_ratio*100:.1f}% fees)"
        
        return True, "Passed all safety checks"

# 2. Run the test SECOND
if __name__ == "__main__":
    guard = VaultlogicSafety()  # Now it knows what this is!

    trap_pool = {
        "pool_name": "ScamYield-USDC",
        "tvl": 100000,
        "apy": 150.0,
        "fee_apy": 5.0
    }

    print("--- Running Vaultlogic Safety Debugger ---")
    is_safe, reason = guard.is_pool_whale_proof(trap_pool)
    print(f"Result for {trap_pool['pool_name']}: {'✅ SAFE' if is_safe else '❌ REJECTED'} - {reason}")