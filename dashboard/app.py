"""
Simple web dashboard for CoreWeave Profitability Monitor
"""
import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.data_manager import DataManager
from analysis.correlation_analyzer import CorrelationAnalyzer

# Initialize data manager
dm = DataManager()
analyzer = CorrelationAnalyzer(dm)

# Initialize Dash app
app = dash.Dash(__name__)
app.title = "CoreWeave Profitability Monitor"

# Define the layout
app.layout = html.Div([
    html.H1("CoreWeave Profitability Monitor", 
            style={'textAlign': 'center', 'marginBottom': 30}),
    
    # Control panel
    html.Div([
        html.Label("Time Period (days):"),
        dcc.Dropdown(
            id='time-period-dropdown',
            options=[
                {'label': '7 days', 'value': 7},
                {'label': '30 days', 'value': 30},
                {'label': '90 days', 'value': 90},
                {'label': '180 days', 'value': 180}
            ],
            value=30
        ),
        html.Button('Refresh Data', id='refresh-button', n_clicks=0,
                   style={'marginTop': 10})
    ], style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top'}),
    
    # Main content area
    html.Div([
        # Summary cards
        html.Div(id='summary-cards', style={'marginBottom': 20}),
        
        # Charts
        dcc.Tabs(id='main-tabs', value='overview', children=[
            dcc.Tab(label='Overview', value='overview'),
            dcc.Tab(label='GPU Pricing', value='gpu-pricing'),
            dcc.Tab(label='Financial Markets', value='financial'),
            dcc.Tab(label='Correlations', value='correlations'),
            dcc.Tab(label='Alerts', value='alerts')
        ]),
        
        html.Div(id='tab-content')
        
    ], style={'width': '75%', 'float': 'right'})
])

@app.callback(
    [Output('summary-cards', 'children'),
     Output('tab-content', 'children')],
    [Input('time-period-dropdown', 'value'),
     Input('main-tabs', 'value'),
     Input('refresh-button', 'n_clicks')]
)
def update_dashboard(days_back, active_tab, n_clicks):
    # Get data summary
    summary = dm.get_data_summary()
    
    # Create summary cards
    summary_cards = html.Div([
        html.H3("Data Summary"),
        html.Div([
            html.Div([
                html.H4(f"{info['count']}", style={'margin': 0, 'color': '#1f77b4'}),
                html.P(table.replace('_', ' ').title(), style={'margin': 0})
            ], className='summary-card', style={
                'border': '1px solid #ddd',
                'padding': '10px',
                'margin': '5px',
                'borderRadius': '5px',
                'textAlign': 'center'
            }) for table, info in summary.items()
        ])
    ])
    
    # Generate tab content based on active tab
    if active_tab == 'overview':
        content = create_overview_tab(days_back)
    elif active_tab == 'gpu-pricing':
        content = create_gpu_pricing_tab(days_back)
    elif active_tab == 'financial':
        content = create_financial_tab(days_back)
    elif active_tab == 'correlations':
        content = create_correlations_tab(days_back)
    elif active_tab == 'alerts':
        content = create_alerts_tab()
    else:
        content = html.Div("Select a tab to view data")
    
    return summary_cards, content

def create_overview_tab(days_back):
    """Create overview tab content"""
    try:
        # Get recent data
        gpu_data = dm.get_gpu_pricing(days_back=days_back)
        treasury_data = dm.get_treasury_yields(days_back=days_back)
        energy_data = dm.get_energy_futures(days_back=days_back)
        
        charts = []
        
        # GPU pricing trend
        if not gpu_data.empty:
            gpu_data['timestamp'] = pd.to_datetime(gpu_data['timestamp'])
            fig_gpu = px.line(gpu_data, x='timestamp', y='price', color='gpu_model',
                             title='GPU Pricing Trends')
            charts.append(dcc.Graph(figure=fig_gpu))
        
        # Treasury yields
        if not treasury_data.empty:
            treasury_data['timestamp'] = pd.to_datetime(treasury_data['timestamp'])
            fig_treasury = px.line(treasury_data, x='timestamp', y='yield_10y',
                                  title='10-Year Treasury Yield')
            charts.append(dcc.Graph(figure=fig_treasury))
        
        # Energy prices
        if not energy_data.empty:
            energy_data['timestamp'] = pd.to_datetime(energy_data['timestamp'])
            fig_energy = px.line(energy_data, x='timestamp', y='natural_gas_price',
                                title='Natural Gas Futures')
            charts.append(dcc.Graph(figure=fig_energy))
        
        if not charts:
            return html.Div("No data available for the selected period")
        
        return html.Div(charts)
        
    except Exception as e:
        return html.Div(f"Error loading overview: {str(e)}")

def create_gpu_pricing_tab(days_back):
    """Create GPU pricing tab content"""
    try:
        gpu_data = dm.get_gpu_pricing(days_back=days_back)
        
        if gpu_data.empty:
            return html.Div("No GPU pricing data available")
        
        gpu_data['timestamp'] = pd.to_datetime(gpu_data['timestamp'])
        
        # Price trends by GPU model
        fig_trends = px.line(gpu_data, x='timestamp', y='price', color='gpu_model',
                            title='GPU Pricing Trends by Model')
        
        # Average prices
        avg_prices = gpu_data.groupby('gpu_model')['price'].mean().reset_index()
        fig_avg = px.bar(avg_prices, x='gpu_model', y='price',
                        title='Average GPU Prices')
        
        # Price distribution
        fig_dist = px.box(gpu_data, x='gpu_model', y='price',
                         title='GPU Price Distribution')
        
        return html.Div([
            dcc.Graph(figure=fig_trends),
            html.Div([
                html.Div([dcc.Graph(figure=fig_avg)], style={'width': '50%', 'display': 'inline-block'}),
                html.Div([dcc.Graph(figure=fig_dist)], style={'width': '50%', 'display': 'inline-block'})
            ])
        ])
        
    except Exception as e:
        return html.Div(f"Error loading GPU pricing data: {str(e)}")

def create_financial_tab(days_back):
    """Create financial markets tab content"""
    try:
        treasury_data = dm.get_treasury_yields(days_back=days_back)
        energy_data = dm.get_energy_futures(days_back=days_back)
        rates_data = dm.get_interest_rates(days_back=days_back)
        
        charts = []
        
        # Treasury yields
        if not treasury_data.empty:
            treasury_data['timestamp'] = pd.to_datetime(treasury_data['timestamp'])
            fig_treasury = px.line(treasury_data, x='timestamp', y='yield_10y',
                                  title='10-Year Treasury Yield (%)')
            charts.append(dcc.Graph(figure=fig_treasury))
        
        # Energy futures
        if not energy_data.empty:
            energy_data['timestamp'] = pd.to_datetime(energy_data['timestamp'])
            
            # Natural gas
            fig_gas = px.line(energy_data, x='timestamp', y='natural_gas_price',
                             title='Natural Gas Futures ($/MMBtu)')
            charts.append(dcc.Graph(figure=fig_gas))
            
            # Crude oil (if available)
            if 'crude_oil_price' in energy_data.columns and energy_data['crude_oil_price'].notna().any():
                fig_oil = px.line(energy_data, x='timestamp', y='crude_oil_price',
                                 title='Crude Oil Futures ($/barrel)')
                charts.append(dcc.Graph(figure=fig_oil))
        
        # Interest rates
        if not rates_data.empty:
            rates_data['timestamp'] = pd.to_datetime(rates_data['timestamp'])
            fig_rates = px.line(rates_data, x='timestamp', y='fed_funds_rate',
                               title='Federal Funds Rate (%)')
            charts.append(dcc.Graph(figure=fig_rates))
        
        if not charts:
            return html.Div("No financial data available for the selected period")
        
        return html.Div(charts)
        
    except Exception as e:
        return html.Div(f"Error loading financial data: {str(e)}")

def create_correlations_tab(days_back):
    """Create correlations tab content"""
    try:
        # Get correlation analysis
        analysis = analyzer.analyze_profitability_indicators(days_back=days_back)
        
        if "error" in analysis:
            return html.Div(f"Error in correlation analysis: {analysis['error']}")
        
        content = []
        
        # GPU correlations table
        if analysis.get('gpu_correlations'):
            gpu_corr_data = []
            for metric, corr_data in analysis['gpu_correlations'].items():
                gpu_corr_data.append({
                    'Metric': metric.replace('_', ' ').title(),
                    'Correlation': f"{corr_data['correlation']:.3f}",
                    'Strength': corr_data['strength'].title(),
                    'Significance': corr_data['significance'].replace('_', ' ').title()
                })
            
            content.append(html.H3("GPU Price Correlations"))
            content.append(dash_table.DataTable(
                data=gpu_corr_data,
                columns=[{"name": i, "id": i} for i in gpu_corr_data[0].keys()] if gpu_corr_data else [],
                style_cell={'textAlign': 'left'},
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{Strength} = Strong'},
                        'backgroundColor': '#ff9999',
                        'color': 'black',
                    },
                    {
                        'if': {'filter_query': '{Strength} = Moderate'},
                        'backgroundColor': '#ffcc99',
                        'color': 'black',
                    }
                ]
            ))
        
        # Key insights
        if analysis.get('key_insights'):
            content.append(html.H3("Key Insights"))
            content.append(html.Ul([
                html.Li(insight) for insight in analysis['key_insights']
            ]))
        
        # Risk factors
        if analysis.get('risk_factors'):
            content.append(html.H3("Risk Factors"))
            content.append(html.Ul([
                html.Li(risk, style={'color': 'red' if 'HIGH RISK' in risk else 'orange'})
                for risk in analysis['risk_factors']
            ]))
        
        if not content:
            return html.Div("No correlation data available")
        
        return html.Div(content)
        
    except Exception as e:
        return html.Div(f"Error loading correlation analysis: {str(e)}")

def create_alerts_tab():
    """Create alerts tab content"""
    try:
        # Get unresolved alerts
        alerts = dm.get_unresolved_alerts()
        
        if alerts.empty:
            return html.Div("No unresolved alerts")
        
        # Convert to list of dictionaries for DataTable
        alerts_data = alerts.to_dict('records')
        
        # Format timestamp
        for alert in alerts_data:
            alert['timestamp'] = pd.to_datetime(alert['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        
        return html.Div([
            html.H3("Unresolved Alerts"),
            dash_table.DataTable(
                data=alerts_data,
                columns=[
                    {"name": "Time", "id": "timestamp"},
                    {"name": "Type", "id": "alert_type"},
                    {"name": "Severity", "id": "severity"},
                    {"name": "Message", "id": "message"}
                ],
                style_cell={'textAlign': 'left', 'whiteSpace': 'normal', 'height': 'auto'},
                style_data_conditional=[
                    {
                        'if': {'filter_query': '{severity} = high'},
                        'backgroundColor': '#ff9999',
                        'color': 'black',
                    },
                    {
                        'if': {'filter_query': '{severity} = critical'},
                        'backgroundColor': '#ff6666',
                        'color': 'white',
                    }
                ],
                page_size=10
            )
        ])
        
    except Exception as e:
        return html.Div(f"Error loading alerts: {str(e)}")

if __name__ == '__main__':
    # Run the app
    app.run(
        debug=True, 
        host='0.0.0.0', 
        port=12000
    )