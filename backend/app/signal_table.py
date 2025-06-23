"""
Signal Summary Table - Creates a visual table of trading signals and confirmations
"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class SignalTable:
    """Creates a visual table of trading signals with confirmations"""
    
    def __init__(self, signals_df):
        """Initialize with signals DataFrame"""
        if signals_df is None or signals_df.empty:
            raise ValueError("Signals DataFrame cannot be None or empty")
        
        self.signals_df = signals_df.copy()
        print(f"SignalTable initialized with {len(self.signals_df)} signals")
    
    def create_table_figure(self):
        """Create a plotly figure with the signals table"""
        # Prepare data for table
        table_data = self._prepare_table_data()
        
        # Create figure
        fig = go.Figure(data=[go.Table(
            header=dict(
                values=list(table_data.columns),
                fill_color='paleturquoise',
                align='center',
                font=dict(size=12, color='black')
            ),
            cells=dict(
                values=[table_data[col] for col in table_data.columns],
                fill_color='lavender',
                align='center',
                font=dict(size=11),
                height=25
            )
        )])
        
        fig.update_layout(
            title="Trading Signals Summary",
            height=400,
            margin=dict(l=10, r=10, t=50, b=10)
        )
        
        return fig
    
    def _prepare_table_data(self):
        """Prepare data for the table display"""
        table_df = pd.DataFrame()

        # Basic signal info
        table_df['Signal'] = self.signals_df['Type'].apply(
            lambda x: "🔼 BUY" if x == 'LONG' else "🔽 SELL"
        )
        table_df['Cross Time'] = self.signals_df['Cross_Time'].dt.strftime('%Y-%m-%d %H:%M')

        # Volume Spike
        table_df['Volume Spike'] = self.signals_df['Volume_Spike_Time'].notna().map({True: '✅', False: '❌'})
        table_df['Volume Spike Time'] = self.signals_df['Volume_Spike_Time'].apply(
            lambda x: x.strftime('%Y-%m-%d %H:%M') if pd.notna(x) else '-'
        )

        # Big Candle
        table_df['Big Candle'] = self.signals_df['Big_Candle_Time'].notna().map({True: '✅', False: '❌'})
        table_df['Big Candle Time'] = self.signals_df['Big_Candle_Time'].apply(
            lambda x: x.strftime('%Y-%m-%d %H:%M') if pd.notna(x) else '-'
        )

        # Breakout
        table_df['Breakout'] = self.signals_df['Breakout_Time'].notna().map({True: '✅', False: '❌'})
        table_df['Breakout Time'] = self.signals_df['Breakout_Time'].apply(
            lambda x: x.strftime('%Y-%m-%d %H:%M') if pd.notna(x) else '-'
        )

        # S/R confirmation if available
        if 'SR_Confirmed' in self.signals_df.columns:
            table_df['S/R Confirm'] = self.signals_df['SR_Confirmed'].map({True: '✅', False: '❌', None: '❌'})
            if 'SR_Level_Broken' in self.signals_df.columns:
                table_df['S/R Level Broken'] = self.signals_df['SR_Level_Broken'].apply(
                    lambda x: f"{x:.2f}" if pd.notna(x) else '-'
                )

        # Accuracy if available
        if 'Accuracy' in self.signals_df.columns:
            table_df['Accurate'] = self.signals_df['Accuracy'].map(
                {True: '✅', False: '❌', None: '-'}
            )

        return table_df
    
    def add_table_to_chart(self, main_fig, lookahead_bars=5):
        """Add the signals table below the main chart"""
        # Create table figure
        table_fig = self.create_table_figure()
        
        # Create a new figure with subplots
        combined_fig = make_subplots(
            rows=2, 
            cols=1,
            row_heights=[0.8, 0.2],
            specs=[[{"type": "scatter"}], [{"type": "table"}]],
            vertical_spacing=0.03
        )
        
        # Add all traces from main figure to the top subplot
        for trace in main_fig.data:
            combined_fig.add_trace(trace, row=1, col=1)
        
        # Add table to bottom subplot
        combined_fig.add_trace(
            go.Table(
                header=table_fig.data[0].header,
                cells=table_fig.data[0].cells
            ),
            row=2, col=1
        )
        
        # Update layout
        # Copy layout from main figure
        for key in main_fig.layout:
            if key != 'height' and key != 'grid' and key != 'xaxis' and key != 'yaxis':
                combined_fig.layout[key] = main_fig.layout[key]
        
        # Add title info about lookahead
        title = main_fig.layout.title.text if hasattr(main_fig.layout.title, 'text') else "Trading Analysis"
        combined_fig.update_layout(
            title=f"{title}<br><sub>Accuracy measured {lookahead_bars} candles after breakout</sub>",
            height=1000,  # Increased height to accommodate table
        )
        
        # Update axes
        combined_fig.update_xaxes(main_fig.layout.xaxis, row=1, col=1)
        combined_fig.update_yaxes(main_fig.layout.yaxis, row=1, col=1)
        
        return combined_fig