"""
Alert system for monitoring CoreWeave profitability indicators
"""
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
import pandas as pd
import os
from dotenv import load_dotenv

from storage.data_manager import DataManager

load_dotenv()


class AlertRule:
    def __init__(self, name: str, condition: Callable, severity: str, message_template: str):
        self.name = name
        self.condition = condition
        self.severity = severity  # 'low', 'medium', 'high', 'critical'
        self.message_template = message_template
        self.last_triggered = None


class AlertSystem:
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.rules = []
        self.notification_channels = []
        self._setup_default_rules()

    def _setup_default_rules(self):
        """Setup default alert rules for CoreWeave profitability indicators"""
        
        # GPU Pricing Alerts
        self.add_rule(AlertRule(
            name="gpu_price_spike",
            condition=self._check_gpu_price_spike,
            severity="high",
            message_template="GPU prices increased by {change}% in the last {period} hours. Current average: ${price}/hour"
        ))
        
        # Treasury Yield Alerts
        self.add_rule(AlertRule(
            name="treasury_yield_spike",
            condition=self._check_treasury_yield_spike,
            severity="medium",
            message_template="10Y Treasury yield increased by {change} basis points to {current}%. This may impact CoreWeave's borrowing costs."
        ))
        
        # Energy Price Alerts
        self.add_rule(AlertRule(
            name="natural_gas_spike",
            condition=self._check_natural_gas_spike,
            severity="high",
            message_template="Natural gas prices spiked {change}% to ${price}/MMBtu. This directly impacts CoreWeave's operational costs."
        ))
        
        # Interest Rate Alerts
        self.add_rule(AlertRule(
            name="fed_rate_change",
            condition=self._check_fed_rate_change,
            severity="high",
            message_template="Federal funds rate changed to {rate}%. This affects CoreWeave's financing costs and customer spending."
        ))
        
        # SEC Filing Alerts
        self.add_rule(AlertRule(
            name="new_sec_filing",
            condition=self._check_new_sec_filing,
            severity="medium",
            message_template="New SEC filing detected: {filing_type} for {company}. Filed on {date}."
        ))
        
        # Hardware Supply Alerts
        self.add_rule(AlertRule(
            name="gpu_supply_constraint",
            condition=self._check_gpu_supply_constraint,
            severity="high",
            message_template="GPU supply constraints detected for {hardware_type}. Status: {status}"
        ))
        
        # Energy Market Event Alerts
        self.add_rule(AlertRule(
            name="energy_market_event",
            condition=self._check_energy_market_event,
            severity="medium",
            message_template="Energy market event detected: {event_type} with {impact_level} impact in {regions}"
        ))

    def add_rule(self, rule: AlertRule):
        """Add a new alert rule"""
        self.rules.append(rule)

    def add_notification_channel(self, channel: Callable):
        """Add a notification channel (email, SMS, webhook, etc.)"""
        self.notification_channels.append(channel)

    # Alert Condition Checkers
    def _check_gpu_price_spike(self) -> Optional[Dict[str, Any]]:
        """Check for GPU price spikes"""
        try:
            # Get GPU pricing data for last 24 hours
            df = self.data_manager.get_gpu_pricing(days_back=2)
            if df.empty:
                return None
            
            # Calculate price changes
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            # Group by GPU model and calculate percentage change
            for gpu_model in df['gpu_model'].unique():
                gpu_data = df[df['gpu_model'] == gpu_model]
                if len(gpu_data) < 2:
                    continue
                
                recent_price = gpu_data.iloc[-1]['price']
                previous_price = gpu_data.iloc[-2]['price']
                
                if previous_price > 0:
                    change_percent = ((recent_price - previous_price) / previous_price) * 100
                    
                    if change_percent > 15:  # 15% increase threshold
                        return {
                            'change': round(change_percent, 1),
                            'period': 24,
                            'price': recent_price,
                            'gpu_model': gpu_model
                        }
            
            return None
            
        except Exception as e:
            print(f"Error checking GPU price spike: {e}")
            return None

    def _check_treasury_yield_spike(self) -> Optional[Dict[str, Any]]:
        """Check for Treasury yield spikes"""
        try:
            df = self.data_manager.get_treasury_yields(days_back=2)
            if df.empty or len(df) < 2:
                return None
            
            df = df.sort_values('timestamp')
            current_yield = df.iloc[-1]['yield_10y']
            previous_yield = df.iloc[-2]['yield_10y']
            
            if current_yield and previous_yield:
                change_bps = (current_yield - previous_yield) * 100  # Convert to basis points
                
                if abs(change_bps) > 20:  # 20 basis points threshold
                    return {
                        'change': round(change_bps, 1),
                        'current': current_yield
                    }
            
            return None
            
        except Exception as e:
            print(f"Error checking Treasury yield spike: {e}")
            return None

    def _check_natural_gas_spike(self) -> Optional[Dict[str, Any]]:
        """Check for natural gas price spikes"""
        try:
            df = self.data_manager.get_energy_futures(days_back=2)
            if df.empty or len(df) < 2:
                return None
            
            df = df.sort_values('timestamp')
            current_price = df.iloc[-1]['natural_gas_price']
            previous_price = df.iloc[-2]['natural_gas_price']
            
            if current_price and previous_price and previous_price > 0:
                change_percent = ((current_price - previous_price) / previous_price) * 100
                
                if abs(change_percent) > 10:  # 10% change threshold
                    return {
                        'change': round(change_percent, 1),
                        'price': current_price
                    }
            
            return None
            
        except Exception as e:
            print(f"Error checking natural gas spike: {e}")
            return None

    def _check_fed_rate_change(self) -> Optional[Dict[str, Any]]:
        """Check for Federal Reserve rate changes"""
        try:
            df = self.data_manager.get_interest_rates(days_back=7)
            if df.empty:
                return None
            
            df = df.sort_values('timestamp')
            
            if len(df) >= 2:
                current_rate = df.iloc[-1]['fed_funds_rate']
                previous_rate = df.iloc[-2]['fed_funds_rate']
                
                if current_rate != previous_rate:
                    return {
                        'rate': current_rate,
                        'change': current_rate - previous_rate
                    }
            
            return None
            
        except Exception as e:
            print(f"Error checking Fed rate change: {e}")
            return None

    def _check_new_sec_filing(self) -> Optional[Dict[str, Any]]:
        """Check for new SEC filings"""
        try:
            df = self.data_manager.get_sec_filings(days_back=1, company="CoreWeave")
            if df.empty:
                return None
            
            # Check if there are any filings from the last 24 hours
            df['filing_date'] = pd.to_datetime(df['filing_date'])
            recent_filings = df[df['filing_date'] >= datetime.now() - timedelta(days=1)]
            
            if not recent_filings.empty:
                filing = recent_filings.iloc[0]
                return {
                    'filing_type': filing['filing_type'],
                    'company': filing['company'],
                    'date': filing['filing_date'].strftime('%Y-%m-%d')
                }
            
            return None
            
        except Exception as e:
            print(f"Error checking new SEC filing: {e}")
            return None

    def _check_gpu_supply_constraint(self) -> Optional[Dict[str, Any]]:
        """Check for GPU supply constraints in news"""
        try:
            df = self.data_manager.get_hardware_news(days_back=1)
            if df.empty:
                return None
            
            # Look for supply constraint mentions
            constraint_news = df[df['supply_status'].isin(['shortage', 'delayed'])]
            
            if not constraint_news.empty:
                news = constraint_news.iloc[0]
                return {
                    'hardware_type': news['hardware_type'],
                    'status': news['supply_status']
                }
            
            return None
            
        except Exception as e:
            print(f"Error checking GPU supply constraint: {e}")
            return None

    def _check_energy_market_event(self) -> Optional[Dict[str, Any]]:
        """Check for energy market events"""
        try:
            df = self.data_manager.get_energy_events(days_back=1, impact_level="high")
            if df.empty:
                return None
            
            event = df.iloc[0]
            regions = event['affected_regions'] if event['affected_regions'] else "Unknown"
            
            return {
                'event_type': event['event_type'],
                'impact_level': event['impact_level'],
                'regions': regions
            }
            
        except Exception as e:
            print(f"Error checking energy market event: {e}")
            return None

    async def check_all_rules(self) -> List[Dict[str, Any]]:
        """Check all alert rules and return triggered alerts"""
        triggered_alerts = []
        
        for rule in self.rules:
            try:
                result = rule.condition()
                if result:
                    # Format message
                    message = rule.message_template.format(**result)
                    
                    alert = {
                        'rule_name': rule.name,
                        'severity': rule.severity,
                        'message': message,
                        'timestamp': datetime.now(),
                        'data': result
                    }
                    
                    triggered_alerts.append(alert)
                    
                    # Store alert in database
                    self.data_manager.create_alert(
                        alert_type=rule.name,
                        message=message,
                        severity=rule.severity,
                        data_source="alert_system"
                    )
                    
                    # Update last triggered time
                    rule.last_triggered = datetime.now()
                    
            except Exception as e:
                print(f"Error checking rule {rule.name}: {e}")
        
        return triggered_alerts

    async def send_notifications(self, alerts: List[Dict[str, Any]]):
        """Send notifications for triggered alerts"""
        if not alerts:
            return
        
        for channel in self.notification_channels:
            try:
                await channel(alerts)
            except Exception as e:
                print(f"Error sending notification: {e}")

    async def run_monitoring_cycle(self):
        """Run one monitoring cycle"""
        print(f"Running alert monitoring cycle at {datetime.now()}")
        
        # Check all rules
        triggered_alerts = await self.check_all_rules()
        
        if triggered_alerts:
            print(f"Found {len(triggered_alerts)} triggered alerts")
            for alert in triggered_alerts:
                print(f"  {alert['severity'].upper()}: {alert['message']}")
            
            # Send notifications
            await self.send_notifications(triggered_alerts)
        else:
            print("No alerts triggered")
        
        return triggered_alerts


# Notification Channels
class EmailNotifier:
    def __init__(self, smtp_server: str, smtp_port: int, username: str, password: str, recipients: List[str]):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.recipients = recipients

    async def __call__(self, alerts: List[Dict[str, Any]]):
        """Send email notifications"""
        try:
            # Create email content
            subject = f"CoreWeave Profitability Alert - {len(alerts)} Alert(s)"
            
            body = "CoreWeave Profitability Monitoring Alert\n\n"
            body += f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            for alert in alerts:
                body += f"SEVERITY: {alert['severity'].upper()}\n"
                body += f"RULE: {alert['rule_name']}\n"
                body += f"MESSAGE: {alert['message']}\n"
                body += "-" * 50 + "\n"
            
            # Send email
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ", ".join(self.recipients)
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            text = msg.as_string()
            server.sendmail(self.username, self.recipients, text)
            server.quit()
            
            print(f"Email notification sent to {len(self.recipients)} recipients")
            
        except Exception as e:
            print(f"Error sending email notification: {e}")


class ConsoleNotifier:
    async def __call__(self, alerts: List[Dict[str, Any]]):
        """Print alerts to console"""
        print("\n" + "="*60)
        print("COREWEAVE PROFITABILITY ALERTS")
        print("="*60)
        
        for alert in alerts:
            print(f"\n[{alert['severity'].upper()}] {alert['rule_name']}")
            print(f"Time: {alert['timestamp']}")
            print(f"Message: {alert['message']}")
        
        print("\n" + "="*60)


# Example usage
async def main():
    """Test the alert system"""
    dm = DataManager()
    alert_system = AlertSystem(dm)
    
    # Add console notifier
    alert_system.add_notification_channel(ConsoleNotifier())
    
    # Add email notifier if configured
    email_config = {
        'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'smtp_port': int(os.getenv('SMTP_PORT', '587')),
        'username': os.getenv('EMAIL_USERNAME'),
        'password': os.getenv('EMAIL_PASSWORD'),
        'recipients': os.getenv('EMAIL_RECIPIENTS', '').split(',')
    }
    
    if email_config['username'] and email_config['password']:
        email_notifier = EmailNotifier(**email_config)
        alert_system.add_notification_channel(email_notifier)
    
    # Run monitoring cycle
    await alert_system.run_monitoring_cycle()


if __name__ == "__main__":
    asyncio.run(main())