"""
Correlation analysis for CoreWeave profitability indicators
"""
import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import matplotlib.pyplot as plt
import seaborn as sns
from storage.data_manager import DataManager


class CorrelationAnalyzer:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager

    def prepare_time_series_data(self, days_back: int = 90) -> pd.DataFrame:
        """Prepare time series data for correlation analysis"""
        
        # Get all data types
        gpu_pricing = self.data_manager.get_gpu_pricing(days_back=days_back)
        treasury_yields = self.data_manager.get_treasury_yields(days_back=days_back)
        energy_futures = self.data_manager.get_energy_futures(days_back=days_back)
        interest_rates = self.data_manager.get_interest_rates(days_back=days_back)
        
        # Create a unified time series DataFrame
        time_series = pd.DataFrame()
        
        # Process GPU pricing (average prices by day)
        if not gpu_pricing.empty:
            gpu_pricing['timestamp'] = pd.to_datetime(gpu_pricing['timestamp'])
            gpu_pricing['date'] = gpu_pricing['timestamp'].dt.date
            gpu_daily = gpu_pricing.groupby('date')['price'].mean().reset_index()
            gpu_daily.columns = ['date', 'avg_gpu_price']
            time_series = pd.merge(time_series, gpu_daily, on='date', how='outer') if not time_series.empty else gpu_daily
        
        # Process Treasury yields
        if not treasury_yields.empty:
            treasury_yields['timestamp'] = pd.to_datetime(treasury_yields['timestamp'])
            treasury_yields['date'] = treasury_yields['timestamp'].dt.date
            treasury_daily = treasury_yields.groupby('date')['yield_10y'].mean().reset_index()
            treasury_daily.columns = ['date', 'treasury_10y']
            time_series = pd.merge(time_series, treasury_daily, on='date', how='outer') if not time_series.empty else treasury_daily
        
        # Process Energy futures
        if not energy_futures.empty:
            energy_futures['timestamp'] = pd.to_datetime(energy_futures['timestamp'])
            energy_futures['date'] = energy_futures['timestamp'].dt.date
            energy_daily = energy_futures.groupby('date').agg({
                'natural_gas_price': 'mean',
                'crude_oil_price': 'mean'
            }).reset_index()
            time_series = pd.merge(time_series, energy_daily, on='date', how='outer') if not time_series.empty else energy_daily
        
        # Process Interest rates
        if not interest_rates.empty:
            interest_rates['timestamp'] = pd.to_datetime(interest_rates['timestamp'])
            interest_rates['date'] = interest_rates['timestamp'].dt.date
            rates_daily = interest_rates.groupby('date')['fed_funds_rate'].mean().reset_index()
            time_series = pd.merge(time_series, rates_daily, on='date', how='outer') if not time_series.empty else rates_daily
        
        # Sort by date and forward fill missing values
        if not time_series.empty:
            time_series = time_series.sort_values('date')
            time_series = time_series.fillna(method='ffill')
        
        return time_series

    def calculate_correlations(self, data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Calculate correlation matrix for all numeric columns"""
        
        # Select only numeric columns
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            return {}
        
        # Calculate correlation matrix
        correlation_matrix = data[numeric_cols].corr()
        
        # Convert to dictionary format
        correlations = {}
        for col1 in numeric_cols:
            correlations[col1] = {}
            for col2 in numeric_cols:
                if col1 != col2:
                    correlations[col1][col2] = correlation_matrix.loc[col1, col2]
        
        return correlations

    def calculate_correlation_with_significance(self, x: pd.Series, y: pd.Series) -> Tuple[float, float]:
        """Calculate correlation coefficient with p-value"""
        
        # Remove NaN values
        valid_data = pd.DataFrame({'x': x, 'y': y}).dropna()
        
        if len(valid_data) < 3:
            return 0.0, 1.0
        
        correlation, p_value = stats.pearsonr(valid_data['x'], valid_data['y'])
        return correlation, p_value

    def analyze_gpu_price_correlations(self, days_back: int = 90) -> Dict[str, Dict[str, float]]:
        """Analyze correlations specifically with GPU pricing"""
        
        data = self.prepare_time_series_data(days_back=days_back)
        
        if data.empty or 'avg_gpu_price' not in data.columns:
            return {}
        
        gpu_correlations = {}
        
        # Correlate GPU prices with other metrics
        for col in data.columns:
            if col not in ['date', 'avg_gpu_price'] and data[col].dtype in ['float64', 'int64']:
                correlation, p_value = self.calculate_correlation_with_significance(
                    data['avg_gpu_price'], data[col]
                )
                
                gpu_correlations[col] = {
                    'correlation': correlation,
                    'p_value': p_value,
                    'significance': 'significant' if p_value < 0.05 else 'not_significant',
                    'strength': self._interpret_correlation_strength(abs(correlation))
                }
        
        return gpu_correlations

    def _interpret_correlation_strength(self, abs_correlation: float) -> str:
        """Interpret correlation strength"""
        if abs_correlation >= 0.7:
            return 'strong'
        elif abs_correlation >= 0.3:
            return 'moderate'
        elif abs_correlation >= 0.1:
            return 'weak'
        else:
            return 'very_weak'

    def analyze_profitability_indicators(self, days_back: int = 90) -> Dict[str, any]:
        """Comprehensive analysis of profitability indicators"""
        
        data = self.prepare_time_series_data(days_back=days_back)
        
        if data.empty:
            return {"error": "No data available for analysis"}
        
        analysis = {
            "data_period": {
                "days_back": days_back,
                "start_date": data['date'].min() if not data.empty else None,
                "end_date": data['date'].max() if not data.empty else None,
                "total_observations": len(data)
            },
            "correlations": {},
            "key_insights": [],
            "risk_factors": []
        }
        
        # Calculate all correlations
        correlations = self.calculate_correlations(data)
        analysis["correlations"] = correlations
        
        # GPU-specific analysis
        gpu_correlations = self.analyze_gpu_price_correlations(days_back=days_back)
        analysis["gpu_correlations"] = gpu_correlations
        
        # Generate insights
        insights = self._generate_insights(data, gpu_correlations)
        analysis["key_insights"] = insights
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(data, gpu_correlations)
        analysis["risk_factors"] = risk_factors
        
        # Store analysis results
        self._store_correlation_results(gpu_correlations, days_back)
        
        return analysis

    def _generate_insights(self, data: pd.DataFrame, gpu_correlations: Dict[str, Dict[str, float]]) -> List[str]:
        """Generate key insights from correlation analysis"""
        
        insights = []
        
        # Check for strong correlations with GPU pricing
        for metric, corr_data in gpu_correlations.items():
            correlation = corr_data['correlation']
            strength = corr_data['strength']
            significance = corr_data['significance']
            
            if strength in ['strong', 'moderate'] and significance == 'significant':
                direction = "positively" if correlation > 0 else "negatively"
                insights.append(
                    f"GPU prices are {strength}ly {direction} correlated with {metric} "
                    f"(r={correlation:.3f}, p<0.05)"
                )
        
        # Check for energy cost correlations
        if 'natural_gas_price' in gpu_correlations:
            gas_corr = gpu_correlations['natural_gas_price']['correlation']
            if abs(gas_corr) > 0.3:
                direction = "increase" if gas_corr > 0 else "decrease"
                insights.append(
                    f"Natural gas price changes may {direction} GPU pricing costs for CoreWeave"
                )
        
        # Check for interest rate impact
        if 'fed_funds_rate' in gpu_correlations:
            rate_corr = gpu_correlations['fed_funds_rate']['correlation']
            if abs(rate_corr) > 0.2:
                impact = "increase" if rate_corr > 0 else "decrease"
                insights.append(
                    f"Federal funds rate changes may {impact} GPU demand through financing costs"
                )
        
        # Check for Treasury yield impact
        if 'treasury_10y' in gpu_correlations:
            treasury_corr = gpu_correlations['treasury_10y']['correlation']
            if abs(treasury_corr) > 0.2:
                impact = "higher" if treasury_corr > 0 else "lower"
                insights.append(
                    f"Rising Treasury yields may lead to {impact} GPU pricing through cost of capital effects"
                )
        
        return insights

    def _identify_risk_factors(self, data: pd.DataFrame, gpu_correlations: Dict[str, Dict[str, float]]) -> List[str]:
        """Identify potential risk factors for CoreWeave profitability"""
        
        risk_factors = []
        
        # Energy cost risks
        if 'natural_gas_price' in gpu_correlations:
            gas_corr = gpu_correlations['natural_gas_price']['correlation']
            if gas_corr > 0.3:
                risk_factors.append(
                    "HIGH RISK: Natural gas price increases directly impact operational costs"
                )
        
        # Interest rate risks
        if 'fed_funds_rate' in gpu_correlations:
            rate_corr = gpu_correlations['fed_funds_rate']['correlation']
            if abs(rate_corr) > 0.2:
                risk_factors.append(
                    "MEDIUM RISK: Interest rate changes affect customer demand and financing costs"
                )
        
        # Market volatility risks
        if not data.empty and 'avg_gpu_price' in data.columns:
            gpu_volatility = data['avg_gpu_price'].std() / data['avg_gpu_price'].mean()
            if gpu_volatility > 0.1:
                risk_factors.append(
                    f"MEDIUM RISK: High GPU price volatility ({gpu_volatility:.1%}) indicates market instability"
                )
        
        # Treasury yield risks
        if 'treasury_10y' in gpu_correlations:
            treasury_corr = gpu_correlations['treasury_10y']['correlation']
            if treasury_corr > 0.3:
                risk_factors.append(
                    "MEDIUM RISK: Rising Treasury yields increase borrowing costs for expansion"
                )
        
        return risk_factors

    def _store_correlation_results(self, gpu_correlations: Dict[str, Dict[str, float]], days_back: int):
        """Store correlation analysis results in database"""
        
        for metric, corr_data in gpu_correlations.items():
            self.data_manager.store_correlation_analysis(
                metric_1="avg_gpu_price",
                metric_2=metric,
                correlation=corr_data['correlation'],
                p_value=corr_data['p_value'],
                period_days=days_back,
                notes=f"Strength: {corr_data['strength']}, Significance: {corr_data['significance']}"
            )

    def generate_correlation_report(self, days_back: int = 90) -> str:
        """Generate a comprehensive correlation report"""
        
        analysis = self.analyze_profitability_indicators(days_back=days_back)
        
        if "error" in analysis:
            return f"Error generating report: {analysis['error']}"
        
        report = []
        report.append("="*60)
        report.append("COREWEAVE PROFITABILITY CORRELATION ANALYSIS")
        report.append("="*60)
        report.append(f"Analysis Period: {analysis['data_period']['start_date']} to {analysis['data_period']['end_date']}")
        report.append(f"Total Observations: {analysis['data_period']['total_observations']}")
        report.append("")
        
        # GPU Correlations
        report.append("GPU PRICING CORRELATIONS:")
        report.append("-" * 30)
        for metric, corr_data in analysis.get('gpu_correlations', {}).items():
            correlation = corr_data['correlation']
            strength = corr_data['strength']
            significance = corr_data['significance']
            
            report.append(f"{metric}:")
            report.append(f"  Correlation: {correlation:.3f}")
            report.append(f"  Strength: {strength}")
            report.append(f"  Significance: {significance}")
            report.append("")
        
        # Key Insights
        report.append("KEY INSIGHTS:")
        report.append("-" * 15)
        for insight in analysis.get('key_insights', []):
            report.append(f"• {insight}")
        report.append("")
        
        # Risk Factors
        report.append("RISK FACTORS:")
        report.append("-" * 15)
        for risk in analysis.get('risk_factors', []):
            report.append(f"• {risk}")
        report.append("")
        
        report.append("="*60)
        
        return "\n".join(report)


# Example usage
if __name__ == "__main__":
    dm = DataManager()
    analyzer = CorrelationAnalyzer(dm)
    
    # Generate correlation report
    report = analyzer.generate_correlation_report(days_back=30)
    print(report)
    
    # Get detailed analysis
    analysis = analyzer.analyze_profitability_indicators(days_back=30)
    print("\nDetailed Analysis:")
    print(analysis)