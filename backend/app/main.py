"""
Main Trading System - Orchestrates all components
Run this file to execute the complete trading analysis
"""
from .technical_indicators import EnhancedSRDetector
from .data_processor import DataProcessor
from .technical_indicators import TechnicalIndicators
from .signal_generator import SignalGenerator
from .backtester import Backtester
from .chart_builder import ChartBuilder
from .signal_table import SignalTable
class TradingSystem:
    """Main trading system that orchestrates all components"""
    
    def __init__(self):
        self.data_processor = None
        self.indicators = None
        self.signal_generator = None
        self.backtester = None
        self.chart_builder = None
        
        self.df = None
        self.signals = None
        
        print("Trading System initialized ✓")
    
    def load_and_process_data(self, file_path):
        """Load and process market data"""
        print(f"\n--- LOADING DATA ---")
        
        self.data_processor = DataProcessor()
        self.df = self.data_processor.process_data(file_path)
        
        print(f"Data processing complete: {len(self.df)} rows loaded")
        return self.df
    
    def calculate_indicators(self, ema_fast=9, ema_slow=15, big_candle_multiplier=2, big_candle_lookback=10, volume_multiplier=2, volume_lookback=10, swing_lookback=8):
        """Calculate all technical indicators"""
        print(f"\n--- CALCULATING INDICATORS ---")
        
        if self.df is None:
            raise ValueError("Load data first using load_and_process_data()")
        
        self.indicators = TechnicalIndicators(self.df)
        self.df = self.indicators.calculate_all_indicators(
            ema_fast=ema_fast,
            ema_slow=ema_slow,
            big_candle_multiplier=big_candle_multiplier,
            big_candle_lookback=big_candle_lookback,
            volume_multiplier=volume_multiplier,
            volume_lookback=volume_lookback,
            swing_lookback=swing_lookback
        )
        
        # Print indicator summary
        summary = self.indicators.get_crossover_summary()
        print(f"Indicator calculation complete:")
        print(f"  Bullish crossovers: {summary['bullish_crossovers']}")
        print(f"  Bearish crossovers: {summary['bearish_crossovers']}")
        
        return self.df
    
    def generate_signals(self, confirmation_bars=7, lookahead_bars=5):
        """Generate trading signals"""
        print(f"\n--- GENERATING SIGNALS ---")
        
        if self.indicators is None:
            raise ValueError("Calculate indicators first using calculate_indicators()")
        
        self.signal_generator = SignalGenerator(self.df, self.indicators)
        self.signals = self.signal_generator.scan_for_signals(
            confirmation_bars=confirmation_bars,
            lookahead_bars=lookahead_bars
        )
        
        # Print signal summary
        summary = self.signal_generator.get_signal_summary()
        print(f"Signal generation complete:")
        print(f"  Total signals: {summary['total_signals']}")
        print(f"  Long signals: {summary['long_signals']}")
        print(f"  Short signals: {summary['short_signals']}")
        print(f"  Signals with breakout: {summary['signals_with_breakout']}")
        
        return self.signals
    
    def run_backtest(self, lookahead_bars=5):
        """Run backtest analysis"""
        print(f"\n--- RUNNING BACKTEST ---")
        
        if not self.signals:
            raise ValueError("Generate signals first using generate_signals()")
        
        self.backtester = Backtester(self.signals)
        
        # Calculate and print detailed report
        self.backtester.print_detailed_report(lookahead_bars=lookahead_bars)
        
        # Return accuracy metrics
        return self.backtester.calculate_accuracy(lookahead_bars)
    
    def create_chart(self, lookahead_bars=5, show_chart=True):
        """Create and display trading chart"""
        print(f"\n--- CREATING CHART ---")
        
        if self.df is None or not self.signals:
            raise ValueError("Complete data processing and signal generation first")
        
        # Get signals as DataFrame
        signals_df = self.signal_generator.get_signals_dataframe()
        
        # Create chart
        self.chart_builder = ChartBuilder(self.df, signals_df)
        
        # Get accuracy rate for title
        accuracy_results = self.backtester.calculate_accuracy(lookahead_bars)
        accuracy_rate = accuracy_results['accuracy_rate']
    
        sr_detector = EnhancedSRDetector(self.df)
        sr_levels = sr_detector.get_top_sr_levels(num_levels=4)
    
        # Build complete chart with S/R levels
        fig = self.chart_builder.build_complete_chart(
            accuracy_rate=accuracy_rate,
            lookahead_bars=lookahead_bars,
            sr_levels=sr_levels  # <-- pass S/R levels here
        )
        
        # Create signal table as a separate figure
        signal_table = SignalTable(signals_df)
        table_fig = signal_table.create_table_figure()
        
        if show_chart:
            # Show both figures separately
            fig.show()
            table_fig.show()
        
        return fig, table_fig
    
    def run_complete_analysis(self, file_path, lookahead_bars=5, 
                            confirmation_bars=7, ema_fast=9, ema_slow=15,    big_candle_multiplier=2,        # <--- set your value here
    big_candle_lookback=10,         # <--- set your value here
    volume_multiplier=2,
    volume_lookback=10,
                            show_chart=True):
        """Run complete trading analysis pipeline"""
        print("="*60)
        print("STARTING COMPLETE TRADING ANALYSIS")
        print("="*60)

        
        try:
            # Step 1: Load and process data
            self.load_and_process_data(file_path)
            
            # Step 2: Calculate indicators
            self.calculate_indicators(
    ema_fast=ema_fast,
    ema_slow=ema_slow,
    big_candle_multiplier=big_candle_multiplier,
    big_candle_lookback=big_candle_lookback,
    volume_multiplier=volume_multiplier,
    volume_lookback=volume_lookback,
    swing_lookback=8
)
            
            # Step 3: Generate signals
            self.generate_signals(
                confirmation_bars=confirmation_bars,
                lookahead_bars=lookahead_bars
            )
            signals_df = self.signal_generator.get_signals_dataframe()
            
            # Step 4: Run backtest
            accuracy_results = self.run_backtest(lookahead_bars=lookahead_bars)
            
            # Step 5: Create chart
            self.create_chart(lookahead_bars=lookahead_bars, show_chart=show_chart)
            
            print(f"\n{'='*60}")
            print("ANALYSIS COMPLETE ✓")
            print(f"Overall Accuracy: {accuracy_results['accuracy_rate']:.2f}%")
            print("="*60)
            
            if not signals_df.empty:
                total_signals = len(signals_df)
                sr_confirmed = signals_df['SR_Confirmed'].sum()
                sr_accuracy = (sr_confirmed / total_signals) * 100 if total_signals > 0 else 0
                print(f"\nS/R Confirmation Accuracy: {sr_accuracy:.2f}% ({sr_confirmed}/{total_signals})")
            else:
                print("\nS/R Confirmation Accuracy: N/A")

            # === DETAILED SIGNAL TIMELINES ===
            print("\n" + "="*80)
            print("\n" + "="*80)
            print("DETAILED SIGNAL TIMELINES WITH EXACT EVENT LOCATIONS")
            print("="*80)
            self.print_signal_timeline()

            user_choice = input("\nEnter signal ID for detailed view (or press Enter to skip): ")
            if user_choice.isdigit():
                self.print_signal_timeline(int(user_choice))
            return {
                'accuracy_results': accuracy_results,
                'signals': self.signals,
                'dataframe': self.df
            }
        except Exception as e:
            print(f"Error during analysis: {e}")
            raise


    
    def get_best_signals(self, min_confirmations=2):
        """Get the best signals with minimum confirmations"""
        if self.backtester is None:
            raise ValueError("Run backtest first")
        
        return self.backtester.get_best_signals(min_confirmations=min_confirmations)
    
    def save_results(self, filename_prefix="trading_analysis"):
        """Save analysis results to files"""
        if self.signals and self.chart_builder:
            # Save signals to CSV
            signals_df = self.signal_generator.get_signals_dataframe()
            signals_df.to_csv(f"{filename_prefix}_signals.csv", index=False)
            
            # Save chart
            self.chart_builder.save_chart(f"{filename_prefix}_chart.html")
            
            print(f"Results saved with prefix: {filename_prefix}")
    def get_detailed_signal_timeline(self):
        """Get detailed timeline of each signal with exact event timings"""
        if not self.signals:
            return []

        detailed_timelines = []

        for idx, signal in enumerate(self.signals):
            # You need to store Cross_Index and Cross_Price in your signals for this to work
            cross_idx = None
            cross_price = None
            # Try to infer cross_idx and cross_price if not present
            if 'Cross_Time' in signal and self.df is not None:
                try:
                    cross_idx = self.df.index.get_loc(signal['Cross_Time'])
                    cross_price = self.df.loc[signal['Cross_Time'], 'Close']
                except Exception:
                    cross_idx = None
                    cross_price = None
            if 'Cross_Index' in signal:
                cross_idx = signal['Cross_Index']
            if 'Cross_Price' in signal:
                cross_price = signal['Cross_Price']

            progression = self.signal_generator.track_signal_progression(
                cross_idx, signal['Type']
            ) if cross_idx is not None else {}

            cross_events = self.indicators.get_event_at_candle(cross_idx) if cross_idx is not None else []

            timeline = {
                'signal_id': idx + 1,
                'signal_type': signal['Type'],
                'cross_details': {
                    'candle_number': cross_idx,
                    'timestamp': signal['Cross_Time'],
                    'price': cross_price,
                    'events_at_cross': cross_events
                },
                'progression': progression,
                'confirmation_count': signal.get('Confirmation_Count', 0),
                'final_accuracy': signal.get('Accuracy', 'Unknown')
            }

            detailed_timelines.append(timeline)

        return detailed_timelines

    def print_signal_timeline(self, signal_id=None):
        """Print detailed timeline for specific signal or all signals"""
        timelines = self.get_detailed_signal_timeline()

        if signal_id:
            timelines = [t for t in timelines if t['signal_id'] == signal_id]

        for timeline in timelines:
            print(f"\n{'='*60}")
            print(f"SIGNAL #{timeline['signal_id']} - {timeline['signal_type']} TIMELINE")
            print(f"{'='*60}")

            # Cross details
            cross = timeline['cross_details']
            print(f"📍 CROSS EVENT:")
            print(f"   Candle #{cross['candle_number']} at {cross['timestamp']}")
            print(f"   Price: {cross['price']:.4f}" if cross['price'] is not None else "   Price: N/A")
            if cross['events_at_cross']:
                print(f"   Concurrent Events: {', '.join([e['event'] for e in cross['events_at_cross']])}")

            # Events after cross
            progression = timeline['progression']
            if progression and progression.get('events_after_cross'):
                print(f"\n📈 EVENTS AFTER CROSS:")
                for event in progression['events_after_cross']:
                    print(f"   Candle +{event['candle_after_cross']}: {', '.join(event['events'])} at {event['timestamp']}")
                    print(f"   Price: {event['price']:.4f}")

            # Breakout details
            if progression and 'breakout_candle' in progression:
                print(f"\n🚀 BREAKOUT CONFIRMED:")
                print(f"   Candle #{progression['breakout_candle']} at {progression['breakout_time']}")
                print(f"   Breakout Price: {progression['breakout_price']:.4f}")

            print(f"\n✅ FINAL RESULT: {timeline['final_accuracy']} | Confirmations: {timeline['confirmation_count']}")
# ...existing code...


def main():
    """Main execution function"""
    # Get user input for lookahead bars
    try:
        lookahead_bars = int(input("How many candles after breakout should we check? "))
    except ValueError:
        lookahead_bars = 5
        print(f"Using default lookahead of {lookahead_bars} bars")
    
    # File path (update this to your CSV file location)
    file_path = r'C:\Users\sunil\Desktop\project1\PROJECT21\Real-Time\2025-06-04T11-59_export.csv'
    
    # Create and run trading system
    trading_system = TradingSystem()
    
    try:
        results = trading_system.run_complete_analysis(
            file_path=file_path,
            lookahead_bars=lookahead_bars,
            confirmation_bars=7,
            ema_fast=9,
            ema_slow=15,
            big_candle_multiplier=2.5,  # <--- set your value here
            big_candle_lookback=10,   # <--- set your value here
            volume_multiplier=2.5,
            volume_lookback=10,
            show_chart=True
        )
        
        # Optionally save results
        # trading_system.save_results("my_trading_analysis")
        
        # Show best signals
        print("\n--- TOP SIGNALS WITH MULTIPLE CONFIRMATIONS ---")
        best_signals = trading_system.get_best_signals(min_confirmations=2)
        if not best_signals.empty:
            print(best_signals[['Type', 'Cross_Time', 'Breakout_Time', 'Accuracy', 'Confirmation_Count']].head())
        else:
            print("No signals found with multiple confirmations")
        print("\n--- ALL BREAKOUTS WITH S/R CONFIRMATION ---")
        signals_df = trading_system.signal_generator.get_signals_dataframe()
        if not signals_df.empty:
            print(signals_df[['Type', 'Cross_Time', 'Breakout_Time', 'Breakout_Price', 'SR_Confirmed', 'SR_Level_Broken']].to_string(index=False))
        else:
            print("No signals found.")

        # Calculate and print S/R confirmation accuracy
        if not signals_df.empty:
            total_signals = len(signals_df)
            sr_confirmed = signals_df['SR_Confirmed'].sum()
            sr_accuracy = (sr_confirmed / total_signals) * 100 if total_signals > 0 else 0
            print(f"\nS/R Confirmation Accuracy: {sr_accuracy:.2f}% ({sr_confirmed}/{total_signals})")
        else:
            print("\nS/R Confirmation Accuracy: N/A")
    except Exception as e:
        print(f"Analysis failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()