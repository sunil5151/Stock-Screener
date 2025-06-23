import pandas as pd
import numpy as np

class Backtester:
    """Analyze signal performance and calculate accuracy metrics"""
    
    def __init__(self, signals):
        """Initialize with signals list or DataFrame"""
        if isinstance(signals, list):
            self.signals_df = pd.DataFrame(signals)
        elif isinstance(signals, pd.DataFrame):
            self.signals_df = signals.copy()
        else:
            raise ValueError("Signals must be a list or DataFrame")
        
        self.lookahead_bars = None
        print(f"Backtester initialized with {len(self.signals_df)} signals")
    
    def calculate_accuracy(self, lookahead_bars=None):
        """Calculate overall accuracy of signals with breakouts"""
        if self.signals_df.empty:
            return {
                'accuracy_rate': 0.0,
                'total_signals': 0,
                'accurate_signals': 0,
                'breakout_signals': 0
            }
        
        # Filter signals that have accuracy data (i.e., had breakouts and lookahead data)
        valid_signals = self.signals_df['Accuracy'].notna()
        
        if not valid_signals.any():
            return {
                'accuracy_rate': 0.0,
                'total_signals': len(self.signals_df),
                'accurate_signals': 0,
                'breakout_signals': 0
            }
        
        # Calculate accuracy metrics
        accurate_signals = self.signals_df.loc[valid_signals, 'Accuracy'].sum()
        total_valid = valid_signals.sum()
        accuracy_rate = (accurate_signals / total_valid) * 100 if total_valid > 0 else 0.0
        
        self.lookahead_bars = lookahead_bars
        
        results = {
            'accuracy_rate': accuracy_rate,
            'total_signals': len(self.signals_df),
            'breakout_signals': total_valid,
            'accurate_signals': int(accurate_signals),
            'inaccurate_signals': int(total_valid - accurate_signals)
        }
        
        print(f"Accuracy Analysis:")
        print(f"  Total signals: {results['total_signals']}")
        print(f"  Signals with breakouts: {results['breakout_signals']}")
        print(f"  Accurate signals: {results['accurate_signals']}")
        print(f"  Overall accuracy: {results['accuracy_rate']:.2f}%")
        
        return results
    
    def analyze_by_signal_type(self):
        """Analyze accuracy by signal type (LONG vs SHORT)"""
        if self.signals_df.empty:
            return {}
        
        results = {}
        
        for signal_type in ['LONG', 'SHORT']:
            type_signals = self.signals_df[self.signals_df['Type'] == signal_type]
            valid_signals = type_signals['Accuracy'].notna()
            
            if valid_signals.any():
                accurate = type_signals.loc[valid_signals, 'Accuracy'].sum()
                total_valid = valid_signals.sum()
                accuracy_rate = (accurate / total_valid) * 100 if total_valid > 0 else 0.0
            else:
                accurate = 0
                total_valid = 0
                accuracy_rate = 0.0
            
            results[signal_type] = {
                'total_signals': len(type_signals),
                'breakout_signals': int(total_valid),
                'accurate_signals': int(accurate),
                'accuracy_rate': accuracy_rate
            }
        
        return results
    
    def get_performance_metrics(self):
        """Get detailed performance metrics"""
        if self.signals_df.empty:
            return {}
        
        # Basic counts
        total_signals = len(self.signals_df)
        signals_with_breakout = len(self.signals_df[self.signals_df['Breakout_Time'].notna()])
        signals_with_volume = len(self.signals_df[self.signals_df['Volume_Spike_Time'].notna()])
        signals_with_big_candle = len(self.signals_df[self.signals_df['Big_Candle_Time'].notna()])
        signals_with_sr_confirm = len(self.signals_df[self.signals_df['SR_Confirmed'] == True])
        sr_confirmation_rate = (signals_with_sr_confirm / total_signals) * 100 if total_signals > 0 else 0
        
        # Calculate confirmation rates
        volume_confirmation_rate = (signals_with_volume / total_signals) * 100 if total_signals > 0 else 0
        candle_confirmation_rate = (signals_with_big_candle / total_signals) * 100 if total_signals > 0 else 0
        breakout_rate = (signals_with_breakout / total_signals) * 100 if total_signals > 0 else 0
        
        # Price movement analysis for breakout signals
        breakout_signals = self.signals_df[self.signals_df['Breakout_Time'].notna()]
        avg_price_change = 0.0
        
        if not breakout_signals.empty:
            price_changes = []
            for _, signal in breakout_signals.iterrows():
                if pd.notna(signal['Price_After_n']) and pd.notna(signal['Breakout_Price']):
                    change = signal['Price_After_n'] - signal['Breakout_Price']
                    if signal['Type'] == 'SHORT':
                        change = -change  # For shorts, we want price to go down
                    price_changes.append(change)
            
            if price_changes:
                avg_price_change = np.mean(price_changes)
        
        return {
            'total_signals': total_signals,
            'breakout_rate': breakout_rate,
            'volume_confirmation_rate': volume_confirmation_rate,
            'candle_confirmation_rate': candle_confirmation_rate,
            'avg_price_change': avg_price_change,
            'signals_with_all_confirmations': self._count_full_confirmations(),
            'sr_confirmation_rate': sr_confirmation_rate,
            'signals_with_sr_confirmation': signals_with_sr_confirm,
        }
    
    def _count_full_confirmations(self):
        """Count signals with all confirmations (volume spike + big candle + breakout)"""
        if self.signals_df.empty:
            return 0
        
        full_confirmations = (
            self.signals_df['Volume_Spike_Time'].notna() & 
            self.signals_df['Big_Candle_Time'].notna() & 
            self.signals_df['Breakout_Time'].notna()
        ).sum()
        
        return int(full_confirmations)
    def get_best_signals(self, min_confirmations=2):

        """Get signals with minimum number of confirmations"""
        if self.signals_df.empty:
            return pd.DataFrame()
        
        # Count confirmations for each signal
        confirmations = (
            self.signals_df['Volume_Spike_Time'].notna().astype(int) +
            self.signals_df['Big_Candle_Time'].notna().astype(int) +
            self.signals_df['Breakout_Time'].notna().astype(int)
        )
        
        best_signals = self.signals_df[confirmations >= min_confirmations].copy()
        best_signals['Confirmation_Count'] = confirmations[confirmations >= min_confirmations]
        
        # Include SR_Confirmed in the output columns
        columns_to_show = [
            'Type', 'Cross_Time', 'Breakout_Time', 'Accuracy',
            'Confirmation_Count', 'SR_Confirmed', 'SR_Level_Broken'
        ]
        # Only include columns that exist in the DataFrame
        columns_to_show = [col for col in columns_to_show if col in best_signals.columns]
        
        return best_signals.sort_values('Confirmation_Count', ascending=False)[columns_to_show]
    

    
    def print_detailed_report(self, lookahead_bars=None):
        """Print a comprehensive backtest report"""
        print("\n" + "="*50)
        print("BACKTESTING REPORT")
        print("="*50)
        
        # Overall accuracy
        accuracy_results = self.calculate_accuracy(lookahead_bars)
        print(f"\nOVERALL PERFORMANCE:")
        print(f"Accuracy Rate: {accuracy_results['accuracy_rate']:.2f}%")
        
        # By signal type
        type_analysis = self.analyze_by_signal_type()
        print(f"\nBY SIGNAL TYPE:")
        for signal_type, metrics in type_analysis.items():
            print(f"{signal_type}:")
            print(f"  Accuracy: {metrics['accuracy_rate']:.2f}%")
            print(f"  Breakout signals: {metrics['breakout_signals']}")
        
        # Performance metrics
        perf_metrics = self.get_performance_metrics()
        print(f"\nCONFIRMATION ANALYSIS:")
        print(f"Breakout rate: {perf_metrics['breakout_rate']:.1f}%")
        print(f"Volume confirmation rate: {perf_metrics['volume_confirmation_rate']:.1f}%")
        print(f"Big candle confirmation rate: {perf_metrics['candle_confirmation_rate']:.1f}%")
        print(f"Signals with all confirmations: {perf_metrics['signals_with_all_confirmations']}")
        
        # Best signals
        best_signals = self.get_best_signals(min_confirmations=2)
        print(f"\nHIGH-QUALITY SIGNALS (2+ confirmations): {len(best_signals)}")
        print(f"S/R confirmation rate: {perf_metrics['sr_confirmation_rate']:.1f}%")
        print(f"Signals with S/R confirmation: {perf_metrics['signals_with_sr_confirmation']}")
        
        print("="*50)
    
    def get_signals_dataframe(self):
        """Return the signals DataFrame"""
        return self.signals_df.copy()