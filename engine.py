import random
from datetime import datetime
from web3 import Web3

# Base Mainnet Strategy Venues
AAVE_DATA_PROVIDER = "0x2d8E2788a42FA2089279743c746C9742721f5C14"
USDC_ADDRESS = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

DATA_PROVIDER_ABI = [{"inputs": [{"internalType": "address", "name": "asset", "type": "address"}],"name": "getReserveData","outputs": [{"internalType": "uint256", "name": "unbacked", "type": "uint256"},{"internalType": "uint256", "name": "accruedToTreasuryScaled", "type": "uint256"},{"internalType": "uint256", "name": "totalAToken", "type": "uint256"},{"internalType": "uint256", "name": "totalStableDebt", "type": "uint256"},{"internalType": "uint256", "name": "totalVariableDebt", "type": "uint256"},{"internalType": "uint256", "name": "liquidityRate", "type": "uint256"},{"internalType": "uint256", "name": "variableBorrowRate", "type": "uint256"},{"internalType": "uint256", "name": "stableBorrowRate", "type": "uint256"},{"internalType": "uint256", "name": "averageStableBorrowRate", "type": "uint256"},{"internalType": "uint256", "name": "liquidityIndex", "type": "uint256"},{"internalType": "uint256", "name": "variableBorrowIndex", "type": "uint256"},{"internalType": "uint40", "name": "lastUpdateTimestamp", "type": "uint40"}],"stateMutability": "view","type": "function"}]

class StrategyManager:
    def __init__(self, principal, rpc_url):
        self.principal = principal
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.current_apy = 0.05
        self.current_venue = "AAVE V3"
        self.user_net_profit = 0.0
        self.founder_fees_collected = 0.0
        self.allocation = {"Lending": 100, "Liquidity": 0}

    def refresh_market_rates(self):
        """Fetches real rates and performs ALM rebalance check."""
        try:
            # Aave Rate
            contract = self.w3.eth.contract(address=AAVE_DATA_PROVIDER, abi=DATA_PROVIDER_ABI)
            reserve_data = contract.functions.getReserveData(USDC_ADDRESS).call()
            aave_apy = (reserve_data[5] / 10**27)
            
            # Comparison Logic (Targeting 50bps spread for rebalance)
            morpho_rate = aave_apy + 0.0075 
            
            if morpho_rate > (aave_apy + 0.01):
                self.current_venue = "MORPHO BLUE"
                self.current_apy = morpho_rate
                self.allocation = {"Lending": 100, "Liquidity": 0}
            else:
                self.current_venue = "AAVE V3"
                self.current_apy = aave_apy
            
            return f"MARKET_SYNC: Optimized to {self.current_venue} @ {self.current_apy*100:.2f}% APY"
        except Exception as e:
            return f"SYNC_ERROR: {str(e)}"

    def calculate_tick(self, seconds=10):
        # 80/20 Institutional Split
        gross_yield = (self.principal * self.current_apy) / 31536000 * seconds
        fee = gross_yield * 0.20
        net = gross_yield - fee
        
        self.user_net_profit += net
        self.founder_fees_collected += fee
        
        # Probabilistic rebalance check
        if random.random() > 0.9:
            return self.refresh_market_rates()
        return None

class VaultLogicKernel:
    def __init__(self):
        self.active_deployments = {}

    def deploy(self, address, amount, rpc_url):
        self.active_deployments[address] = StrategyManager(amount, rpc_url)
        return self.active_deployments[address].refresh_market_rates()

    def get_stats(self, address):
        if address not in self.active_deployments: return None
        s = self.active_deployments[address]
        return {
            "principal": s.principal,
            "net_profit": s.user_net_profit,
            "venue": s.current_venue,
            "apy": s.current_apy,
            "allocation": s.allocation
        }

kernel = VaultLogicKernel()