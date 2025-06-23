import pandas as pd
import numpy as np

class TechnicalIndicators:
    """Calculate technical indicators for trading analysis"""
    def track_event_timings(self):
        """Track exact timing of all events"""
        self.event_log = []

        # Track volume spike timings
        if 'VolSpike' in self.df.columns:
            for idx in self.df[self.df['VolSpike']].index:
                self.event_log.append({
                    'event': 'Volume_Spike',
                    'candle_number': self.df.index.get_loc(idx),
                    'timestamp': idx,
                    'volume': self.df.loc[idx, 'Volume'],
                    'volume_ratio': self.df.loc[idx, 'Volume'] / self.df.loc[idx, 'AvgVol20'] if 'AvgVol20' in self.df.columns else None,
                    'price': self.df.loc[idx, 'Close']
                })

        # Track big candle timings
        if 'BigCandle' in self.df.columns:
            for idx in self.df[self.df['BigCandle']].index:
                self.event_log.append({
                    'event': 'Big_Candle',
                    'candle_number': self.df.index.get_loc(idx),
                    'timestamp': idx,
                    'body_size': self.df.loc[idx, 'Body'],
                    'body_ratio': self.df.loc[idx, 'Body'] / self.df.loc[idx, 'AvgBody20'] if 'AvgBody20' in self.df.columns else None,
                    'candle_type': 'Bullish' if self.df.loc[idx, 'Close'] > self.df.loc[idx, 'Open'] else 'Bearish',
                    'price': self.df.loc[idx, 'Close']
                })

    def get_event_at_candle(self, candle_number):
        """Get all events that occurred at specific candle"""
        return [event for event in getattr(self, 'event_log', []) if event['candle_number'] == candle_number]  
    def __init__(self, df):
        """Initialize with OHLCV dataframe"""
        if df is None or df.empty:
            raise ValueError("DataFrame cannot be None or empty")
        
        self.df = df.copy()
        print(f"TechnicalIndicators initialized with {len(self.df)} rows")
    
    def calculate_emas(self, fast_period=9, slow_period=15):
        """Calculate EMA crossovers and signals"""
        print(f"Calculating EMAs: {fast_period} and {slow_period} periods")
        
        # Calculate EMAs
        self.df[f'EMA{fast_period}'] = self.df['Close'].ewm(span=fast_period, adjust=False).mean()
        self.df[f'EMA{slow_period}'] = self.df['Close'].ewm(span=slow_period, adjust=False).mean()
        
        # Calculate previous values for crossover detection
        self.df[f'EMA{fast_period}_prev'] = self.df[f'EMA{fast_period}'].shift(1)
        self.df[f'EMA{slow_period}_prev'] = self.df[f'EMA{slow_period}'].shift(1)
        
        # Detect crossovers
        self.df['Bullish_Cross'] = (
            (self.df[f'EMA{fast_period}_prev'] <= self.df[f'EMA{slow_period}_prev']) &
            (self.df[f'EMA{fast_period}'] > self.df[f'EMA{slow_period}'])
        )
        
        self.df['Bearish_Cross'] = (
            (self.df[f'EMA{fast_period}_prev'] >= self.df[f'EMA{slow_period}_prev']) &
            (self.df[f'EMA{fast_period}'] < self.df[f'EMA{slow_period}'])
        )
        
        bullish_count = self.df['Bullish_Cross'].sum()
        bearish_count = self.df['Bearish_Cross'].sum()
        print(f"Found {bullish_count} bullish crossovers, {bearish_count} bearish crossovers")
        
        return self.df
    
    def calculate_all_indicators(self, ema_fast=9, ema_slow=15, 
                                big_candle_multiplier=1.5, big_candle_lookback=20,
                                volume_multiplier=1.5, volume_lookback=20,
                                swing_lookback=8):
        """Calculate all technical indicators at once"""
        print("Calculating all technical indicators...")

        self.calculate_emas(ema_fast, ema_slow)
        self.calculate_big_candles(multiplier=big_candle_multiplier, lookback_period=big_candle_lookback)
        self.calculate_volume_spikes(multiplier=volume_multiplier, lookback_period=volume_lookback)
        self.calculate_swing_points(swing_lookback)
        self.calculate_vwap()
        self.find_pivot_points()
        self.track_event_timings()
        print("All indicators calculated ✓")
        return self.df
    
    def calculate_big_candles(self, multiplier=2, lookback_period=10):
        """Identify big candles based on body size"""
        print(f"Calculating big candles (body > {multiplier}x {lookback_period}-bar average)")

        # Calculate candle body size
        self.df['Body'] = (self.df['Close'] - self.df['Open']).abs()

        # Calculate rolling average of body sizes, EXCLUDING the current candle
        self.df[f'AvgBody{lookback_period}'] = (
            self.df['Body'].rolling(window=lookback_period).mean().shift(1)
        )

        # Identify big candles
        self.df['BigCandle'] = self.df['Body'] > (multiplier * self.df[f'AvgBody{lookback_period}'])

        big_candle_count = self.df['BigCandle'].sum()
        print(f"Found {big_candle_count} big candles")

        return self.df

    def calculate_vwap(self):
        """Calculate Volume Weighted Average Price"""
        print("Calculating VWAP...")
        
        # Typical Price = (High + Low + Close) / 3
        self.df['Typical_Price'] = (self.df['High'] + self.df['Low'] + self.df['Close']) / 3
        
        # VWAP = Cumulative(Typical Price * Volume) / Cumulative(Volume)
        self.df['Price_Volume'] = self.df['Typical_Price'] * self.df['Volume']
        self.df['Cumulative_PV'] = self.df['Price_Volume'].cumsum()
        self.df['Cumulative_Volume'] = self.df['Volume'].cumsum()
        self.df['VWAP'] = self.df['Cumulative_PV'] / self.df['Cumulative_Volume']
        
        # Cleanup temporary columns
        self.df.drop(['Price_Volume', 'Cumulative_PV', 'Cumulative_Volume', 'Typical_Price'], 
                     axis=1, inplace=True)
        
        print("VWAP calculated ✓")
        return self.df

    def find_pivot_points(self, window=5):
        """Find pivot highs and lows"""
        print(f"Finding pivot points with window={window}")
        
        self.df['Pivot_High'] = self.df['High'].rolling(window=window*2+1, center=True).max() == self.df['High']
        self.df['Pivot_Low'] = self.df['Low'].rolling(window=window*2+1, center=True).min() == self.df['Low']
        
        return self.df

    def get_support_resistance_levels(self, num_levels=4):
        """Get top support and resistance levels based on pivot points"""
        print(f"Calculating top {num_levels} support and resistance levels")
        
        # Get pivot points
        pivot_highs = self.df[self.df['Pivot_High']]['High'].values
        pivot_lows = self.df[self.df['Pivot_Low']]['Low'].values
        
        # Sort and get top levels
        resistance_levels = sorted(pivot_highs, reverse=True)[:num_levels]
        support_levels = sorted(pivot_lows)[:num_levels]
        
        print(f"Found {len(resistance_levels)} resistance and {len(support_levels)} support levels")
        
        return {
            'resistance_levels': resistance_levels,
            'support_levels': support_levels
        }

    def calculate_volume_spikes(self, multiplier=2, lookback_period=10):
        """Identify volume spikes"""
        print(f"Calculating volume spikes (volume > {multiplier}x {lookback_period}-bar average)")
        
        # Calculate rolling average volume
        self.df[f'AvgVol{lookback_period}'] = self.df['Volume'].rolling(window=lookback_period).mean()
        
        # Identify volume spikes
        self.df['VolSpike'] = self.df['Volume'] > (multiplier * self.df[f'AvgVol{lookback_period}'])
        
        vol_spike_count = self.df['VolSpike'].sum()
        print(f"Found {vol_spike_count} volume spikes")
        
        return self.df

    def calculate_swing_points(self, lookback_bars=8):
        """Calculate swing highs and lows for breakout detection"""
        print(f"Calculating swing points with {lookback_bars}-bar lookback")
        
        def swing_high_at(df, index, lookback=lookback_bars):
            """Get swing high at specific index"""
            if index <= 0:
                return None
            start = max(0, index - lookback)
            slice_highs = df['High'].iloc[start:index]
            return slice_highs.max() if len(slice_highs) > 0 else None
        
        def swing_low_at(df, index, lookback=lookback_bars):
            """Get swing low at specific index"""
            if index <= 0:
                return None
            start = max(0, index - lookback)
            slice_lows = df['Low'].iloc[start:index]
            return slice_lows.min() if len(slice_lows) > 0 else None
        
        # Store functions as instance methods for use by other classes
        self.swing_high_at = lambda idx: swing_high_at(self.df, idx, lookback_bars)
        self.swing_low_at = lambda idx: swing_low_at(self.df, idx, lookback_bars)
        
        return self.df

    def get_data(self):
        """Return dataframe with calculated indicators"""
        return self.df.copy()

    def get_crossover_summary(self):
        """Get summary of crossover signals"""
        if 'Bullish_Cross' not in self.df.columns:
            return "No crossover data calculated"
        
        bullish_dates = self.df[self.df['Bullish_Cross']].index.tolist()
        bearish_dates = self.df[self.df['Bearish_Cross']].index.tolist()
        
        return {
            'bullish_crossovers': len(bullish_dates),
            'bearish_crossovers': len(bearish_dates),
            'bullish_dates': bullish_dates[:5],  # Show first 5
            'bearish_dates': bearish_dates[:5]   # Show first 5
        }
class EnhancedSRDetector:
    def __init__(self, df, lookback_window=8, merge_threshold=0.002):
        self.df = df.copy()
        self.lookback_window = lookback_window
        self.merge_threshold = merge_threshold
        self.sr_levels = []
        
    def detect_fractal_pivots(self):
        """
        Enhanced fractal detection using Bill Williams method
        with volume confirmation
        """
        window = self.lookback_window
        swing_highs = []
        swing_lows = []
        
        for i in range(window, len(self.df) - window):
            # Get the window of data around current bar
            window_data = self.df.iloc[i - window : i + window + 1]
            current_high = self.df['High'].iat[i]
            current_low = self.df['Low'].iat[i]
            current_vol = self.df['Volume'].iat[i]
            
            # Fractal High: current high is highest in the window
            if current_high == window_data['High'].max():
                # Volume confirmation: current volume should be above average
                avg_vol = window_data['Volume'].mean()
                volume_strength = current_vol / avg_vol if avg_vol > 0 else 1
                
                swing_highs.append({
                    'price': float(current_high),
                    'index': i,
                    'timestamp': self.df.index[i],
                    'volume_strength': volume_strength,
                    'type': 'resistance'
                })
            
            # Fractal Low: current low is lowest in the window  
            if current_low == window_data['Low'].min():
                avg_vol = window_data['Volume'].mean()
                volume_strength = current_vol / avg_vol if avg_vol > 0 else 1
                
                swing_lows.append({
                    'price': float(current_low),
                    'index': i,
                    'timestamp': self.df.index[i],
                    'volume_strength': volume_strength,
                    'type': 'support'
                })
        
        return swing_highs + swing_lows
    
    def calculate_pivot_points(self):
        """
        Calculate traditional pivot points for additional S/R levels
        """
        # Use last complete day/period for pivot calculation
        last_high = self.df['High'].iloc[-1]
        last_low = self.df['Low'].iloc[-1]
        last_close = self.df['Close'].iloc[-1]
        
        # Traditional Pivot Point formula
        pivot = (last_high + last_low + last_close) / 3
        
        # Support and Resistance levels
        r1 = (2 * pivot) - last_low
        r2 = pivot + (last_high - last_low)
        r3 = last_high + 2 * (pivot - last_low)
        
        s1 = (2 * pivot) - last_high
        s2 = pivot - (last_high - last_low)
        s3 = last_low - 2 * (last_high - pivot)
        
        pivot_levels = [
            {'price': float(r3), 'type': 'resistance', 'strength': 3, 'source': 'pivot_r3'},
            {'price': float(r2), 'type': 'resistance', 'strength': 2, 'source': 'pivot_r2'},
            {'price': float(r1), 'type': 'resistance', 'strength': 1, 'source': 'pivot_r1'},
            {'price': float(pivot), 'type': 'pivot', 'strength': 4, 'source': 'pivot'},
            {'price': float(s1), 'type': 'support', 'strength': 1, 'source': 'pivot_s1'},
            {'price': float(s2), 'type': 'support', 'strength': 2, 'source': 'pivot_s2'},
            {'price': float(s3), 'type': 'support', 'strength': 3, 'source': 'pivot_s3'},
        ]
        
        return pivot_levels
    
    def test_level_strength(self, level_price, tolerance=0.001):
        """
        Test how many times price has tested a level and with what volume
        """
        touches = 0
        total_volume = 0
        test_details = []
        
        for i in range(len(self.df)):
            high = self.df['High'].iat[i]
            low = self.df['Low'].iat[i] 
            volume = self.df['Volume'].iat[i]
            
            # Check if price tested the level (within tolerance)
            if (low <= level_price * (1 + tolerance) and 
                high >= level_price * (1 - tolerance)):
                touches += 1
                total_volume += volume
                test_details.append({
                    'index': i,
                    'timestamp': self.df.index[i],
                    'volume': volume
                })
        
        avg_volume_at_tests = total_volume / touches if touches > 0 else 0
        overall_avg_volume = self.df['Volume'].mean()
        volume_ratio = avg_volume_at_tests / overall_avg_volume if overall_avg_volume > 0 else 1
        
        return {
            'touches': touches,
            'volume_ratio': volume_ratio,
            'test_details': test_details
        }
    def track_event_timings(self):
        """Track exact timing of all events"""
        self.event_log = []

        # Track volume spike timings
        if 'VolSpike' in self.df.columns:
            for idx in self.df[self.df['VolSpike']].index:
                self.event_log.append({
                    'event': 'Volume_Spike',
                    'candle_number': self.df.index.get_loc(idx),
                    'timestamp': idx,
                    'volume': self.df.loc[idx, 'Volume'],
                    'volume_ratio': self.df.loc[idx, 'Volume'] / self.df.loc[idx, 'AvgVol20'] if f'AvgVol20' in self.df.columns else None,
                    'price': self.df.loc[idx, 'Close']
                })

        # Track big candle timings
        if 'BigCandle' in self.df.columns:
            for idx in self.df[self.df['BigCandle']].index:
                self.event_log.append({
                    'event': 'Big_Candle',
                    'candle_number': self.df.index.get_loc(idx),
                    'timestamp': idx,
                    'body_size': self.df.loc[idx, 'Body'],
                    'body_ratio': self.df.loc[idx, 'Body'] / self.df.loc[idx, 'AvgBody20'] if 'AvgBody20' in self.df.columns else None,
                    'candle_type': 'Bullish' if self.df.loc[idx, 'Close'] > self.df.loc[idx, 'Open'] else 'Bearish',
                    'price': self.df.loc[idx, 'Close']
                })

    def get_event_at_candle(self, candle_number):
        """Get all events that occurred at specific candle"""
        return [event for event in getattr(self, 'event_log', []) if event['candle_number'] == candle_number]

    def calculate_all_indicators(self, ema_fast=9, ema_slow=15, 
                                 big_candle_multiplier=1.5, big_candle_lookback=20,
                                 volume_multiplier=1.5, volume_lookback=20,
                                 swing_lookback=8):
        # ...existing code...
        self.track_event_timings()
        print("All indicators calculated ✓")
        return self.df
    
    def merge_and_score_levels(self, all_levels):
        """
        Merge nearby levels and score them based on multiple factors
        """
        # Sort levels by price
        all_levels.sort(key=lambda x: x['price'])
        
        merged_levels = []
        i = 0
        
        while i < len(all_levels):
            current_level = all_levels[i]
            cluster = [current_level]
            
            # Find all levels within merge threshold
            j = i + 1
            while j < len(all_levels):
                if (abs(all_levels[j]['price'] - current_level['price']) / 
                    current_level['price'] < self.merge_threshold):
                    cluster.append(all_levels[j])
                    j += 1
                else:
                    break
            
            # Calculate merged level properties
            avg_price = sum(level['price'] for level in cluster) / len(cluster)
            
            # Test the merged level strength
            strength_data = self.test_level_strength(avg_price)
            
            # Calculate composite strength score
            volume_score = min(strength_data['volume_ratio'], 3.0)  # Cap at 3x
            touch_score = min(strength_data['touches'], 10) / 10 * 5  # Max 5 points
            cluster_size_score = min(len(cluster), 5) / 5 * 2  # Max 2 points
            
            # Volume strength from fractals
            vol_strength_score = 0
            if cluster[0].get('volume_strength'):
                vol_strength_score = min(cluster[0]['volume_strength'], 2.0)
            
            composite_score = volume_score + touch_score + cluster_size_score + vol_strength_score
            
            merged_level = {
                'price': avg_price,
                'type': cluster[0]['type'],
                'strength_score': composite_score,
                'touches': strength_data['touches'],
                'volume_ratio': strength_data['volume_ratio'],
                'cluster_size': len(cluster),
                'test_details': strength_data['test_details']
            }
            
            merged_levels.append(merged_level)
            i = j
        
        return merged_levels
    
    def get_top_sr_levels(self, num_levels=4):
        """
        Get top support and resistance levels based on comprehensive analysis
        """
        # Get fractal pivots
        fractal_levels = self.detect_fractal_pivots()
        
        # Get pivot point levels  
        pivot_levels = self.calculate_pivot_points()
        
        # Combine all levels
        all_levels = fractal_levels + pivot_levels
        
        if not all_levels:
            raise RuntimeError("No support/resistance levels detected")
        
        # Merge and score levels
        merged_levels = self.merge_and_score_levels(all_levels)
        
        # Separate by type and sort by strength
        supports = [l for l in merged_levels if l['type'] == 'support']
        resistances = [l for l in merged_levels if l['type'] == 'resistance']
        
        supports.sort(key=lambda x: x['strength_score'], reverse=True)
        resistances.sort(key=lambda x: x['strength_score'], reverse=True)
        
        return {
            'supports': supports[:num_levels],
            'resistances': resistances[:num_levels],
            'all_levels': merged_levels
        }