import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

class ChartBuilder:
    """Build interactive Plotly charts for trading analysis"""
    
    def __init__(self, df, signals_df=None):
        """Initialize with OHLCV data and optional signals"""
        if df is None or df.empty:
            raise ValueError("DataFrame cannot be None or empty")
        
        self.df = df.copy()
        self.signals_df = signals_df.copy() if signals_df is not None else pd.DataFrame()
        self.fig = None
        
        # Set default renderer
        pio.renderers.default = 'browser'
        
        print(f"ChartBuilder initialized with {len(self.df)} data points")
        if not self.signals_df.empty:
            print(f"  {len(self.signals_df)} signals to plot")
    
    def create_base_chart(self, height=800):
        """Create base candlestick chart with volume subplot"""
        print("Creating base candlestick chart...")
        
        # Create subplots: candlestick on top, volume on bottom
        self.fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            row_heights=[0.7, 0.3],
            vertical_spacing=0.02,
            subplot_titles=('Price', 'Volume')
        )
        
        # Add candlestick chart with improved visibility
        self.fig.add_trace(
            go.Candlestick(
                x=self.df.index,
                open=self.df['Open'],
                high=self.df['High'],
                low=self.df['Low'],
                close=self.df['Close'],
                name='Candlesticks',
                increasing=dict(line=dict(width=3, color='#26a69a'), fillcolor='#26a69a'),
                decreasing=dict(line=dict(width=3, color='#ef5350'), fillcolor='#ef5350')
            ),
            row=1, col=1
        )
        
        # Add volume bars
        self.fig.add_trace(
            go.Bar(
                x=self.df.index,
                y=self.df['Volume'],
                name='Volume',
                marker_color='lightblue'
            ),
            row=2, col=1
        )
        
        # Set initial layout
        self.fig.update_layout(
            height=height,
            title="Trading Chart",
            xaxis_rangeslider_visible=False,  # Disable rangeslider which can cause rendering issues
            showlegend=True,
            # Improve overall appearance
            plot_bgcolor='rgba(240,240,240,0.8)',
            paper_bgcolor='white',
            font=dict(size=12),
            margin=dict(l=30, r=30, t=50, b=30)  # Reduce margins to maximize chart area
        )
        
        return self.fig
    
    def add_ema_lines(self, ema_fast=9, ema_slow=15):
        """Add EMA lines to the chart"""
        if self.fig is None:
            raise ValueError("Create base chart first using create_base_chart()")
        
        ema_fast_col = f'EMA{ema_fast}'
        ema_slow_col = f'EMA{ema_slow}'
        
        if ema_fast_col not in self.df.columns or ema_slow_col not in self.df.columns:
            print(f"Warning: EMA columns not found. Expected {ema_fast_col} and {ema_slow_col}")
            return
        
        print(f"Adding EMA lines: {ema_fast} and {ema_slow}")
        
        # Add fast EMA
        self.fig.add_trace(
            go.Scatter(
                x=self.df.index,
                y=self.df[ema_fast_col],
                mode='lines',
                line=dict(color='orange', width=1),
                name=f'EMA {ema_fast}'
            ),
            row=1, col=1
        )
        
        # Add slow EMA
        self.fig.add_trace(
            go.Scatter(
                x=self.df.index,
                y=self.df[ema_slow_col],
                mode='lines',
                line=dict(color='green', width=1),
                name=f'EMA {ema_slow}'
            ),
            row=1, col=1
        )
    
    def add_signal_annotations(self, lookahead_bars=5):
        """Add signal annotations to the chart"""
        if self.fig is None:
            raise ValueError("Create base chart first using create_base_chart()")
        
        if self.signals_df.empty:
            print("No signals to annotate")
            return
        
        print(f"Adding signal annotations for {len(self.signals_df)} signals")
        
        for _, signal in self.signals_df.iterrows():
            self._add_crossover_marker(signal)
            self._add_volume_spike_marker(signal)
            self._add_big_candle_marker(signal)
            self._add_breakout_marker(signal, lookahead_bars)
    
    def add_sr_confirmation_annotations(self):
        """Annotate each breakout with S/R confirmation status"""
        if self.fig is None:
            raise ValueError("Create base chart first using create_base_chart()")
        if self.signals_df.empty:
            print("No signals to annotate for S/R confirmation")
            return

        for _, signal in self.signals_df.iterrows():
            if pd.notna(signal.get('Breakout_Time', None)):
                breakout_time = signal['Breakout_Time']
                if breakout_time in self.df.index:
                    breakout_price = signal['Breakout_Price']
                    sr_confirmed = signal.get('SR_Confirmed', False)
                    text = "S/R Confirmed" if sr_confirmed else "No S/R Confirm"
                    color = "purple" if sr_confirmed else "gray"
                    self.fig.add_annotation(
                        x=breakout_time,
                        y=breakout_price,
                        text=text,
                        showarrow=True,
                        arrowhead=1,
                        font=dict(color=color, size=12),
                        bgcolor="white"
                    )
    
    def _add_crossover_marker(self, signal):
        """Add EMA crossover marker"""
        if pd.notna(signal['Cross_Time']):
            cross_time = signal['Cross_Time']
            if cross_time in self.df.index:
                close_price = self.df.loc[cross_time, 'Close']
                
                self.fig.add_trace(
                    go.Scatter(
                        x=[cross_time],
                        y=[close_price],
                        mode='markers',
                        marker=dict(symbol='circle', color='purple', size=10),
                        hoverinfo='text',
                        hovertext=(
                            f"EMA Crossover ({signal['Type']})<br>"
                            f"Time: {cross_time}<br>"
                            f"Price: {close_price:.2f}"
                        ),
                        showlegend=False
                    ),
                    row=1, col=1
                )
    
    def _add_volume_spike_marker(self, signal):
        """Add volume spike marker"""
        if pd.notna(signal['Volume_Spike_Time']):
            vol_time = signal['Volume_Spike_Time']
            if vol_time in self.df.index:
                volume = self.df.loc[vol_time, 'Volume']
                
                self.fig.add_trace(
                    go.Scatter(
                        x=[vol_time],
                        y=[volume],
                        mode='markers',
                        marker=dict(symbol='square', color='blue', size=8),
                        hoverinfo='text',
                        hovertext=(
                            f"Volume Spike<br>"
                            f"Time: {vol_time}<br>"
                            f"Volume: {volume:,.0f}"
                        ),
                        showlegend=False
                    ),
                    row=2, col=1
                )
    
    def _add_big_candle_marker(self, signal):
        """Add big candle marker"""
        if pd.notna(signal['Big_Candle_Time']):
            candle_time = signal['Big_Candle_Time']
            if candle_time in self.df.index:
                high_price = self.df.loc[candle_time, 'High']
                body_size = abs(self.df.loc[candle_time, 'Close'] - self.df.loc[candle_time, 'Open'])
                
                self.fig.add_trace(
                    go.Scatter(
                        x=[candle_time],
                        y=[high_price],
                        mode='markers',
                        marker=dict(symbol='diamond', color='orange', size=8),
                        hoverinfo='text',
                        hovertext=(
                            f"Big Candle<br>"
                            f"Time: {candle_time}<br>"
                            f"Body Size: {body_size:.2f}"
                        ),
                        showlegend=False
                    ),
                    row=1, col=1
                )
    
    def _add_breakout_marker(self, signal, lookahead_bars):
        """Add breakout marker"""
        if pd.notna(signal['Breakout_Time']):
            breakout_time = signal['Breakout_Time']
            if breakout_time in self.df.index:
                breakout_price = signal['Breakout_Price']
                
                # Choose marker style based on signal type
                symbol = 'triangle-up' if signal['Type'] == 'LONG' else 'triangle-down'
                color = 'green' if signal['Type'] == 'LONG' else 'red'
                
                # Create hover text
                hover_text = (
                    f"Breakout ({signal['Type']})<br>"
                    f"Time: {breakout_time}<br>"
                    f"Price: {breakout_price:.2f}"
                )
                
                if pd.notna(signal['Price_After_n']):
                    price_diff = signal['Price_After_n'] - breakout_price
                    hover_text += (
                        f"<br>After {lookahead_bars} bars: {signal['Price_After_n']:.2f}"
                        f"<br>Difference: {price_diff:.2f}"
                        f"<br>Accurate: {'Yes' if signal['Accuracy'] else 'No'}"
                    )
                
                self.fig.add_trace(
                    go.Scatter(
                        x=[breakout_time],
                        y=[breakout_price],
                        mode='markers',
                        marker=dict(symbol=symbol, color=color, size=12),
                        hoverinfo='text',
                        hovertext=hover_text,
                        showlegend=False
                    ),
                    row=1, col=1
                )
    
    def add_vwap_line(self):
        """Add VWAP line to chart"""
        if 'VWAP' not in self.df.columns:
            print("Warning: VWAP column not found")
            return
        
        print("Adding VWAP line")
        self.fig.add_trace(
            go.Scatter(
                x=self.df.index,
                y=self.df['VWAP'],
                mode='lines',
                line=dict(color='purple', width=2),
                name='VWAP'
            ),
            row=1, col=1
        )

    def add_support_resistance_lines(self, sr_levels):
        """Add horizontal S&R lines - FIXED VERSION"""
        if not sr_levels:
            print("No S/R levels provided")
            return
            
        print("Adding Support/Resistance lines")
        
        try:
            # Handle different input formats for sr_levels
            if isinstance(sr_levels, dict):
                resistances = sr_levels.get('resistances', [])
                supports = sr_levels.get('supports', [])
            elif isinstance(sr_levels, list):
                # If it's a list, assume it's all resistance levels
                resistances = sr_levels
                supports = []
            else:
                print(f"Warning: Unknown sr_levels format: {type(sr_levels)}")
                return
            
            # Add resistance lines
            for i, resistance in enumerate(resistances):
                try:
                    # Extract price value safely
                    if isinstance(resistance, dict):
                        price = resistance.get('price', resistance.get('level', None))
                    elif isinstance(resistance, (int, float)):
                        price = resistance
                    elif hasattr(resistance, 'price'):
                        price = resistance.price
                    else:
                        price = float(resistance)  # Try to convert to float
                    
                    # Ensure price is a number
                    if price is None:
                        print(f"Warning: Could not extract price from resistance {i}: {resistance}")
                        continue
                    
                    price = float(price)  # Convert to float
                    print(f"Adding resistance line at: {price} (type: {type(price)})")
                    
                    self.fig.add_hline(
                        y=price,
                        line=dict(color='red', width=1, dash='dash'),
                        annotation_text=f"R{i+1}: {price:.2f}",
                        row=1, col=1
                    )
                    
                except Exception as e:
                    print(f"Error adding resistance line {i}: {e}")
                    print(f"Resistance data: {resistance}, type: {type(resistance)}")
                    continue
            
            # Add support lines  
            for i, support in enumerate(supports):
                try:
                    # Extract price value safely
                    if isinstance(support, dict):
                        price = support.get('price', support.get('level', None))
                    elif isinstance(support, (int, float)):
                        price = support
                    elif hasattr(support, 'price'):
                        price = support.price
                    else:
                        price = float(support)  # Try to convert to float
                    
                    # Ensure price is a number
                    if price is None:
                        print(f"Warning: Could not extract price from support {i}: {support}")
                        continue
                    
                    price = float(price)  # Convert to float
                    print(f"Adding support line at: {price} (type: {type(price)})")
                    
                    self.fig.add_hline(
                        y=price,
                        line=dict(color='green', width=1, dash='dash'),
                        annotation_text=f"S{i+1}: {price:.2f}",
                        row=1, col=1
                    )
                    
                except Exception as e:
                    print(f"Error adding support line {i}: {e}")
                    print(f"Support data: {support}, type: {type(support)}")
                    continue
                    
        except Exception as e:
            print(f"Error in add_support_resistance_lines: {e}")
            print(f"sr_levels type: {type(sr_levels)}")
            print(f"sr_levels content: {sr_levels}")

    def update_chart_title(self, accuracy_rate=None, lookahead_bars=None):
        """Update chart title with accuracy information"""
        if self.fig is None:
            return
        
        base_title = "Trading Analysis: Candlesticks + EMAs + Volume + Signals"
        
        if accuracy_rate is not None and lookahead_bars is not None:
            title = f"{base_title}<br>Overall Accuracy (lookahead={lookahead_bars}): {accuracy_rate:.2f}%"
        else:
            title = base_title
        
        self.fig.update_layout(title=title)
    
    def customize_layout(self, **kwargs):
        """Customize chart layout"""
        if self.fig is None:
            raise ValueError("Create base chart first")
        
        default_layout = {
            'xaxis': dict(title='Date'),
            'yaxis': dict(
                title='Price',
                # Add auto-range settings to focus on the price action
                autorange=False,
                # Set a fixed range to zoom in on the price action
                # This will be calculated dynamically based on visible data
                range=[self.df['Low'].min() * 0.995, self.df['High'].max() * 1.005]
            ),
            'xaxis2': dict(title='Date'),
            'yaxis2': dict(title='Volume'),
            'legend': dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1
            ),
            'margin': dict(l=40, r=40, t=80, b=40)
        }
        
        # Merge with custom kwargs
        layout_updates = {**default_layout, **kwargs}
        self.fig.update_layout(**layout_updates)
        
        # Improve candlestick visibility
        self.fig.update_traces(
            selector=dict(type='candlestick'),
            increasing=dict(line=dict(width=2), fillcolor='#26a69a'),
            decreasing=dict(line=dict(width=2), fillcolor='#ef5350')
        )
    
    def build_complete_chart(self, accuracy_rate=None, lookahead_bars=5, 
                           ema_fast=9, ema_slow=15, height=800, sr_levels=None):
        """Build a complete chart with all components"""
        print("Building complete trading chart...")
        
        # Create base chart
        self.create_base_chart(height=height)
        
        # Add EMA lines
        self.add_ema_lines(ema_fast, ema_slow)
        
        # Add VWAP line
        self.add_vwap_line()
        
        # Add S&R lines if provided
        if sr_levels:
            self.add_support_resistance_lines(sr_levels)
        
        # Add signal annotations
        self.add_signal_annotations(lookahead_bars)
        self.add_sr_confirmation_annotations() 
        
        # Update title with accuracy
        self.update_chart_title(accuracy_rate, lookahead_bars)
        
        # Customize layout
        self.customize_layout()
        
        print("Chart building complete ✓")
        return self.fig
    
    def show_chart(self):
        """Display the chart"""
        if self.fig is None:
            raise ValueError("No chart created. Call create_base_chart() or build_complete_chart() first")
        
        self.fig.show()
    
    def save_chart(self, filename, format='html'):
        """Save chart to file"""
        if self.fig is None:
            raise ValueError("No chart created")
        
        if format == 'html':
            self.fig.write_html(filename)
        elif format == 'png':
            self.fig.write_image(filename)
        else:
            raise ValueError("Format must be 'html' or 'png'")
        
        print(f"Chart saved as {filename}")
    
    def get_figure(self):
        """Return the Plotly figure object"""
        return self.fig