# CoreWeave Profitability Indicators Monitor

A comprehensive data crawler and monitoring system designed to track key indicators that correlate with CoreWeave's profitability. This system monitors financial markets, energy prices, GPU pricing, SEC filings, and news events to provide insights into factors affecting CoreWeave's business performance.

## 🎯 Monitored Indicators

### Financial Markets
- **Treasury Yields (10Y, 2Y, 30Y)** - Impact on borrowing costs and customer spending
- **Federal Funds Rate** - Affects financing costs and demand for cloud services
- **Natural Gas Futures** - Direct impact on data center operational costs
- **Crude Oil Futures** - Indirect energy cost indicator

### GPU Market
- **Spot GPU Rental Prices** - Lambda Labs pricing data
- **CoreWeave GPU Pricing** - Direct pricing monitoring
- **Hardware Launch News** - NVIDIA/AMD product announcements
- **Supply Constraint Reports** - GPU availability and supply chain issues

### Corporate Intelligence
- **SEC Filings** - CoreWeave debt levels, power contracts, and risk factors
- **Earnings Call Transcripts** - Utilization rates and customer commentary
- **Bond Issuance Alerts** - Corporate financing activities

### Market Events
- **Energy Market Volatility** - Storms, geopolitical events affecting energy
- **Interest Rate Changes** - Federal Reserve policy updates
- **Cloud Platform Pricing** - Competitive pricing changes

## 🏗️ Architecture

```
├── crawler/                 # Data collection modules
│   ├── core.py             # Web crawling engine
│   ├── financial_data.py   # Financial market data
│   ├── sec_filings.py      # SEC filings crawler
│   ├── news_crawler.py     # News and events
│   └── schema.py           # Data models
├── storage/                 # Data persistence
│   ├── data_manager.py     # Database operations
│   └── setup.py            # Database schema
├── alerts/                  # Alert system
│   └── alert_system.py     # Monitoring and notifications
├── analysis/                # Data analysis
│   └── correlation_analyzer.py  # Correlation analysis
└── run.py                  # Main orchestrator
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd data-crawler

# Install dependencies
pip install -r requirements.txt

# Setup database
python storage/setup.py
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

**Required API Keys:**
- OpenAI API key for content extraction
- FRED API key for economic data
- Email credentials for notifications

### 3. Run the Monitor

```bash
# Single collection cycle
python run.py

# Continuous monitoring (60-minute intervals)
MONITOR_MODE=continuous MONITOR_INTERVAL=60 python run.py

# Scheduled monitoring with different frequencies
MONITOR_MODE=scheduled python run.py

# View data summary
MONITOR_MODE=summary python run.py
```

## 📊 Data Collection Frequencies

| Data Type | Frequency | Rationale |
|-----------|-----------|-----------|
| GPU Pricing | 15 minutes | High volatility, direct revenue impact |
| Financial Data | 15 minutes | Market hours volatility |
| News & Events | 1 hour | Breaking news impact |
| SEC Filings | 4 hours | Low frequency, high importance |
| Alert Monitoring | 30 minutes | Timely notification balance |

## 🔔 Alert System

### Alert Types

1. **GPU Price Spikes** (>15% increase)
2. **Treasury Yield Changes** (>20 basis points)
3. **Natural Gas Price Spikes** (>10% change)
4. **Federal Funds Rate Changes**
5. **New SEC Filings**
6. **GPU Supply Constraints**
7. **Energy Market Events**

### Notification Channels

- **Console Output** - Real-time monitoring
- **Email Alerts** - Detailed notifications
- **SMS Alerts** - Critical alerts only (optional)

## 📈 Correlation Analysis

The system automatically analyzes correlations between:

- GPU pricing vs. energy costs
- Interest rates vs. GPU demand
- Treasury yields vs. financing costs
- Supply constraints vs. pricing power

### Example Analysis Output

```
GPU PRICING CORRELATIONS:
natural_gas_price:
  Correlation: 0.456
  Strength: moderate
  Significance: significant

treasury_10y:
  Correlation: 0.234
  Strength: weak
  Significance: significant

KEY INSIGHTS:
• GPU prices are moderately positively correlated with natural_gas_price (r=0.456, p<0.05)
• Natural gas price changes may increase GPU pricing costs for CoreWeave

RISK FACTORS:
• HIGH RISK: Natural gas price increases directly impact operational costs
• MEDIUM RISK: Interest rate changes affect customer demand and financing costs
```

## 🗄️ Database Schema

### Core Tables

- `gpu_pricing` - GPU rental prices and availability
- `treasury_yields` - Government bond yields
- `energy_futures` - Energy commodity prices
- `sec_filings` - Corporate filings and financial data
- `hardware_news` - Product launches and supply news
- `interest_rates` - Federal Reserve rates
- `energy_market_events` - Market disruption events
- `alerts` - System alerts and notifications
- `correlation_analysis` - Statistical analysis results

## 🔧 Configuration Options

### Environment Variables

```bash
# Monitoring Mode
MONITOR_MODE=single|continuous|scheduled|summary
MONITOR_INTERVAL=60  # Minutes between cycles

# Alert Thresholds
GPU_PRICE_SPIKE_THRESHOLD=15      # Percentage
TREASURY_YIELD_SPIKE_THRESHOLD=20 # Basis points
NATURAL_GAS_SPIKE_THRESHOLD=10    # Percentage

# Collection Frequencies
GPU_PRICING_FREQUENCY=15          # Minutes
FINANCIAL_DATA_FREQUENCY=15       # Minutes
NEWS_DATA_FREQUENCY=60            # Minutes
SEC_FILINGS_FREQUENCY=240         # Minutes (4 hours)
```

## 📋 Usage Examples

### Single Data Collection

```python
from run import CoreWeaveProfitabilityMonitor

monitor = CoreWeaveProfitabilityMonitor()
results = await monitor.run_full_collection_cycle()
```

### Custom Alert Rules

```python
from alerts.alert_system import AlertSystem, AlertRule

def custom_condition():
    # Custom logic here
    return {"metric": "value"}

rule = AlertRule(
    name="custom_alert",
    condition=custom_condition,
    severity="high",
    message_template="Custom alert: {metric}"
)

alert_system.add_rule(rule)
```

### Correlation Analysis

```python
from analysis.correlation_analyzer import CorrelationAnalyzer
from storage.data_manager import DataManager

dm = DataManager()
analyzer = CorrelationAnalyzer(dm)

# Generate report
report = analyzer.generate_correlation_report(days_back=90)
print(report)

# Get detailed analysis
analysis = analyzer.analyze_profitability_indicators(days_back=90)
```

## 🔍 Monitoring Dashboard

### Data Summary

```bash
# View current data status
MONITOR_MODE=summary python run.py
```

Output:
```
Data Summary:
gpu_pricing: 1,234 records
  Latest: 2024-06-20 14:30:00
treasury_yields: 567 records
  Latest: 2024-06-20 14:15:00
energy_futures: 890 records
  Latest: 2024-06-20 14:15:00
```

## 🚨 Alert Examples

### High Priority Alerts

```
[HIGH] gpu_price_spike
Time: 2024-06-20 14:30:00
Message: GPU prices increased by 18.5% in the last 24 hours. Current average: $4.89/hour

[HIGH] natural_gas_spike
Time: 2024-06-20 14:25:00
Message: Natural gas prices spiked 12.3% to $3.45/MMBtu. This directly impacts CoreWeave's operational costs.
```

### Medium Priority Alerts

```
[MEDIUM] treasury_yield_spike
Time: 2024-06-20 14:20:00
Message: 10Y Treasury yield increased by 25 basis points to 4.35%. This may impact CoreWeave's borrowing costs.

[MEDIUM] new_sec_filing
Time: 2024-06-20 13:45:00
Message: New SEC filing detected: 10-Q for CoreWeave. Filed on 2024-06-20.
```

## 🔧 Troubleshooting

### Common Issues

1. **API Rate Limits**
   - Increase collection intervals
   - Add API key rotation

2. **Database Locks**
   - Check for long-running queries
   - Restart monitoring process

3. **Missing Data**
   - Verify API keys
   - Check network connectivity
   - Review error logs

### Debug Mode

```bash
# Enable verbose logging
LOG_LEVEL=DEBUG python run.py
```

## 📊 Performance Metrics

### System Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 10GB for 1 year of data
- **Network**: Stable internet connection

### Data Volume Estimates

| Period | GPU Pricing | Financial | News | Total |
|--------|-------------|-----------|------|-------|
| 1 Day | ~100 records | ~200 records | ~50 records | ~350 records |
| 1 Month | ~3K records | ~6K records | ~1.5K records | ~10.5K records |
| 1 Year | ~36K records | ~72K records | ~18K records | ~126K records |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing GitHub issues
3. Create a new issue with detailed information

## 🔮 Roadmap

### Planned Features

- [ ] Web dashboard for real-time monitoring
- [ ] Machine learning models for price prediction
- [ ] Integration with more cloud platforms
- [ ] Advanced visualization tools
- [ ] API endpoints for external integration
- [ ] Slack/Discord notification channels
- [ ] Historical data export functionality
- [ ] Custom correlation analysis tools

### Data Sources Expansion

- [ ] AWS/GCP/Azure pricing data
- [ ] Cryptocurrency market indicators
- [ ] Semiconductor industry metrics
- [ ] Data center real estate prices
- [ ] Power grid reliability data