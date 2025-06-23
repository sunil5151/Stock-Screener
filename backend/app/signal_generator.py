import pandas as pd
import numpy as np
from .technical_indicators import EnhancedSRDetector

class SignalGenerator:
    """Generate trading signals based on technical indicators"""
    
    def __init__(self, df, indicators_obj):
        """Initialize with dataframe and technical indicators object"""
        if df is None or df.empty:
            raise ValueError("DataFrame cannot be None or empty")
        
        self.df = df.copy()
        self.indicators = indicators_obj
        self.signals = []
        
        print(f"SignalGenerator initialized with {len(self.df)} rows")
    
    def scan_for_signals(self, confirmation_bars=7, lookahead_bars=5, volspike_lookahead=12):
        """
        Scan for potential trading signals.
        Only create a signal if a volume spike occurs within volspike_lookahead candles after the crossover.
        """
        print(f"Scanning for signals...")
        print(f"Confirmation window: {confirmation_bars} bars")
        print(f"Lookahead window: {lookahead_bars} bars")
        print(f"Volume spike lookahead: {volspike_lookahead} bars")

        self.signals = []

        for i in range(1, len(self.df)):
            # LONG SIGNALS - Look for bullish crossover
            if self.df['Bullish_Cross'].iloc[i - 1]:
                volspike_idx = None
                # Look for volume spike in next volspike_lookahead candles
                for j in range(i, min(i + volspike_lookahead, len(self.df))):
                    if self.df['VolSpike'].iloc[j]:
                        volspike_idx = j
                        break
                if volspike_idx is not None:
                    signal = self._process_long_signal(i, confirmation_bars, lookahead_bars, volspike_idx)
                    if signal:
                        self.signals.append(signal)

            # SHORT SIGNALS - Look for bearish crossover
            if self.df['Bearish_Cross'].iloc[i - 1]:
                volspike_idx = None
                for j in range(i, min(i + volspike_lookahead, len(self.df))):
                    if self.df['VolSpike'].iloc[j]:
                        volspike_idx = j
                        break
                if volspike_idx is not None:
                    signal = self._process_short_signal(i, confirmation_bars, lookahead_bars, volspike_idx)
                    if signal:
                        self.signals.append(signal)

        print(f"Found {len(self.signals)} potential signals")
        return self.signals
    
    def _process_long_signal(self, start_idx, confirmation_bars, lookahead_bars, volspike_idx=None):
        """Process a potential long signal"""
        cross_time = self.df.index[start_idx - 1]
        cross_idx = start_idx - 1
        cross_price = self.df['Close'].iloc[cross_idx]
        
        signal_data = {
            'Type': 'LONG',
            'Cross_Time': cross_time,
            'Volume_Spike_Time': self.df.index[volspike_idx] if volspike_idx is not None else None,
            'Cross_Index': self.df.index[start_idx - 1],
            'Cross_Price': cross_price,
            'Big_Candle_Time': None,
            'Breakout_Time': None,
            'Breakout_Price': None,
            'Price_After_n': None,
            'Accuracy': None
        }
        
        # Look for confirmations and breakout within confirmation_bars
        for j in range(start_idx, min(start_idx + confirmation_bars, len(self.df))):
            
            # Capture first volume spike
            if signal_data['Volume_Spike_Time'] is None and self.df['VolSpike'].iloc[j]:
                signal_data['Volume_Spike_Time'] = self.df.index[j]
            
            # Capture first big candle
            if signal_data['Big_Candle_Time'] is None and self.df['BigCandle'].iloc[j]:
                signal_data['Big_Candle_Time'] = self.df.index[j]
            
            # Check for breakout above swing high
            swing_high = self.indicators.swing_high_at(j)
            if swing_high is not None and self.df['Close'].iloc[j] > swing_high:
                signal_data['Breakout_Time'] = self.df.index[j]
                signal_data['Breakout_Price'] = self.df['Close'].iloc[j]
                
                # Calculate accuracy using lookahead
                if j + lookahead_bars < len(self.df):
                    future_price = self.df['Close'].iloc[j + lookahead_bars]
                    signal_data['Price_After_n'] = future_price
                    signal_data['Accuracy'] = (future_price > signal_data['Breakout_Price'])
                
                # Check S/R breakout confirmation
                sr_confirmed, sr_level = self.check_sr_breakout_confirmation(j, 'LONG', lookahead=12)
                signal_data['SR_Confirmed'] = sr_confirmed
                signal_data['SR_Level_Broken'] = sr_level
                
                break
        
        return signal_data
    
    def _process_short_signal(self, start_idx, confirmation_bars, lookahead_bars, volspike_idx=None):
        """Process a potential short signal"""
        cross_time = self.df.index[start_idx - 1]
        
        signal_data = {
            'Type': 'SHORT',
            'Cross_Time': self.df.index[start_idx - 1],
            'Volume_Spike_Time': self.df.index[volspike_idx] if volspike_idx is not None else None,
            'Big_Candle_Time': None,
            'Breakout_Time': None,
            'Breakout_Price': None,
            'Price_After_n': None,
            'Accuracy': None
        }
        
        # Look for confirmations and breakout within confirmation_bars
        for j in range(start_idx, min(start_idx + confirmation_bars, len(self.df))):
            
            # Capture first volume spike
            if signal_data['Volume_Spike_Time'] is None and self.df['VolSpike'].iloc[j]:
                signal_data['Volume_Spike_Time'] = self.df.index[j]
            
            # Capture first big candle
            if signal_data['Big_Candle_Time'] is None and self.df['BigCandle'].iloc[j]:
                signal_data['Big_Candle_Time'] = self.df.index[j]
            
            # Check for breakout below swing low
            swing_low = self.indicators.swing_low_at(j)
            if swing_low is not None and self.df['Close'].iloc[j] < swing_low:
                signal_data['Breakout_Time'] = self.df.index[j]
                signal_data['Breakout_Price'] = self.df['Close'].iloc[j]
                
                # Calculate accuracy using lookahead
                if j + lookahead_bars < len(self.df):
                    future_price = self.df['Close'].iloc[j + lookahead_bars]
                    signal_data['Price_After_n'] = future_price
                    signal_data['Accuracy'] = (future_price < signal_data['Breakout_Price'])
                
                # Check S/R breakout confirmation
                sr_confirmed, sr_level = self.check_sr_breakout_confirmation(j, 'SHORT', lookahead=12)
                signal_data['SR_Confirmed'] = sr_confirmed
                signal_data['SR_Level_Broken'] = sr_level
                
                break
        
        return signal_data
    def track_signal_progression(self, signal_idx, signal_type):
        """Track the progression of a signal from cross to confirmation"""
        # Ensure signal_idx is an integer position
        if not isinstance(signal_idx, int):
            try:
                cross_candle = self.df.index.get_loc(signal_idx)
            except Exception:
                raise ValueError(f"Invalid signal_idx: {signal_idx}")
        else:
            cross_candle = signal_idx

        progression = {
            'cross_candle': cross_candle,
            'cross_time': self.df.index[cross_candle],
            'events_after_cross': []
        }

        # Track events in the next 10 candles after cross
        for i in range(1, 11):
            if cross_candle + i < len(self.df):
                candle_idx = cross_candle + i
                candle_events = []

                # Check for volume spike
                if self.df['VolSpike'].iloc[candle_idx]:
                    candle_events.append('Volume_Spike')

                # Check for big candle
                if self.df['BigCandle'].iloc[candle_idx]:
                    candle_events.append('Big_Candle')

                # Check for breakout
                breakout_result = self.check_breakout_at_candle(candle_idx, signal_type)
                if breakout_result['breakout_occurred']:
                    candle_events.append('Breakout')
                    progression['breakout_candle'] = candle_idx
                    progression['breakout_time'] = self.df.index[candle_idx]
                    progression['breakout_price'] = breakout_result['breakout_price']

                if candle_events:
                    progression['events_after_cross'].append({
                        'candle_after_cross': i,
                        'candle_number': candle_idx,
                        'timestamp': self.df.index[candle_idx],
                        'events': candle_events,
                        'price': self.df['Close'].iloc[candle_idx]
                    })

        return progression

    def check_breakout_at_candle(self, candle_idx, signal_type):
        """Check if breakout occurred at specific candle"""
        if signal_type.upper() == 'LONG':
            swing_high = self.indicators.swing_high_at(candle_idx)
            current_high = self.df['High'].iloc[candle_idx]
            if swing_high is not None and current_high > swing_high:
                return {
                    'breakout_occurred': True,
                    'breakout_price': current_high,
                    'swing_level_broken': swing_high
                }
        else:  # SHORT
            swing_low = self.indicators.swing_low_at(candle_idx)
            current_low = self.df['Low'].iloc[candle_idx]
            if swing_low is not None and current_low < swing_low:
                return {
                    'breakout_occurred': True,
                    'breakout_price': current_low,
                    'swing_level_broken': swing_low
                }
        return {'breakout_occurred': False}
    
    def check_sr_breakout_confirmation(self, signal_idx, direction, lookahead=12, num_levels=4):
        """
        Check if a support/resistance level is broken within the next `lookahead` candles after `signal_idx`.
        Uses EnhancedSRDetector for S/R levels.
        """
        sr_detector = EnhancedSRDetector(self.df)
        sr_data = sr_detector.get_top_sr_levels(num_levels=num_levels)
        supports = sr_data['supports']
        resistances = sr_data['resistances']

        confirmed = False
        broken_level = None

        cross_price = self.df['Close'].iloc[signal_idx]

        if direction == 'LONG':
            # Only consider resistance levels above the cross price
            relevant_resistances = [r for r in resistances if r['price'] > cross_price]
            for j in range(signal_idx + 1, min(signal_idx + 1 + lookahead, len(self.df))):
                for r in relevant_resistances:
                    # Confirm breakout above resistance
                    if self.df['High'].iloc[j] > r['price'] and cross_price < r['price']:
                        confirmed = True
                        broken_level = r['price']
                        return confirmed, broken_level
        elif direction == 'SHORT':
            # Only consider support levels below the cross price
            relevant_supports = [s for s in supports if s['price'] < cross_price]
            for j in range(signal_idx + 1, min(signal_idx + 1 + lookahead, len(self.df))):
                for s in relevant_supports:
                    # Confirm breakdown below support
                    if self.df['Low'].iloc[j] < s['price'] and cross_price > s['price']:
                        confirmed = True
                        broken_level = s['price']
                        return confirmed, broken_level

        return confirmed, broken_level

    def get_signals_dataframe(self):
        """Return signals as a pandas DataFrame"""
        if not self.signals:
            return pd.DataFrame()
        
        return pd.DataFrame(self.signals)
    
    def get_signal_summary(self):
        """Get summary statistics of signals"""
        if not self.signals:
            return "No signals generated"
        
        df_signals = self.get_signals_dataframe()
        
        long_signals = len(df_signals[df_signals['Type'] == 'LONG'])
        short_signals = len(df_signals[df_signals['Type'] == 'SHORT'])
        
        # Count signals with breakouts
        breakout_signals = len(df_signals[df_signals['Breakout_Time'].notna()])
        
        # Count signals with volume spikes
        volume_confirmations = len(df_signals[df_signals['Volume_Spike_Time'].notna()])
        
        # Count signals with big candles
        candle_confirmations = len(df_signals[df_signals['Big_Candle_Time'].notna()])
        
        return {
            'total_signals': len(self.signals),
            'long_signals': long_signals,
            'short_signals': short_signals,
            'signals_with_breakout': breakout_signals,
            'signals_with_volume_spike': volume_confirmations,
            'signals_with_big_candle': candle_confirmations
        }
    
    def filter_signals_with_breakout(self):
        """Return only signals that had a breakout"""
        if not self.signals:
            return []
        
        return [signal for signal in self.signals if signal['Breakout_Time'] is not None]
    
    def get_signals(self):
        """Return the raw signals list"""
        return self.signals
