import random
from datetime import datetime

class StrategyManager:
    """
    Manages capital allocation logic for a specific deployment.
    Calculates 80/20 profit splits and simulates protocol rebalancing.
    """
    def __init__(self, principal, target_apy=0.0582):
        self.principal = principal
        self.target_apy = target_apy
        self.user_net_profit = 0.0
        self.founder_fees_collected = 0.0
        self.start_time = datetime.now()
        self.allocation = {"Lending": 70, "Liquidity": 30}

    def calculate_tick(self, seconds=10):
        """Calculates yield and splits for a 10-second window."""
        # Annual yield / seconds in year * window
        gross_yield = (self.principal * self.target_apy) / 31536000 * seconds
        
        # The 20% Founder Cut (Vaultlogic's Revenue)
        fee = gross_yield * 0.20
        net = gross_yield - fee
        
        self.user_net_profit += net
        self.founder_fees_collected += fee
        
        # Simulate strategy shifts based on "market" conditions
        if random.random() > 0.8:
            new_lending = random.randint(60, 85)
            self.allocation = {"Lending": new_lending, "Liquidity": 100 - new_lending}
            return f"Strategy Optimized: Moved to {new_lending}% Lending / {100-new_lending}% LP"
        
        return None

class VaultLogicKernel:
    def __init__(self):
        self.active_deployments = {} # Map: WalletAddress -> StrategyManager

    def deploy(self, address, amount):
        self.active_deployments[address] = StrategyManager(amount)
        return f"KERNEL_ACTIVE: Deployment of ${amount:,.2f} confirmed for {address[:8]}..."

    def get_stats(self, address):
        if address not in self.active_deployments:
            return None
        strat = self.active_deployments[address]
        return {
            "principal": strat.principal,
            "net_profit": strat.user_net_profit,
            "founder_fees": strat.founder_fees_collected,
            "allocation": strat.allocation,
            "apy": strat.target_apy
        }

# Global Instance to be imported by main.py
kernel = VaultLogicKernel()