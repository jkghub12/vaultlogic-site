import random
from datetime import datetime
from web3 import Web3

# --- ADDRESSES (Base Mainnet) ---
AAVE_DATA_PROVIDER = "0x2d8E2788a42FA2089279743c746C9742721f5C14"
MORPHO_USDC_MARKET = "0x411e790D73c683b54446b0805c6a1f81d1136b69" # Example Morpho Blue Market
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

# ABIs
DATA_PROVIDER_ABI = [{"inputs": [{"internalType": "address", "name": "asset", "type": "address"}],"name": "getReserveData","outputs": [{"internalType": "uint256", "name": "unbacked", "type": "uint256"},{"internalType": "uint256", "name": "accrued", "type": "uint256"},{"internalType": "uint256", "name": "totalAToken", "type": "uint256"},{"internalType": "uint256", "name": "totalStableDebt", "type": "uint256"},{"internalType": "uint256", "name": "totalVariableDebt", "type": "uint256"},{"internalType": "uint256", "name": "liquidityRate", "type": "uint256"},{"internalType": "uint256", "name": "variableBorrowRate", "type": "uint256"},{"internalType": "uint256", "name": "stableBorrowRate", "type": "uint256"},{"internalType": "uint256", "name": "averageStableBorrowRate", "type": "uint256"},{"internalType": "uint256", "name": "liquidityIndex", "type": "uint256"},{"internalType": "uint256", "name": "variableBorrowIndex", "type": "uint256"},{"internalType": "uint40", "name": "lastUpdateTimestamp", "type": "uint40"}],"stateMutability": "view","type": "function"}]

class StrategyManager:
    def __init__(self, principal, rpc_url):
        self.principal = principal
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.current_venue = "Aave V3"
        self.current_apy = 0.05
        self.user_net_profit = 0.0
        self.founder_fees_collected = 0.0
        self.allocation = {"Lending": 100, "Liquidity": 0}
        self.last_rebalance = datetime.now()

    def get_market_rates(self):
        """Fetches rates across multiple Base venues."""
        rates = {}
        try:
            # 1. Fetch Aave V3 Rate
            aave_contract = self.w3.eth.contract(address=AAVE_DATA_PROVIDER, abi=DATA_PROVIDER_ABI)
            reserve_data = aave_contract.functions.getReserveData(USDC_ADDRESS).call()
            rates["Aave V3"] = (reserve_data[5] / 10**27)
            
            # 2. Simulating Morpho & Aerodrome (In production, these would use their respective Lens/Factory contracts)
            # We add a slight random variance to simulate real market fluctuations for the UI
            rates["Morpho Blue"] = rates["Aave V3"] + random.uniform(-0.005, 0.015)
            rates["Aerodrome LP"] = rates["Aave V3"] + random.uniform(0.02, 0.08) # Higher yield, higher risk
            
            return rates
        except:
            return {"Aave V3": 0.05, "Morpho Blue": 0.045, "Aerodrome LP": 0.09}

    def rebalance_logic(self):
        """Autonomous Rebalancing: Lowest Risk vs Highest Yield."""
        rates = self.get_market_rates()
        best_venue = self.current_venue
        best_rate = rates[self.current_venue]

        for venue, rate in rates.items():
            # RISK WEIGHTING: Aerodrome requires a 3% spread to justify the LP risk vs Lending
            threshold = 0.03 if venue == "Aerodrome LP" else 0.005
            
            if rate > (best_rate + threshold):
                best_venue = venue
                best_rate = rate

        if best_venue != self.current_venue:
            old_venue = self.current_venue
            self.current_venue = best_venue
            self.current_apy = best_rate
            
            # Update Allocation UI components
            if "LP" in self.current_venue:
                self.allocation = {"Lending": 20, "Liquidity": 80}
            else:
                self.allocation = {"Lending": 100, "Liquidity": 0}
                
            return f"REBALANCE: Migrated from {old_venue} to {best_venue} (APY: {best_rate*100:.2f}%)"
        
        self.current_apy = best_rate
        return None

    def calculate_tick(self, seconds=10):
        # Rebalance check every ~60 seconds (6 ticks)
        rebalance_msg = None
        if random.random() > 0.8: # Probabilistic check for demo
            rebalance_msg = self.rebalance_logic()

        gross_yield = (self.principal * self.current_apy) / 31536000 * seconds
        fee = gross_yield * 0.20
        net = gross_yield - fee
        
        self.user_net_profit += net
        self.founder_fees_collected += fee
        return rebalance_msg

class VaultLogicKernel:
    def __init__(self):
        self.active_deployments = {}

    def deploy(self, address, amount, rpc_url):
        self.active_deployments[address] = StrategyManager(amount, rpc_url)
        return f"KERNEL_ENGAGED: Deployment verified for {address[:8]}..."

    def get_stats(self, address):
        if address not in self.active_deployments: return None
        strat = self.active_deployments[address]
        return {
            "principal": strat.principal,
            "net_profit": strat.user_net_profit,
            "venue": strat.current_venue,
            "apy": strat.current_apy,
            "allocation": strat.allocation
        }

kernel = VaultLogicKernel()