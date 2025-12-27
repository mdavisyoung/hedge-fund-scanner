"""
Notification System
Send email alerts for trading events
"""

import os
from datetime import datetime
from typing import Dict, List
import requests
from dotenv import load_dotenv
import yaml
from pathlib import Path

load_dotenv()


class NotificationManager:
    """Manages email notifications for trading events"""

    def __init__(self):
        self.sendgrid_api_key = os.getenv('SENDGRID_API_KEY')

        # Load config
        config_path = Path(__file__).parent.parent / "config.yaml"
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.notifications_enabled = self.config['notifications']['enabled']
        self.from_email = self.config['notifications']['email']['from']
        self.to_email = self.config['notifications']['email']['to']

    def send_email(self, subject: str, html_content: str) -> bool:
        """
        Send email via SendGrid API

        Args:
            subject: Email subject line
            html_content: HTML email body

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.notifications_enabled:
            print(f"📧 Notifications disabled. Would have sent: {subject}")
            return False

        if not self.sendgrid_api_key:
            print(f"⚠️ SendGrid API key not configured. Cannot send: {subject}")
            return False

        try:
            response = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {self.sendgrid_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "personalizations": [{
                        "to": [{"email": self.to_email}],
                        "subject": subject
                    }],
                    "from": {"email": self.from_email},
                    "content": [{
                        "type": "text/html",
                        "value": html_content
                    }]
                },
                timeout=10
            )

            if response.status_code == 202:
                print(f"✅ Email sent: {subject}")
                return True
            else:
                print(f"❌ Failed to send email: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error sending email: {e}")
            return False

    def notify_trade_executed(self, trade: Dict) -> bool:
        """Notify when a trade is executed"""
        ticker = trade['ticker']
        action = trade['action']
        shares = trade['shares']
        entry_price = trade['entry_price']
        confidence = trade.get('confidence', 'N/A')
        reasoning = trade.get('reasoning', 'No reasoning provided')

        subject = f"🤖 Trade Executed: {action} {shares} shares of {ticker}"

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .trade-details {{ background: #f4f4f4; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .footer {{ background: #333; color: white; padding: 10px; text-align: center; font-size: 12px; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .label {{ font-weight: bold; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 Autonomous Trade Executed</h1>
            </div>

            <div class="content">
                <h2>{action} {ticker}</h2>
                <p>The AI autonomous trader has executed a new trade based on market analysis.</p>

                <div class="trade-details">
                    <div class="metric">
                        <span class="label">Ticker:</span> {ticker}
                    </div>
                    <div class="metric">
                        <span class="label">Action:</span> {action}
                    </div>
                    <div class="metric">
                        <span class="label">Shares:</span> {shares}
                    </div>
                    <div class="metric">
                        <span class="label">Entry Price:</span> ${entry_price:.2f}
                    </div>
                    <div class="metric">
                        <span class="label">Position Value:</span> ${trade['position_value']:,.2f}
                    </div>
                    <div class="metric">
                        <span class="label">Stop Loss:</span> ${trade['stop_loss']:.2f}
                    </div>
                    <div class="metric">
                        <span class="label">Target:</span> ${trade['target']:.2f}
                    </div>
                    <div class="metric">
                        <span class="label">AI Confidence:</span> {confidence}/10
                    </div>
                </div>

                <h3>AI Reasoning:</h3>
                <p>{reasoning}</p>

                <p><strong>Timestamp:</strong> {trade['timestamp']}</p>
                <p><strong>Order ID:</strong> {trade.get('order_id', 'N/A')}</p>
            </div>

            <div class="footer">
                <p>Autonomous AI Trader | Paper Trading Mode</p>
                <p>This is an automated notification. Do not reply to this email.</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(subject, html_content)

    def notify_position_closed(self, trade: Dict, exit_reason: str) -> bool:
        """Notify when a position is closed"""
        ticker = trade['ticker']
        pnl = trade.get('pnl', 0)
        pnl_pct = trade.get('pnl_pct', 0)
        entry_price = trade['entry_price']
        exit_price = trade.get('exit_price', 0)

        # Determine if win or loss
        is_win = pnl_pct > 0
        emoji = "🎉" if is_win else "📉"
        color = "#4CAF50" if is_win else "#f44336"

        subject = f"{emoji} Position Closed: {ticker} ({pnl_pct:+.2f}%)"

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: {color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .trade-details {{ background: #f4f4f4; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .footer {{ background: #333; color: white; padding: 10px; text-align: center; font-size: 12px; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .label {{ font-weight: bold; color: #666; }}
                .pnl {{ font-size: 24px; font-weight: bold; color: {color}; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{emoji} Position Closed</h1>
            </div>

            <div class="content">
                <h2>{ticker}</h2>

                <div class="pnl">
                    P/L: ${pnl:+,.2f} ({pnl_pct:+.2f}%)
                </div>

                <div class="trade-details">
                    <div class="metric">
                        <span class="label">Entry Price:</span> ${entry_price:.2f}
                    </div>
                    <div class="metric">
                        <span class="label">Exit Price:</span> ${exit_price:.2f}
                    </div>
                    <div class="metric">
                        <span class="label">Shares:</span> {trade['shares']}
                    </div>
                    <div class="metric">
                        <span class="label">Exit Reason:</span> {exit_reason}
                    </div>
                </div>

                <h3>Trade Summary:</h3>
                <p><strong>Entry:</strong> {trade['timestamp']}</p>
                <p><strong>Exit:</strong> {trade.get('exit_timestamp', 'N/A')}</p>
                <p><strong>Initial Confidence:</strong> {trade.get('confidence', 'N/A')}/10</p>
            </div>

            <div class="footer">
                <p>Autonomous AI Trader | Paper Trading Mode</p>
                <p>This is an automated notification. Do not reply to this email.</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(subject, html_content)

    def send_daily_digest(self, positions: List[Dict], metrics: Dict, hot_stocks: List[Dict]) -> bool:
        """Send daily performance digest"""
        subject = f"📊 Daily Trading Digest - {datetime.now().strftime('%Y-%m-%d')}"

        # Build positions summary
        positions_html = ""
        if positions:
            for pos in positions:
                color = "#4CAF50" if pos['unrealized_pnl_pct'] > 0 else "#f44336"
                positions_html += f"""
                <tr>
                    <td>{pos['ticker']}</td>
                    <td>{pos['qty']}</td>
                    <td>${pos['entry_price']:.2f}</td>
                    <td>${pos['current_price']:.2f}</td>
                    <td style="color: {color}; font-weight: bold;">{pos['unrealized_pnl_pct']:+.2f}%</td>
                </tr>
                """
        else:
            positions_html = "<tr><td colspan='5'>No open positions</td></tr>"

        # Build hot stocks summary
        hot_stocks_html = ""
        if hot_stocks:
            for stock in hot_stocks[:5]:  # Top 5
                hot_stocks_html += f"""
                <tr>
                    <td>{stock['ticker']}</td>
                    <td>{stock['score']['total_score']:.1f}</td>
                    <td>${stock.get('current_price', 0):.2f}</td>
                    <td>${stock.get('entry_price', 0):.2f}</td>
                </tr>
                """
        else:
            hot_stocks_html = "<tr><td colspan='4'>No hot stocks available</td></tr>"

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: #2196F3; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .section {{ margin: 20px 0; }}
                .metrics {{ display: flex; justify-content: space-around; flex-wrap: wrap; }}
                .metric-box {{ background: #f4f4f4; padding: 15px; margin: 10px; border-radius: 5px; text-align: center; min-width: 150px; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #2196F3; }}
                .metric-label {{ color: #666; font-size: 14px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                th {{ background: #2196F3; color: white; padding: 10px; text-align: left; }}
                td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
                .footer {{ background: #333; color: white; padding: 10px; text-align: center; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Daily Trading Digest</h1>
                <p>{datetime.now().strftime('%A, %B %d, %Y')}</p>
            </div>

            <div class="content">
                <div class="section">
                    <h2>Performance Metrics</h2>
                    <div class="metrics">
                        <div class="metric-box">
                            <div class="metric-value">{metrics['total_trades']}</div>
                            <div class="metric-label">Total Trades</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-value">{metrics['win_rate']:.1f}%</div>
                            <div class="metric-label">Win Rate</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-value">{metrics['profit_factor']:.2f}</div>
                            <div class="metric-label">Profit Factor</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-value" style="color: {'#4CAF50' if metrics['total_pnl_pct'] > 0 else '#f44336'}">
                                {metrics['total_pnl_pct']:+.2f}%
                            </div>
                            <div class="metric-label">Total P/L</div>
                        </div>
                    </div>
                </div>

                <div class="section">
                    <h2>Current Positions ({len(positions)})</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Ticker</th>
                                <th>Shares</th>
                                <th>Entry</th>
                                <th>Current</th>
                                <th>P/L %</th>
                            </tr>
                        </thead>
                        <tbody>
                            {positions_html}
                        </tbody>
                    </table>
                </div>

                <div class="section">
                    <h2>Top Hot Stocks</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Ticker</th>
                                <th>Score</th>
                                <th>Price</th>
                                <th>Entry Target</th>
                            </tr>
                        </thead>
                        <tbody>
                            {hot_stocks_html}
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="footer">
                <p>Autonomous AI Trader | Paper Trading Mode</p>
                <p>This is an automated notification. Do not reply to this email.</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(subject, html_content)

    def notify_error(self, error_message: str, context: Dict = None) -> bool:
        """Send error notification"""
        subject = "⚠️ Trading Error Alert"

        context_html = ""
        if context:
            context_html = "<h3>Context:</h3><ul>"
            for key, value in context.items():
                context_html += f"<li><strong>{key}:</strong> {value}</li>"
            context_html += "</ul>"

        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: #f44336; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .error-box {{ background: #ffebee; border-left: 4px solid #f44336; padding: 15px; margin: 15px 0; }}
                .footer {{ background: #333; color: white; padding: 10px; text-align: center; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>⚠️ Trading Error Alert</h1>
            </div>

            <div class="content">
                <p>An error occurred in the autonomous trading system:</p>

                <div class="error-box">
                    <strong>Error:</strong> {error_message}
                </div>

                {context_html}

                <p><strong>Timestamp:</strong> {datetime.now().isoformat()}</p>
                <p>Please check the system logs and take appropriate action.</p>
            </div>

            <div class="footer">
                <p>Autonomous AI Trader | Error Notification System</p>
            </div>
        </body>
        </html>
        """

        return self.send_email(subject, html_content)
